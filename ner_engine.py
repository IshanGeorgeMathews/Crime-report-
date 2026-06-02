import os
import re
import json
import requests
import unicodedata
from datetime import datetime

# Import place names, junk words, etc. from utils
from utils import PLACE_NAMES, JUNK_WORDS, create_new_profile

REGISTRY_NAME = "review_registry.json"

class NEREngine:
    def __init__(self, pp_dir: str, ollama_url: str = "http://localhost:11434"):
        self.pp_dir = pp_dir
        self.ollama_url = ollama_url
        self.registry_path = os.path.join(pp_dir, REGISTRY_NAME)
        self.registry = {}
        self.load_registry()
        self.reconcile_arfr()
        self.ner_pipeline = None

    def initialize_ner_pipeline(self):
        """Lazy load Hugging Face NER pipeline."""
        if self.ner_pipeline is not None:
            return True
        try:
            from transformers import pipeline
            import torch
            print("  [NER Engine] Loading Hugging Face dslim/bert-base-NER model...")
            device = 0 if torch.cuda.is_available() else -1
            self.ner_pipeline = pipeline(
                "ner", 
                model="dslim/bert-base-NER", 
                aggregation_strategy="simple", 
                device=device
            )
            print("  [NER Engine] Model loaded successfully.")
            return True
        except Exception as e:
            print(f"  [Warning] Pretrained NER loading failed: {e}. Operating in fallback mode.")
            self.ner_pipeline = None
            return False

    def load_registry(self):
        """Load review_registry.json if it exists."""
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    self.registry = json.load(f)
            except Exception as e:
                print(f"[Warning] Failed to load {REGISTRY_NAME}: {e}")
                self.registry = {}
        else:
            self.registry = {}

    def save_registry(self):
        """Save review_registry.json."""
        try:
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump(self.registry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Error] Failed to save registry: {e}")

    def reconcile_arfr(self):
        """Automatic Registry-Filesystem Reconciliation (ARFR).
        
        Scans PP directory and updates registry based on files.
        - Production profiles (Name.docx or <Num>) Name.docx) -> 'approved'.
        - Review profiles (Name_review.docx) -> 'pending' (re-opened if rejected).
        """
        if not os.path.isdir(self.pp_dir):
            return

        # Scan files in PP_DIR
        production_names = set()
        review_names = set()

        for fname in os.listdir(self.pp_dir):
            if not fname.lower().endswith(".docx"):
                continue
            
            # Skip template and UO files
            if fname == "PP Form details.docx" or "uo" in fname.lower():
                continue

            if fname.lower().endswith("_review.docx"):
                # Review profile: e.g. "Arippa_review.docx" -> name "arippa"
                name_part = fname[:-12]  # strip _review.docx
                review_names.add(name_part.strip().lower())
            else:
                # Production profile: e.g. "1)  Sachin.docx" or "Sachin.docx"
                name_part = fname[:-5]  # strip .docx
                m = re.match(r"^\d+\)\s*(.*)", name_part)
                if m:
                    name_part = m.group(1)
                production_names.add(name_part.strip().lower())

        # Apply state reconciliation rules
        modified = False
        
        # Rule 1: Production profile exists -> status is "approved"
        for name in production_names:
            entry = self.registry.get(name, {})
            if entry.get("status") != "approved":
                self.registry[name] = {
                    "status": "approved",
                    "last_seen": datetime.utcnow().isoformat() + "Z"
                }
                modified = True

        # Rule 2: Review profile exists -> status is "pending" if it was "rejected" or not present
        for name in review_names:
            if name in production_names:
                # If production profile ALSO exists, production wins (approved)
                continue
            entry = self.registry.get(name, {})
            if entry.get("status") in ("rejected", None):
                self.registry[name] = {
                    "status": "pending",
                    "last_seen": datetime.utcnow().isoformat() + "Z"
                }
                modified = True

        if modified:
            self.save_registry()
            print(f"[ARFR] Registry reconciled with filesystem.")

    def get_status(self, name: str) -> str:
        """Get the status of a name from the registry (pending, approved, rejected, or None)."""
        name_lower = name.strip().lower()
        entry = self.registry.get(name_lower)
        if entry:
            return entry.get("status")
        return None

    def reject_name(self, name: str):
        """Mark a name as rejected in the registry."""
        name_lower = name.strip().lower()
        self.registry[name_lower] = {
            "status": "rejected",
            "last_seen": datetime.utcnow().isoformat() + "Z"
        }
        self.save_registry()

    def approve_name(self, name: str):
        """Mark a name as approved in the registry."""
        name_lower = name.strip().lower()
        self.registry[name_lower] = {
            "status": "approved",
            "last_seen": datetime.utcnow().isoformat() + "Z"
        }
        self.save_registry()

    def _resolve_model(self) -> str:
        """Find the best available model from Ollama, prioritizing cloud models."""
        try:
            r = requests.get(f"{self.ollama_url}/api/tags", timeout=3)
            if r.status_code == 200:
                tags = [t["name"] for t in r.json().get("models", [])]
                for preferred in ["gpt-oss", "gemma2", "llama3", "qwen2.5"]:
                    for t in tags:
                        if t.lower().startswith(preferred):
                            return t
        except Exception:
            pass
        return ""

    def classify_candidates(self, text: str, candidates: list) -> dict:
        """Classify candidate names using pretrained HF model, Ollama model, or heuristics fallback."""
        classifications = {}
        if not candidates:
            return classifications

        # Method 1: Try pretrained HF model
        if self.initialize_ner_pipeline():
            try:
                results = self.ner_pipeline(text)
                extracted_entities = {}
                for ent in results:
                    word = ent.get("word", "").strip()
                    entity_type = ent.get("entity_group", "")
                    if word and entity_type:
                        norm_type = {
                            "PER": "PERSON",
                            "LOC": "LOCATION",
                            "ORG": "ORGANIZATION"
                        }.get(entity_type, "")
                        if norm_type:
                            extracted_entities[word.lower()] = norm_type
                
                # Match candidates to the extracted entities
                from utils import is_fuzzy_match
                for cand in candidates:
                    cand_low = cand.lower()
                    matched_type = None
                    for ent_word, ent_type in extracted_entities.items():
                        if cand_low == ent_word or is_fuzzy_match(cand_low, ent_word):
                            matched_type = ent_type
                            break
                    if matched_type:
                        classifications[cand] = matched_type
            except Exception as e:
                print(f"  [Warning] Pretrained HF NER prediction failed: {e}. Falling back.")

        # Method 2: Try Ollama model if any candidates remain unclassified
        unclassified = [c for c in candidates if c not in classifications]
        if unclassified:
            model_to_use = self._resolve_model()
            use_ollama = bool(model_to_use)

            if use_ollama:
                prompt = (
                    "You are an expert intelligence analyst for the Kerala Police.\n"
                    "Analyze the following text and classify each of the candidate names listed below "
                    "strictly as one of these categories:\n"
                    "- 'PERSON': actual human names, typically Kerala or Indian names (e.g., 'Sachin', 'Beena', 'Chittoor Kutty').\n"
                    "- 'LOCATION': places, districts, towns, or villages (e.g., 'Meppadi', 'Arippa').\n"
                    "- 'ORGANIZATION': political parties, front groups, unions, or committees (e.g., 'RSU', 'KMP').\n"
                    "- 'JUNK': administrative words, boilerplate, titles, police ranks, dates, page numbers, or noise (e.g., 'Signature', 'Sd', 'Copy', 'Inspector', 'Police').\n\n"
                    f"Text:\n\"\"\"{text}\"\"\"\n\n"
                    f"Candidates:\n{', '.join(unclassified)}\n\n"
                    "Return the classification as a JSON object where each candidate name is a key, "
                    "and the value is its classification (strictly one of 'PERSON', 'LOCATION', 'ORGANIZATION', or 'JUNK').\n"
                    "Do not include any other text, markdown formatting, or explanations in the response. "
                    "Output ONLY valid JSON."
                )
                try:
                    resp = requests.post(
                        f"{self.ollama_url}/api/generate",
                        json={"model": model_to_use, "prompt": prompt, "stream": False, "format": "json"},
                        timeout=30
                    )
                    if resp.status_code == 200:
                        response_text = resp.json().get("response", "").strip()
                        parsed = json.loads(response_text)
                        for cand in unclassified:
                            val = parsed.get(cand)
                            if val in {"PERSON", "LOCATION", "ORGANIZATION", "JUNK"}:
                                classifications[cand] = val
                except Exception as e:
                    print(f"[Warning] NER model classification failed: {e}. Falling back to heuristics.")

        # Method 3: Final fallback to heuristics
        for cand in candidates:
            if cand not in classifications or classifications[cand] == "JUNK":
                cand_low = cand.lower()
                if cand_low in PLACE_NAMES:
                    classifications[cand] = "LOCATION"
                elif cand_low in JUNK_WORDS:
                    classifications[cand] = "ORGANIZATION"
                else:
                    # Double guard: if any token is a junk word, classify as ORGANIZATION
                    if any(tok.strip(".,()[]{}'\"-:") in JUNK_WORDS for tok in cand_low.split()):
                        classifications[cand] = "ORGANIZATION"
                    else:
                        classifications[cand] = "PERSON"

        return classifications

    def extract_structured_profile_data(self, text: str) -> dict:
        """Extract structured personal, organizational, relational, and case details using Ollama LLM."""
        default_data = {
            "personal_details": {"parentage": "", "address": "", "police_station": ""},
            "organization_involvement": {"org_name": "", "remarks": ""},
            "relations": [],
            "case_details": {
                "fir_number": "",
                "under_sections": "",
                "police_station": "",
                "case_brief": "",
                "case_status": "Under Investigation",
                "co_accused": ""
            },
            "brief_history": ""
        }

        model_to_use = self._resolve_model()
        if not model_to_use:
            return default_data

        prompt = (
            "You are an expert intelligence analyst for the Kerala Police.\n"
            "Analyze the following intelligence report text and extract structured information to populate a suspect's profile dossier.\n"
            "Extract details strictly matching the following schema and rules:\n"
            "1. 'personal_details':\n"
            "   - 'parentage': Name of father, mother, or spouse if mentioned with s/o, d/o, w/o (e.g. 'Sivadasan').\n"
            "   - 'address': Residence address or home town (e.g. 'Meleparambil, Nilambur, Palakkad').\n"
            "   - 'police_station': The specific police station jurisdiction for their residence or crime (e.g. 'Chittur').\n"
            "2. 'organization_involvement':\n"
            "   - 'org_name': The extremist, radical, or political group they are associated with (e.g. 'Maoist', 'RSU', 'KMP').\n"
            "   - 'remarks': Details or role in that organization.\n"
            "3. 'relations': A list of relatives mentioned in the text. Each relative should have 'name', 'relation' (e.g. Father, Mother, Spouse), 'address', and 'mobile'. Leave address and mobile blank if not in text.\n"
            "4. 'case_details':\n"
            "   - 'fir_number': FIR or crime number mentioned (e.g. '118/2026' or 'Crime No. 843/2022').\n"
            "   - 'under_sections': The legal sections under which they are charged (e.g. '192, 353(1)(b) BNS').\n"
            "   - 'police_station': The police station where the crime/FIR was registered (e.g. 'Chittur PS').\n"
            "   - 'case_brief': A concise English summary of the specific illegal action they took (e.g. 'boycotting election through his facebook account').\n"
            "   - 'case_status': Set to 'Under Investigation' or 'Pending Trial' if sections/FIR are active.\n"
            "   - 'co_accused': Names of other individuals arrested or accused in the same case.\n"
            "5. 'brief_history': A 1-2 sentence narrative summary describing who this person is and their main active issues.\n\n"
            f"Text:\n\"\"\"{text}\"\"\"\n\n"
            "Return the output strictly in this JSON format. Do not include any formatting, code blocks, or markdown explanations. Output ONLY valid JSON."
        )

        try:
            resp = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": model_to_use, "prompt": prompt, "stream": False, "format": "json"},
                timeout=30
            )
            if resp.status_code == 200:
                response_text = resp.json().get("response", "").strip()
                # Find JSON block
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    json_str = response_text[start_idx:end_idx+1]
                    data = json.loads(json_str)
                    
                    # Merge with default_data to ensure keys are present
                    result = {}
                    for k, default_val in default_data.items():
                        extracted_val = data.get(k)
                        if isinstance(default_val, dict) and isinstance(extracted_val, dict):
                            result[k] = {subkey: extracted_val.get(subkey, default_val[subkey]) for subkey in default_val}
                        elif isinstance(default_val, list) and isinstance(extracted_val, list):
                            result[k] = extracted_val
                        else:
                            result[k] = extracted_val if extracted_val is not None else default_val
                    return result
        except Exception as e:
            print(f"[Warning] Structured profile data extraction failed: {e}.")

        return default_data

    def extract_person_names(self, text: str) -> list:
        """Extract person names directly from text using pretrained HF model.
        
        Falls back to rule-based candidate classification if pretrained model fails or is unavailable.
        """
        # Try Method 1: Pretrained HF model (no candidate lists or junk words)
        if self.initialize_ner_pipeline():
            try:
                results = self.ner_pipeline(text)
                person_names = []
                for ent in results:
                    if ent.get("entity_group") == "PER":
                        name = ent.get("word", "").strip()
                        # Clean subwords or BPE formatting if any
                        name = name.replace(" ##", "").replace("##", "")
                        # Filter out very short noise
                        if name and len(name) >= 3:
                            person_names.append(name)
                if person_names:
                    return list(set(person_names))
            except Exception as e:
                print(f"  [Warning] HF NER extraction failed: {e}. Falling back to candidate classification.")

        # Fallback: Extract candidates and classify them (uses Ollama/heuristics and JUNK_WORDS)
        from utils import extract_candidate_names_from_text
        candidates = extract_candidate_names_from_text(text)
        classifications = self.classify_candidates(text, candidates)
        return [cand for cand, cls in classifications.items() if cls == "PERSON"]

    def process_candidate(self, name: str, text: str, template_path: str, report_date: str) -> str:
        """Verified Entity Gate (VEG) State-Machine.
        
        Checks if the candidate PERSON name matches PLACE_NAMES or JUNK_WORDS.
        If yes, applies the state-machine rules:
        - If rejected: returns "ignored".
        - If pending: updates last_seen, returns "pending_already_exists".
        - If approved: returns "approved".
        - If new: creates Name_review.docx, sets pending in registry, returns "pending_new".
        
        If it does not match PLACE_NAMES/JUNK_WORDS, it bypasses the review queue and returns "approved".
        """
        name_lower = name.strip().lower()
        
        if name_lower in PLACE_NAMES or name_lower in JUNK_WORDS:
            status = self.get_status(name)
            
            if status == "rejected":
                return "ignored"
                
            elif status == "pending":
                self.registry[name_lower]["last_seen"] = datetime.utcnow().isoformat() + "Z"
                self.save_registry()
                return "pending_already_exists"
                
            elif status == "approved":
                return "approved"
                
            else:
                self.registry[name_lower] = {
                    "status": "pending",
                    "last_seen": datetime.utcnow().isoformat() + "Z"
                }
                self.save_registry()
                
                safe_name = re.sub(r'[<>:"/\\|?*]', '_', name)
                review_path = os.path.join(self.pp_dir, f"{safe_name}_review.docx")
                if not os.path.exists(review_path):
                    create_new_profile(
                        name=name,
                        activity_desc=text[:300],
                        activity_date=report_date,
                        template_path=template_path,
                        output_path=review_path
                    )
                return "pending_new"
        else:
            return "approved"
