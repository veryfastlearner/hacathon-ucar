import re
from typing import List, Tuple
from app.models.schemas import KPISchema, ValidationQueue

class DataValidator:
    
    @staticmethod
    def validate_kpis(kpis: List[dict]) -> Tuple[List[dict], List[dict]]:
        """
        Validates a list of raw KPI dicts.
        Returns a tuple: (valid_kpis, validation_queue_items).
        """
        valid_kpis = []
        validation_queue = []
        
        # We index by name for complex document-level cross-checks (public + private = total)
        kpi_map = {k['kpi_name']: k for k in kpis}
        
        for k in kpis:
            reason = None
            val = k.get('kpi_value')
            conf = k.get('confidence_score', 0.0)
            
            # Rule 5: Reject fallback_demo_extraction
            if k.get('fallback_demo_extraction'):
                reason = "Rule 5 Triggered: Fake/Fallback data detected. Not allowed."
                
            # Rule 3: Percentage bounds
            if k.get('unit') == "%" and isinstance(val, (int, float)):
                if val < 0 or val > 100:
                    reason = f"Rule 3 Triggered: Percentage {val} out of bounds (0-100)."
                    
            # Rule 4: Academic year format (e.g., 2019/2020)
            ay = k.get('academic_year')
            if ay and not re.match(r"^\d{4}/\d{4}$", str(ay)):
                reason = f"Rule 4 Triggered: Invalid academic year format '{ay}'."
                
            # Confidence logic
            if not reason:
                if conf < 0.70:
                    reason = f"Low Confidence Score: {conf}"
            
            if reason:
                k['validation_status'] = "Manual Review Required"
            else:
                k['validation_status'] = "Auto Validated" if conf >= 0.90 else "Needs Review"
                
            if k['validation_status'] == "Manual Review Required":
                vq = dict(k)
                vq['validation_reason'] = reason
                validation_queue.append(vq)
            else:
                valid_kpis.append(k)
                
        # Rule 2: public + private = total
        # We check within the valid_kpis to see if there's a contradiction.
        # If contradiction found, we shift them to the validation queue.
        if "students_total" in kpi_map and "students_public" in kpi_map and "students_private" in kpi_map:
            tot = kpi_map["students_total"].get("kpi_value", 0)
            pub = kpi_map["students_public"].get("kpi_value", 0)
            pri = kpi_map["students_private"].get("kpi_value", 0)
            if pub + pri != tot:
                for target_name in ["students_total", "students_public", "students_private"]:
                    # Find and shift
                    for idx, v in enumerate(valid_kpis):
                        if v['kpi_name'] == target_name:
                            popped = valid_kpis.pop(idx)
                            popped['validation_status'] = "Manual Review Required"
                            popped['validation_reason'] = f"Rule 2 Contradiction: pub({pub}) + pri({pri}) != tot({tot})"
                            validation_queue.append(popped)
                            break
                            
        return valid_kpis, validation_queue

