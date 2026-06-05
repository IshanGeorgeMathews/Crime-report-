import app.core.paths  # Configures Python path for importing existing modules
import os
import re
from typing import List, Dict, Any
from datetime import datetime

from ner_engine import NEREngine
from utils import PersonProfile
from app.config import settings

class NERService:
    def __init__(self):
        self.engine = NEREngine(
            pp_dir=settings.PP_DIR,
            ollama_url=settings.OLLAMA_URL
        )

    def get_review_queue(self) -> List[Dict[str, Any]]:
        """Run ARFR reconciliation and return list of pending review candidates."""
        self.engine.reconcile_arfr()
        
        pending_items = []
        for name_lower, entry in self.engine.registry.items():
            if entry.get("status") == "pending":
                # Find the review file: e.g. "Jacob_review.docx"
                # The filename on disk uses the original capitalization if possible,
                # otherwise we look for a file ending with "_review.docx"
                name_cap = name_lower.title()
                safe_name = re.sub(r'[<>:"/\\|?*]', '_', name_cap)
                review_file = f"{safe_name}_review.docx"
                review_path = os.path.join(settings.PP_DIR, review_file)
                
                # Fallback check for exact file match with lowercase/other casing
                if not os.path.exists(review_path):
                    for f in os.listdir(settings.PP_DIR):
                        if f.lower() == f"{name_lower}_review.docx":
                            review_path = os.path.join(settings.PP_DIR, f)
                            break
                
                source = "Extracted from daily intelligence logs. Needs disambiguation."
                extraction_method = "HF bert-base-NER"
                anomaly_flags = "None"
                
                if os.path.exists(review_path):
                    try:
                        # Parse the review docx file details
                        prof = PersonProfile(review_path)
                        if prof.brief_history:
                            source = prof.brief_history
                        elif prof.reason_for_inclusion:
                            source = prof.reason_for_inclusion
                        
                        if prof.activity_type:
                            anomaly_flags = f"Activity Category: {prof.activity_type}"
                    except Exception as e:
                        print(f"[Warning] Failed to parse review profile docx: {e}")
                
                pending_items.append({
                    "id": name_lower,
                    "name": name_cap,
                    "source": source,
                    "extractionMethod": extraction_method,
                    "anomalyFlags": anomaly_flags,
                    "status": "pending"
                })
        return pending_items

    def approve_candidate(self, name_id: str) -> bool:
        """Approve a review candidate."""
        self.engine.reconcile_arfr()
        name_lower = name_id.strip().lower()
        if name_lower in self.engine.registry:
            self.engine.approve_name(name_lower)
            
            # Rename *_review.docx to a production profile name
            # Let's find the review file
            for f in os.listdir(settings.PP_DIR):
                if f.lower() == f"{name_lower}_review.docx":
                    old_path = os.path.join(settings.PP_DIR, f)
                    
                    # Find the next sequential number
                    existing_nums = [
                        int(m.group(1))
                        for file in os.listdir(settings.PP_DIR)
                        for m in [re.match(r'^(\d+)\)', file)]
                        if m
                    ]
                    next_num = max(existing_nums, default=0) + 1
                    
                    name_cap = name_lower.title()
                    safe_name = re.sub(r'[<>:"/\\|?*]', '_', name_cap)
                    new_filename = f"{next_num})  {safe_name}.docx"
                    new_path = os.path.join(settings.PP_DIR, new_filename)
                    
                    try:
                        os.rename(old_path, new_path)
                        print(f"[NER Service] Approved and renamed review profile: {f} -> {new_filename}")
                        
                        # Also update the profile PP ID field in the docx if needed
                        # (The frontend can view and edit the profile, so the docx itself is updated)
                        prof = PersonProfile(new_path)
                        # Generate a mock PP ID or let supervisor assign one
                        prof.pp_id = f"{next_num:03d}/{prof.police_station or 'PKD'}"
                        prof.save()
                    except Exception as e:
                        print(f"[Error] Failed to rename/update profile file: {e}")
            return True
        return False

    def reject_candidate(self, name_id: str) -> bool:
        """Reject a review candidate and delete its review docx."""
        self.engine.reconcile_arfr()
        name_lower = name_id.strip().lower()
        if name_lower in self.engine.registry:
            self.engine.reject_name(name_lower)
            
            # Delete the *_review.docx file
            for f in os.listdir(settings.PP_DIR):
                if f.lower() == f"{name_lower}_review.docx":
                    path = os.path.join(settings.PP_DIR, f)
                    try:
                        os.remove(path)
                        print(f"[NER Service] Rejected and deleted review profile: {f}")
                    except Exception as e:
                        print(f"[Error] Failed to delete review profile: {e}")
            return True
        return False
