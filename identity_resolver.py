import re
import difflib
from utils import is_fuzzy_match, soundex_kerala, PersonProfile

class IdentityResolver:
    def __init__(self):
        pass

    def extract_identifying_info(self, text: str) -> dict:
        """Extract parentage name, DOB, and places/PS from the text paragraph."""
        info = {
            "parentage": "",
            "dob": "",
            "places": []
        }
        
        # 1. Extract parentage name (S/o, D/o, W/o patterns)
        parent_match = re.search(
            r"\b([SsDdWw]/[Oo]|spouse\s+of|son\s+of|daughter\s+of|wife\s+of)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})", 
            text
        )
        if parent_match:
            info["parentage"] = parent_match.group(2).strip()
            
        # 2. Extract DOB (Date of Birth) from text (if any)
        dob_match = re.search(
            r"\b(?:DOB|born|date\s+of\s+birth)(?:\s*[:-–]\s*|\s+on\s+)?(\d{2}[-./]\d{2}[-./]\d{4})", 
            text, 
            re.IGNORECASE
        )
        if dob_match:
            info["dob"] = dob_match.group(1).strip()
            
        # 3. Extract places / police station boundaries
        ps_matches = re.findall(
            r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s*(?:P\s*S|Police\s+Station|limits)\b", 
            text,
            re.IGNORECASE
        )
        info["places"] = [ps.strip() for ps in ps_matches if ps.strip()]
        
        return info

    def match_profile(self, extracted: dict, profile: PersonProfile) -> float:
        """Compute match confidence between extracted details and a profile dossier.
        
        Returns:
            confidence score (float, usually between -1.0 and 1.0)
        """
        score = 0.0

        # Extract values from profile
        prof_parentage = profile.parentage
        prof_dob = profile.data.get("DOB", "").strip()
        prof_ps = profile.police_station
        prof_address = profile.address

        # 1. Match Parentage Name
        if extracted["parentage"] and prof_parentage:
            if is_fuzzy_match(extracted["parentage"], prof_parentage):
                score += 0.6
            else:
                # Strong negative score for mismatching parent
                score -= 0.8
        
        # 2. Match Date of Birth (DOB)
        if extracted["dob"] and prof_dob:
            # Normalize dates before comparing: replace '/' or '.' with '-'
            norm_ext_dob = extracted["dob"].replace(".", "-").replace("/", "-")
            norm_prof_dob = prof_dob.replace(".", "-").replace("/", "-")
            if norm_ext_dob == norm_prof_dob:
                score += 0.8
            else:
                # Absolute DOB mismatch is a very strong negative signal
                score -= 0.9

        # 3. Match Police Station
        if prof_ps and extracted["places"]:
            # Check if profile PS is mentioned in the text
            ps_clean = prof_ps.lower().replace("p s", "").replace("ps", "").strip()
            if len(ps_clean) > 2:
                ps_matched = False
                for pl in extracted["places"]:
                    if is_fuzzy_match(ps_clean, pl):
                        ps_matched = True
                        break
                if ps_matched:
                    score += 0.3

        # 4. Check address overlap
        if prof_address and extracted["places"]:
            address_lower = prof_address.lower()
            overlap_count = 0
            for pl in extracted["places"]:
                if pl.lower() in address_lower:
                    overlap_count += 1
            if overlap_count > 0:
                score += min(0.3, overlap_count * 0.15)

        return score

    def resolve_identity(self, name: str, text: str, profiles: list, report_date: str) -> tuple:
        """Find the matching profile for a name based on rule-based scoring.
        
        Returns:
            (matched_profile_obj, resolution_status)
            where resolution_status can be:
                - "auto_merged" (high confidence)
                - "pending_review" (medium/low confidence match)
                - "new_suspect" (no matching profiles, or all are mismatches)
        """
        # Find profiles with matching names
        name_matches = []
        for prof in profiles:
            if prof.name and is_fuzzy_match(name, prof.name):
                name_matches.append(prof)
                
        if not name_matches:
            return None, "new_suspect"

        extracted = self.extract_identifying_info(text)
        
        # If there are candidates, score them
        scored_candidates = []
        for prof in name_matches:
            score = self.match_profile(extracted, prof)
            scored_candidates.append((prof, score))
            
        # Sort by score descending
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        best_prof, best_score = scored_candidates[0]
        
        # Determine status based on thresholds
        if best_score >= 0.6:
            # Check for ambiguity (another candidate with a close high score)
            if len(scored_candidates) > 1 and scored_candidates[1][1] >= 0.5:
                return best_prof, "pending_review"
            return best_prof, "auto_merged"
        elif best_score <= -0.5:
            # Strong mismatch
            return None, "new_suspect"
        else:
            # Low/medium confidence (or score is 0.0 because of missing/insufficient info)
            return best_prof, "pending_review"
