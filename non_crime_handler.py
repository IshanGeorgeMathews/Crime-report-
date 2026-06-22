import os
import json
import re
from datetime import datetime
from utils import extract_district_tag

# Keywords indicating non-crime events (protests, public gatherings, conventions, festivals, rallies, etc.)
NON_CRIME_KEYWORDS = [
    r"\bprotest(s)?\b", r"\bdharna(s)?\b", r"\bstrike(s)?\b", r"\bagitation(s)?\b", r"\bmarch(es)?\b",
    r"\brally\b", r"\brallies\b", r"\bcampaign(s)?\b", r"\bdemonstration(s)?\b", r"\bconvention(s)?\b",
    r"\bhunger\s+strike(s)?\b", r"\bhartal(s)?\b", r"\bblockade(s)?\b", r"\bgherao(s)?\b",
    r"\bpublic\s+meeting(s)?\b", r"\bprocession(s)?\b", r"\bfestival(s)?\b", r"\bdevotees\b", r"\boffering\b",
    r"\bdarshan\b", r"\bcelebration(s)?\b", r"\bpropaganda\b"
]

class NonCrimeHandler:
    def __init__(self, pp_dir: str):
        self.pp_dir = pp_dir
        self.json_path = os.path.join(pp_dir, "non_crime_events.jsonl")

    def identify_non_crime_event(self, text: str) -> bool:
        """Check if the text represents a non-crime event like a protest, festival, etc.
        
        Avoids classifying violent crimes (murder, NDPS drug seizures, physical assaults)
        as purely non-crime events.
        """
        text_lower = text.lower()
        
        # Guard: Drug seizures or criminal arrests are crime events
        if "seized" in text_lower and any(kw in text_lower for kw in ["mdma", "drug", "ganja", "hashish", "heroin"]):
            return False
        if "arrested" in text_lower and any(kw in text_lower for kw in ["murder", "theft", "assault", "robbery", "weapon", "uapa", "rap act"]):
            return False
            
        for pattern in NON_CRIME_KEYWORDS:
            if re.search(pattern, text_lower):
                return True
        return False

    def extract_non_crime_details(self, text: str, report_date: str = "", district: str = "") -> dict:
        """Extract event type, organizer, leaders, and place details from text."""
        text_lower = text.lower()
        
        # 1. Determine sub-type
        event_type = "Protest"
        if "rally" in text_lower or "rallies" in text_lower:
            event_type = "Rally"
        elif "strike" in text_lower or "hartal" in text_lower:
            event_type = "Strike"
        elif "dharna" in text_lower:
            event_type = "Dharna"
        elif "festival" in text_lower or "darshan" in text_lower or "offering" in text_lower:
            event_type = "Festival/Public Event"
        elif "meeting" in text_lower or "convention" in text_lower:
            event_type = "Meeting/Convention"
        elif "march" in text_lower:
            event_type = "March"
        elif "agitation" in text_lower:
            event_type = "Agitation"
            
        # 2. Extract Organizer (e.g. by SC/ST Coordination Committee)
        organizer = ""
        # Look for phrases: "by [A-Z]...", "organized by [A-Z]...", "under the leadership of [A-Z]..."
        org_match = re.search(
            r"(?:by|organized by|under the banner of|started by|conducted by)\s+([A-Z][a-zA-Z\s\(\)\/]+?)(?:\s+under\s+|\s+demanding|\s+at|\s+in|\s+limit|\s+is|\s+was|\s+starting|\s+for|\s+regarding|\.|$)",
            text
        )
        if org_match:
            cand = org_match.group(1).strip()
            # If the candidate contains "leadership" or is too short, clean it up or ignore
            if "leadership" not in cand.lower() and len(cand) > 3:
                organizer = cand
                
        # 3. Extract Leaders (individuals mentioned in Sri., Smt., etc.)
        leaders = []
        leader_matches = re.findall(
            r"(?:Sri\.|Smt\.|Mr\.|Mrs\.)\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})", 
            text
        )
        for name in leader_matches:
            name_clean = name.strip()
            if name_clean and len(name_clean) > 2:
                leaders.append(name_clean)
                
        # 4. Extract District tag
        extracted_tag = extract_district_tag(text)
        final_district = district
        if extracted_tag:
            final_district = extracted_tag.strip("()")
            
        return {
            "event_type": event_type,
            "text": text,
            "district": final_district,
            "date": report_date or datetime.now().strftime("%d.%m.%Y"),
            "organizer": organizer,
            "leaders": list(set(leaders)),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def store_non_crime_event(self, event_data: dict):
        """Save the extracted event to the local non_crime_events.jsonl file."""
        from filelock import FileLock
        lock = FileLock(self.json_path + ".lock", timeout=5)
        with lock:
            exists = False
            if os.path.exists(self.json_path):
                try:
                    with open(self.json_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if not line.strip():
                                continue
                            try:
                                obj = json.loads(line)
                                if obj.get("text") == event_data.get("text"):
                                    exists = True
                                    break
                            except Exception:
                                pass
                except Exception:
                    pass

            if exists:
                return

            try:
                with open(self.json_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event_data, ensure_ascii=False) + "\n")
                print(f"  [Non-Crime Handler] Stored event of type '{event_data['event_type']}' locally (JSONL).")
            except Exception as e:
                print(f"[Error] Failed to store non-crime event locally: {e}")

    def save_to_graph(self, db, event_data: dict, rec_id: str, report_date: str) -> str:
        """Create a Protest node in the Neo4j graph and link it to the Record and individuals."""
        # Use a safe unique ID for this protest
        import hashlib
        h = hashlib.md5(event_data["text"].encode("utf-8")).hexdigest()[:8]
        protest_id = f"{report_date.replace('.', '_')}_protest_{h}"
        
        # Add protest node to graph
        # This will call the newly added add_protest method in GraphDatabase
        prt_id = db.add_protest(
            protest_id=protest_id,
            text=event_data["text"],
            district=event_data["district"],
            category=event_data["event_type"],
            date_str=report_date,
            organizer=event_data["organizer"]
        )
        
        if prt_id:
            # Link Protest to Record
            db.add_relation(prt_id, rec_id, "REPORTED_IN", report_date=report_date)
        return prt_id
