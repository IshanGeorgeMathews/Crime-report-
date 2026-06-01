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

    def classify_candidates(self, text: str, candidates: list) -> dict:
        """Classify candidate names using Gemma2 via Ollama if available.
        
        Fallback to heuristic classifier if Ollama is not available or fails.
        Returns a dict mapping candidate name -> classification (PERSON, LOCATION, ORGANIZATION).
        """
        classifications = {}
        if not candidates:
            return classifications

        # Check if Ollama is reachable and gemma2 is installed
        use_ollama = False
        try:
            r = requests.get(f"{self.ollama_url}/api/tags", timeout=3)
            if r.status_code == 200:
                tags = [t["name"] for t in r.json().get("models", [])]
                if any("gemma2" in t for t in tags):
                    use_ollama = True
        except Exception:
            pass

        if use_ollama:
            prompt = (
                "Analyze the following text and classify each of the candidate names listed below "
                "strictly as either 'PERSON', 'LOCATION', or 'ORGANIZATION'.\n"
                f"Text:\n\"\"\"{text}\"\"\"\n\n"
                f"Candidates:\n{', '.join(candidates)}\n\n"
                "Return the classification as a JSON object where each candidate name is a key, "
                "and the value is its classification (strictly one of 'PERSON', 'LOCATION', or 'ORGANIZATION').\n"
                "Do not include any other text, markdown formatting, or explanations in the response. "
                "Output ONLY valid JSON."
            )
            try:
                resp = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={"model": "gemma2", "prompt": prompt, "stream": False, "format": "json"},
                    timeout=30
                )
                if resp.status_code == 200:
                    response_text = resp.json().get("response", "").strip()
                    parsed = json.loads(response_text)
                    for cand in candidates:
                        val = parsed.get(cand)
                        if val in {"PERSON", "LOCATION", "ORGANIZATION"}:
                            classifications[cand] = val
            except Exception as e:
                print(f"[Warning] Gemma2 classification failed: {e}. Falling back to heuristics.")

        # Fallback to heuristics for any unclassified candidates
        for cand in candidates:
            if cand not in classifications:
                cand_low = cand.lower()
                if cand_low in PLACE_NAMES:
                    classifications[cand] = "LOCATION"
                elif cand_low in JUNK_WORDS:
                    classifications[cand] = "ORGANIZATION"
                else:
                    classifications[cand] = "PERSON"

        return classifications

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
