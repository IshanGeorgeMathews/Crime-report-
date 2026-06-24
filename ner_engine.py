import os
import re
import json
import requests
import unicodedata
from datetime import datetime

# Import profile creation helper from utils
from utils import create_new_profile

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
            model_name = os.getenv("NER_MODEL_PATH", "dslim/bert-base-NER")
            print(f"  [NER Engine] Loading Hugging Face {model_name} model...")
            device = 0 if torch.cuda.is_available() else -1
            self.ner_pipeline = pipeline(
                "ner", 
                model=model_name, 
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
        """Find the best available local Ollama model, prioritizing Qwen."""
        try:
            r = requests.get(f"{self.ollama_url}/api/tags", timeout=3)
            if r.status_code == 200:
                tags = [t["name"] for t in r.json().get("models", [])]
                for preferred in ["qwen", "qwen2.5", "gemma2", "llama3"]:
                    for t in tags:
                        if t.lower().startswith(preferred):
                            return t
        except Exception:
            pass
        return ""

    def classify_candidates(self, text: str, candidates: list) -> dict:
        """Classify candidate names using the Ollama LLM as the sole authority.

        The LLM decides whether each candidate is a real human person name,
        a location, an organization, or junk/noise.  There is NO hardcoded
        word-list fallback — if the LLM is unavailable the safe default is
        JUNK (i.e. we never create a profile for something we can't verify).
        """
        classifications = {}
        if not candidates:
            return classifications

        model_to_use = self._resolve_model()

        if model_to_use:
            prompt = (
                "You are an expert intelligence analyst for the Kerala Police.\n"
                "Your task is to classify each candidate word/phrase below into EXACTLY one category.\n\n"
                "Categories:\n"
                "- 'PERSON': A real human being's personal name. "
                "  Typical Indian/Kerala names such as 'Sachin', 'Beena', 'Chittoor Kutty', 'Mohammed Shareef'.\n"
                "  IMPORTANT: Only classify as PERSON if it is genuinely a human's given name or full name.\n"
                "- 'LOCATION': A geographic place — town, village, district, state, country "
                "  (e.g. 'Meppadi', 'Arippa', 'Kollam', 'Kozhikode', 'Kerala').\n"
                "- 'ORGANIZATION': Political parties, unions, front groups, committees, government bodies "
                "  (e.g. 'RSU', 'KMP', 'Congress', 'Revenue Department', 'CPI').\n"
                "- 'JUNK': Everything else — administrative words, report boilerplate, ranks, titles, "
                "  dates, page numbers, legal terms, common English nouns, verbs, or adjectives "
                "  that are NOT a person's name "
                "  (e.g. 'Revenue', 'Signature', 'Inspector', 'Police', 'Copy', 'Forecast', "
                "  'District', 'Intelligence', 'Station', 'Security', 'Order', 'Report').\n\n"
                "CRITICAL RULES:\n"
                "1. Common English dictionary words (Revenue, District, Intelligence, Security, "
                "   General, Division, etc.) are NEVER person names — classify them as JUNK or ORGANIZATION.\n"
                "2. Police/military ranks and titles (Inspector, Superintendent, Commissioner, "
                "   Constable, Officer) are JUNK, not PERSON.\n"
                "3. When in doubt, classify as JUNK. We only want real human names as PERSON.\n"
                "4. A single common English word is almost certainly NOT a person name.\n\n"
                f"Context text for reference:\n\"\"\"{text[:1500]}\"\"\"\n\n"
                f"Candidates to classify:\n{json.dumps(candidates)}\n\n"
                "Return ONLY a valid JSON object where each candidate is a key and its "
                "classification (PERSON / LOCATION / ORGANIZATION / JUNK) is the value.\n"
                "No markdown, no explanation, no code blocks — just the JSON object."
            )
            try:
                resp = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={"model": model_to_use, "prompt": prompt, "stream": False, "format": "json"},
                    timeout=60
                )
                if resp.status_code == 200:
                    response_text = resp.json().get("response", "").strip()
                    # Handle JSON wrapped in a list
                    parsed = json.loads(response_text)
                    if isinstance(parsed, list):
                        parsed = parsed[0] if parsed else {}
                    for cand in candidates:
                        val = parsed.get(cand)
                        if val in {"PERSON", "LOCATION", "ORGANIZATION", "JUNK"}:
                            classifications[cand] = val
            except Exception as e:
                print(f"[Warning] LLM classification failed: {e}. Defaulting unclassified to JUNK.")

        # Safe default: anything NOT classified by the LLM is JUNK.
        # We NEVER default to PERSON — a false negative (missing a real name)
        # is far less harmful than a false positive (creating a profile for 'Revenue').
        for cand in candidates:
            if cand not in classifications:
                classifications[cand] = "JUNK"
                print(f"  [Safe Default] '{cand}' -> JUNK (LLM did not classify)")

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
                timeout=45
            )
            if resp.status_code == 200:
                response_text = resp.json().get("response", "").strip()
                # Find JSON block
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    json_str = response_text[start_idx:end_idx+1]
                    data = json.loads(json_str)
                    if isinstance(data, list):
                        data = data[0] if data else {}
                    if not isinstance(data, dict):
                        data = {}
                    
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
        """Extract person names from text, using HF model to find candidates and Ollama to classify them."""
        candidates = []
        
        # 1. Use HF model to find initial person candidates
        if self.initialize_ner_pipeline():
            try:
                results = self.ner_pipeline(text)
                for ent in results:
                    if ent.get("entity_group") == "PER":
                        name = ent.get("word", "").strip()
                        name = name.replace(" ##", "").replace("##", "")
                        if name and len(name) >= 3:
                            candidates.append(name)
            except Exception as e:
                print(f"  [Warning] HF NER candidate extraction failed: {e}.")
                
        # 2. If HF didn't find anything or failed, use candidate heuristics to get potential names
        if not candidates:
            from utils import extract_candidate_names_from_text
            candidates = extract_candidate_names_from_text(text)
            
        candidates = list(set(candidates))
        if not candidates:
            return []
            
        # 3. Classify candidates using the locally running Ollama model
        classifications = self.classify_candidates(text, candidates)
        
        # 4. Filter only those verified as PERSON by the model
        return [cand for cand, cls in classifications.items() if cls == "PERSON"]

    def batch_extract_person_names(self, texts: list) -> list:
        """Extract person names from a list of texts in batch mode for high throughput."""
        all_candidates = [[] for _ in range(len(texts))]
        if self.initialize_ner_pipeline():
            try:
                # HuggingFace pipeline supports lists of texts natively.
                results_batch = self.ner_pipeline(texts, batch_size=8)
                for idx, results in enumerate(results_batch):
                    for ent in results:
                        if ent.get("entity_group") == "PER":
                            name = ent.get("word", "").strip()
                            name = name.replace(" ##", "").replace("##", "")
                            if name and len(name) >= 3:
                                all_candidates[idx].append(name)
            except Exception as e:
                print(f"  [Warning] Batch HF NER candidate extraction failed: {e}.")
        
        # Fallbacks for empty candidates
        from utils import extract_candidate_names_from_text
        for idx in range(len(texts)):
            if not all_candidates[idx]:
                all_candidates[idx] = extract_candidate_names_from_text(texts[idx])
            all_candidates[idx] = list(set(all_candidates[idx]))

        # Classify candidates for each text
        final_results = []
        for idx, text in enumerate(texts):
            cands = all_candidates[idx]
            if not cands:
                final_results.append([])
                continue
            classifications = self.classify_candidates(text, cands)
            final_results.append([cand for cand, cls in classifications.items() if cls == "PERSON"])
            
        return final_results

    def process_candidate(self, name: str, text: str, template_path: str, report_date: str) -> str:
        """Process a candidate that has ALREADY been classified as PERSON by
        classify_candidates().  Simply returns 'approved' so the caller
        can create / update the profile.

        The old Verified Entity Gate (VEG) with PLACE_NAMES / JUNK_WORDS
        lists has been removed — all semantic filtering now happens inside
        classify_candidates() via the LLM.
        """
        return "approved"
