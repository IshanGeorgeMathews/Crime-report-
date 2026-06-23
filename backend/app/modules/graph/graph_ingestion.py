import os
import re
import json
from datetime import datetime
from app.infrastructure.documents.utils import (
    load_profile_database,
    extract_district_tag,
    _is_valid_person_name,
    create_new_profile,
    update_profile_activity,
    generate_uo_note_text,
    save_uo_note,
    PersonProfile
)
from app.infrastructure.neo4j.graph_db import GraphDatabase, GNNModelManager
from app.infrastructure.nlp.ner_engine import NEREngine
from app.modules.profiles.identity_resolver import IdentityResolver
from app.modules.review.identity_review_queue import IdentityReviewQueue
from app.modules.consolidation.non_crime_handler import NonCrimeHandler

HONORIFICS = ["sri", "smt", "mr", "mrs", "dr", "prof", "adv", "kum", "kumari"]

class GraphIngestionService:
    def __init__(self, pp_dir: str, template_path: str):
        self.pp_dir = pp_dir
        self.template_path = template_path
        self.resolver = IdentityResolver()
        self.review_queue = IdentityReviewQueue(pp_dir)
        self.non_crime = NonCrimeHandler(pp_dir)

    def ingest_report_items(self, texts: list, report_date: str, use_ollama: bool):
        """Orchestrate ingestion of report event paragraphs:
        1. Classifies and routes non-crime events (like protests) vs crime events.
        2. Resolves identities of extracted names using rule-based scoring (or flags for review).
        3. Persists profiles, UO notes, and Neo4j nodes/edges without duplicate repetition.
        """
        if not os.path.isdir(self.pp_dir):
            os.makedirs(self.pp_dir, exist_ok=True)

        # Load suspect profiles
        profiles = load_profile_database(self.pp_dir)
        profiles = list(profiles)

        # Connect to Neo4j
        db = GraphDatabase()
        ner_eng = NEREngine(self.pp_dir)
        new_names_in_run = set()

        with db.transaction():
            self._ingest_report_items_transactional(
                db, texts, report_date, use_ollama, profiles, ner_eng, new_names_in_run
            )

    def _ingest_report_items_transactional(
        self, db, texts, report_date, use_ollama, profiles, ner_eng, new_names_in_run
    ):
        # Pre-clean junk nodes
        removed = db.clean_junk_nodes()
        if removed:
            print(f"  [Graph DB] Cleaned {removed} junk node(s).")

        # Add Record node
        rec_id = db.add_record(report_date)

        for idx, text in enumerate(texts):
            # Extract structured data using Ollama if enabled
            structured_data = None
            if use_ollama:
                structured_data = ner_eng.extract_structured_profile_data(text)

            # Check if this item is a non-crime event (e.g. protest)
            is_non_crime = self.non_crime.identify_non_crime_event(text)
            event_id = f"{report_date.replace('.', '_')}_{idx}"
            district = ""
            tag = extract_district_tag(text)
            if tag:
                district = tag.strip("()")

            # Storage & Graph creation for the event
            if is_non_crime:
                event_data = self.non_crime.extract_non_crime_details(text, report_date, district)
                self.non_crime.store_non_crime_event(event_data)
                # Add to graph as a Protest node
                event_node_id = self.non_crime.save_to_graph(db, event_data, rec_id, report_date)
                is_protest = True
            else:
                # Add to graph as Crime node
                event_node_id = db.add_crime(event_id, text, district=district, date_str=report_date)
                db.add_relation(event_node_id, rec_id, "REPORTED_IN", report_date=report_date)
                is_protest = False

            # Extract suspect names
            person_candidates = ner_eng.extract_person_names(text)

            # Filter parentage and police ranks
            parent_names = re.findall(r"[SsDd]/o\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})", text)
            parent_names_clean = []
            for pn in parent_names:
                words = [w for w in pn.split() if w.lower() not in HONORIFICS]
                if words:
                    parent_names_clean.append(" ".join(words))

            names = []
            for cand in person_candidates:
                is_parent = False
                for pn in parent_names_clean:
                    from app.infrastructure.documents.utils import is_fuzzy_match as utils_is_fuzzy_match
                    if utils_is_fuzzy_match(cand, pn):
                        is_parent = True
                        break
                if is_parent:
                    continue

                pattern = r"\b" + re.escape(cand) + r"\b\s*,?\s*\b(ACP|DYSP|SP|SI|CI|Inspector|Commissioner|Superintendent|Deputy\s+Superintendent|Assistant\s+Commissioner|Sub\s+Inspector|Circle\s+Inspector)\b"
                if re.search(pattern, text, re.IGNORECASE):
                    continue

                names.append(cand)

            ind_node_ids = []

            for name in names:
                if not _is_valid_person_name(name):
                    continue

                # Process name through VEG/ARFR check
                veg_status = ner_eng.process_candidate(name, text, self.template_path, report_date)
                if veg_status == "ignored":
                    print(f"  [VEG Ignored] '{name}' (silenced location/junk word).")
                    continue

                # Identify if name is new to our local profile directory
                is_new_suspect_filesystem = not any(p.name.lower() == name.lower() for p in profiles)
                if is_new_suspect_filesystem:
                    new_names_in_run.add(name)

                prof_matched = None
                
                # Resolve Identity using rule-based resolver
                matched_cand, resolution_status = self.resolver.resolve_identity(
                    name=name,
                    text=text,
                    profiles=profiles,
                    report_date=report_date
                )

                if resolution_status == "auto_merged" and matched_cand:
                    prof_matched = matched_cand
                    print(f"  [Auto-Merged] '{name}' -> '{prof_matched.name}' (PP ID: {prof_matched.pp_id}).")
                elif resolution_status == "pending_review" and matched_cand:
                    # Flag for review but route to Name_review.docx
                    prof_matched = matched_cand
                    print(f"  [Ambiguous/Low-Confidence Match] '{name}' matches multiple/uncertain profiles. Routing to review queue.")
                    # Extract parent name for creating/updating review dossier if possible
                    parentage = ""
                    pm = re.search(r"[SsDdWw]/o\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
                    if pm:
                        parentage = pm.group(1)
                    self.review_queue.add_to_review(name, text, report_date, self.template_path, parentage=parentage)
                else:
                    # new_suspect: create a new profile
                    print(f"  [New Person] '{name}' — creating profile.")
                    safe_name = re.sub(r'[<>:"/\\|?*]', '_', name)
                    existing_nums = [
                        int(m.group(1))
                        for f in os.listdir(self.pp_dir)
                        if (m := re.match(r'^(\d+)\)', f))
                    ]
                    next_num = max(existing_nums, default=0) + 1
                    new_filename = f"{next_num})  {safe_name}.docx"
                    new_path = os.path.join(self.pp_dir, new_filename)

                    parentage = ""
                    pm = re.search(r"[SsDdWw]/o\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
                    if pm:
                        parentage = pm.group(1)

                    create_new_profile(
                        name=name,
                        parentage=parentage,
                        activity_desc=text[:300],
                        activity_date=report_date,
                        template_path=self.template_path,
                        output_path=new_path,
                    )

                    try:
                        new_prof_obj = PersonProfile(new_path)
                        profiles.append(new_prof_obj)
                        prof_matched = new_prof_obj
                    except Exception:
                        pass

                    # Create UO Note
                    uo_filename = f"{next_num}) UO {safe_name}.docx"
                    uo_path = os.path.join(self.pp_dir, uo_filename)
                    try:
                        uo_text = generate_uo_note_text(prof_matched, use_ollama=use_ollama)
                        save_uo_note(uo_text, uo_path)
                    except Exception as e:
                        print(f"    [Warning] Could not generate UO: {e}")

                # Update the resolved or new profile on disk
                if prof_matched:
                    # Update activity log on profile
                    update_profile_activity(
                        profile_path=prof_matched.filepath,
                        activity_name=f"Mentioned in IS Report {report_date}",
                        activity_desc=text[:300],
                        activity_date=report_date,
                        structured_data=structured_data,
                    )
                    
                    # Regenerate corresponding UO note if it exists
                    uo_path = None
                    m_num = re.match(r"^(\d+)", os.path.basename(prof_matched.filepath))
                    if m_num:
                        num_str = m_num.group(1)
                        pattern = r"^" + num_str + r"\D.*uo"
                        for f in os.listdir(self.pp_dir):
                            if re.match(pattern, f, re.IGNORECASE):
                                uo_path = os.path.join(self.pp_dir, f)
                                break
                    if uo_path:
                        try:
                            updated_prof = PersonProfile(prof_matched.filepath)
                            uo_text = generate_uo_note_text(updated_prof, use_ollama=use_ollama)
                            save_uo_note(uo_text, uo_path)
                        except Exception as e:
                            print(f"    [Warning] Could not regenerate UO: {e}")

                # Keep the previous name if the person was matched to an existing profile
                name_to_use = prof_matched.name if prof_matched else name

                # Derive a stable canonical_node_id from the profile's full name
                # so that a shorter alias in report text does not spawn a duplicate
                canonical_node_id = ""
                if prof_matched and prof_matched.name:
                    canonical_node_id = f"ind_{prof_matched.name.lower().replace(' ', '_')}"

                # Add suspect to Neo4j graph database (or update if exists)
                ind_id = db.add_individual(
                    name=name_to_use,
                    pp_id=prof_matched.pp_id if prof_matched else "",
                    ps=prof_matched.police_station if prof_matched else "",
                    address=prof_matched.address if prof_matched else "",
                    activity_type=prof_matched.activity_type if prof_matched else "",
                    canonical_node_id=canonical_node_id,
                )

                if ind_id and event_node_id:
                    ind_node_ids.append(ind_id)
                    # Link suspect to record
                    db.add_relation(ind_id, rec_id, "MENTIONED_IN", report_date=report_date)
                    
                    # Link suspect to crime/protest event
                    if is_protest:
                        db.add_relation(ind_id, event_node_id, "PARTICIPATED_IN", report_date=report_date)
                    else:
                        db.add_relation(ind_id, event_node_id, "ASSOCIATED_WITH", report_date=report_date)

                    # Link organization involvement
                    org_name = ""
                    org_remarks = ""
                    
                    # 1. Look up organization in matched profile dossier (robust properties)
                    if prof_matched:
                        org_name = prof_matched.organization
                        org_remarks = prof_matched.org_remarks
                    
                    # 2. Look up using fallback keywords in text
                    if not org_name:
                        for known_org in ["Maoist", "RSU", "KMP", "RDPI", "RDTU", "RPM", "RPI (RL) Blue Star", "Adivasi Dalit Munnetta Samithi", "Public Resource Samithi"]:
                            if known_org.lower() in text.lower():
                                org_name = known_org
                                break
                    
                    # 3. Look up using LLM structured extraction if available
                    if structured_data:
                        org_info = structured_data.get("organization_involvement", {})
                        if isinstance(org_info, list):
                            org_info = org_info[0] if org_info else {}
                        elif not isinstance(org_info, dict):
                            org_info = {}
                        extracted_org_name = (org_info.get("org_name") or "").strip()
                        if extracted_org_name:
                            # Only use LLM org if no profile org was found
                            if not org_name:
                                org_name = extracted_org_name
                            org_remarks = org_remarks or (org_info.get("remarks") or "").strip()

                    if org_name:
                        org_id = db.add_organization(org_name, org_remarks)
                        if org_id:
                            db.add_relation(ind_id, org_id, "MEMBER_OF", report_date=report_date)
                            print(f"    [Org Link] '{name_to_use}' -> '{org_name}'")

                    # Link case details
                    if structured_data:
                        case_info = structured_data.get("case_details", {})
                        if isinstance(case_info, list):
                            case_info = case_info[0] if case_info else {}
                        elif not isinstance(case_info, dict):
                            case_info = {}
                        fir = (case_info.get("fir_number") or "").strip()
                        sections = (case_info.get("under_sections") or "").strip()
                        ps = (case_info.get("police_station") or "").strip()
                        brief = (case_info.get("case_brief") or "").strip()
                        case_id = fir if fir else (case_info.get("case_id") or "")
                        if not case_id and (sections or brief):
                            case_id = f"case_{event_node_id}"
                        if case_id:
                            case_node_id = db.add_case(case_id, fir=fir, sections=sections, ps=ps, brief=brief)
                            if case_node_id:
                                db.add_relation(ind_id, case_node_id, "ACCUSED_IN", report_date=report_date)

            # Link co-occurrence of individuals in this paragraph
            for i in range(len(ind_node_ids)):
                for j in range(i + 1, len(ind_node_ids)):
                    db.add_relation(ind_node_ids[i], ind_node_ids[j], "CO_OCCURRED_WITH", report_date=report_date)

        # High Frequency Edge Guards (Extraction Anomaly Check)
        for name in new_names_in_run:
            node_id = f"ind_{name.lower().replace(' ', '_')}"
            if not db.has_node(node_id):
                continue
            connected_events = 0
            for neighbor_id in db.neighbors(node_id):
                neighbor_data = db.get_node(neighbor_id)
                if neighbor_data.get("type") in ["crime", "protest"]:
                    connected_events += 1
            if connected_events > 3:
                print(f"  [High-Frequency Guard] Suspect '{name}' is linked to {connected_events} events. Routing to review queue.")
                db.set_node_property(node_id, "anomaly", "Extraction Anomaly")
                db.set_node_property(node_id, "extraction_anomaly", True)
                self.review_queue.add_to_review(
                    name=name,
                    text=f"High-frequency extraction anomaly: linked to {connected_events} event paragraphs.",
                    report_date=report_date,
                    template_path=self.template_path
                )
                ner_eng.registry[name.lower()] = {
                    "status": "pending",
                    "last_seen": datetime.utcnow().isoformat() + "Z"
                }
                ner_eng.save_registry()

        db.save()
        print(f"  [Graph DB] Saved database with updated records.")
