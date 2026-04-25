from app.models.schemas import KPISchema
from app.utils.institution_mapping import get_institution_id
from typing import List

class KPIGenerator:
    
    @staticmethod
    def _create_kpi(base: dict, name: str, val: any, unit: str) -> dict:
        k = dict(base)
        k["kpi_name"] = name
        k["kpi_label"] = name.replace("_", " ").title()
        k["kpi_value"] = val
        k["unit"] = unit
        k["fallback_demo_extraction"] = False
        k["institution_id"] = get_institution_id(k["institution_name"])
        return k

    @staticmethod
    def generate_academic(excel_raw: dict, filename: str) -> List[dict]:
        kpis = []
        raw_list = excel_raw.get("extracted_raw", [])
        base = {
            "institution_name": "Faculté des Sciences Juridiques, Politiques et Sociales de Tunis",
            "document_id": "ACAD_01",
            "document_type": "excel_academic_results",
            "domain": "Académique",
            "source_file": filename,
            "extraction_method": "Excel Parser",
            "confidence_score": excel_raw.get("confidence", 0.95),
        }
        for item in raw_list:
            kpis.append(KPIGenerator._create_kpi(base, item["name"], item["val"], item["unit"]))
        return kpis

    @staticmethod
    def generate_finance(fields: dict, filename: str) -> List[dict]:
        kpis = []
        mapping = {
            "audit_reports_required": ("number_of_reports", "count"),
            "audit_cycle_months": ("audit_cycle_months", "months"),
            "technical_score_max": ("technical_score_max", "points"),
            "financial_score_max": ("financial_score_max", "points"),
            "procurement_deadline_detected": (1 if "submission_deadline" in fields else 0, "bool"),
            "global_score_formula_detected": (1 if "global_score_formula" in fields else 0, "bool")
        }
        
        base = {
            "institution_name": fields.get("beneficiary", "Université de Carthage"),
            "document_id": "FIN_01",
            "document_type": "pdf_finance_admin",
            "domain": "Finance / Administration",
            "source_file": filename,
            "extraction_method": fields.get("method", "PyMuPDF Native Text"),
            "confidence_score": fields.get("confidence", 0.95),
        }
        
        for k_name, (fk, unit) in mapping.items():
            if fk in fields or fk == 1:
                val = fields.get(fk, 1)
                kpis.append(KPIGenerator._create_kpi(base, k_name, val, unit))
        return kpis

    @staticmethod
    def generate_timetable(fields: dict, filename: str) -> List[dict]:
        kpis = []
        mapping = {
            "weekly_sessions_count": ("weekly_sessions_count", "count"),
            "weekly_hours_estimated": ("weekly_hours_estimated", "hours"),
            "unique_teachers_count": ("unique_teachers_count", "count"),
            "unique_rooms_count": ("unique_rooms_count", "count")
        }
        
        base = {
            "institution_name": fields.get("institution_name", "UCAR"),
            "document_id": "TIME_01",
            "document_type": "pdf_timetable",
            "domain": "Infrastructure",
            "source_file": filename,
            "extraction_method": fields.get("method", "PyMuPDF Table Extraction"),
            "confidence_score": fields.get("confidence", 0.70),
            "academic_year": fields.get("academic_year")
        }
        
        for k_name, (fk, unit) in mapping.items():
            kpis.append(KPIGenerator._create_kpi(base, k_name, fields.get(fk, 0), unit))
        return kpis

    @staticmethod
    def generate_dep_fr(fields: dict, filename: str) -> List[dict]:
        kpis = []
        mapping = {
            "budget_mesrs_millions": ("budget_mesrs_millions", "M TND"),
            "students_total": ("total_students", "count"),
            "students_public": ("students_public", "count"),
            "students_private": ("students_private", "count"),
            "private_sector_percentage": ("private_sector_percentage", "%"),
            "university_residences": ("university_residences", "count"),
            "research_labs": ("research_labs", "count"),
            "research_teachers": ("research_teachers", "count"),
            "foreign_students_count": ("foreign_students_count", "count"),
            "african_students_count": ("african_students_count", "count")
        }
        
        base = {
            "institution_name": fields.get("institution_name", "MESRS"),
            "document_id": "NAT_IND_01",
            "document_type": "pdf_national_indicators",
            "domain": "Académique / National",
            "source_file": filename,
            "extraction_method": fields.get("method", "Regex Pattern Matching"),
            "confidence_score": fields.get("confidence", 0.95)
        }
        
        for k_name, (fk, unit) in mapping.items():
            if fk in fields:
                val = fields.get(fk)
                kpis.append(KPIGenerator._create_kpi(base, k_name, val, unit))
        return kpis
