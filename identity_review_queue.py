import os
import re
import json
from datetime import datetime
from utils import create_new_profile, PersonProfile

REGISTRY_NAME = "review_registry.json"

class IdentityReviewQueue:
    def __init__(self, pp_dir: str):
        self.pp_dir = pp_dir
        self.registry_path = os.path.join(pp_dir, REGISTRY_NAME)

    def _load_registry_nolock(self) -> dict:
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Warning] Failed to load registry in IdentityReviewQueue: {e}")
        return {}

    def _save_registry_nolock(self, registry: dict):
        try:
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Error] Failed to save registry in IdentityReviewQueue: {e}")

    def load_registry(self) -> dict:
        from filelock import FileLock
        lock = FileLock(self.registry_path + ".lock", timeout=5)
        with lock:
            return self._load_registry_nolock()

    def save_registry(self, registry: dict):
        from filelock import FileLock
        lock = FileLock(self.registry_path + ".lock", timeout=5)
        with lock:
            self._save_registry_nolock(registry)

    def add_to_review(self, name: str, text: str, report_date: str, template_path: str, parentage: str = ""):
        """Route a suspect to the review queue, creating docx and updating registry."""
        from filelock import FileLock
        lock = FileLock(self.registry_path + ".lock", timeout=5)
        with lock:
            registry = self._load_registry_nolock()
            name_lower = name.lower()
            
            # 1. Update registry
            registry[name_lower] = {
                "status": "pending",
                "last_seen": datetime.utcnow().isoformat() + "Z",
                "reason": "Identity Resolution: Low-confidence / Ambiguous name match"
            }
            self._save_registry_nolock(registry)
        
        # 2. Create the review docx file (Name_review.docx)
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', name)
        review_filename = f"{safe_name}_review.docx"
        review_path = os.path.join(self.pp_dir, review_filename)
        
        if not os.path.exists(review_path):
            create_new_profile(
                name=name,
                parentage=parentage,
                activity_desc=text[:300],
                activity_date=report_date,
                template_path=template_path,
                output_path=review_path,
            )
            print(f"  [Review Queue] Created review dossier: {review_filename}")
        else:
            # If the review dossier already exists, append this new activity description
            from utils import update_profile_activity
            update_profile_activity(
                profile_path=review_path,
                activity_name=f"Mentioned in IS Report {report_date} (Pending Resolution)",
                activity_desc=text[:300],
                activity_date=report_date
            )
            print(f"  [Review Queue] Updated existing review dossier: {review_filename}")
