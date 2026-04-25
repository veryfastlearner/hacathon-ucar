import os

class DocumentClassifier:
    
    @staticmethod
    def classify_file(file_path: str) -> str:
        """Classifies the document into specific predefined types."""
        base_name = os.path.basename(file_path).lower()
        
        if base_name.endswith('.xlsx') or base_name.endswith('.xls'):
            if "academique" in base_name or "resultats" in base_name:
                return "excel_academic_results"
            
        elif base_name.endswith('.pdf'):
            if "emploi_du_temps" in base_name:
                return "pdf_timetable"
            if "finance" in base_name or "tdr" in base_name:
                return "pdf_finance_admin"
            if "dep_fr" in base_name:
                return "pdf_dep_fr"
                
        return "unknown"
