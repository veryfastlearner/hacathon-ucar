import pandas as pd
from typing import Dict, Any, List
import os

class ExcelParser:
    
    @staticmethod
    def parse_academic_results(file_path: str) -> dict:
        """Reads excel, parses aggregations securely, extracting tables."""
        raw_pages = []
        extracted_tables = []
        extracted_fields = []
        
        try:
            excel = pd.ExcelFile(file_path)
            total_students = 0
            admitted = 0
            failed = 0
            sum_grades = 0.0
            grade_count = 0
            
            for table_idx, sheet in enumerate(excel.sheet_names):
                df = pd.read_excel(file_path, sheet_name=sheet)
                
                # Drop personal columns aggressively
                cols_to_drop = [c for c in df.columns if str(c).lower().strip() in 
                                ['cin', 'nom', 'prenom', 'prénom', 'id', 'date_naissance', 'identifier']]
                safe_df = df.drop(columns=cols_to_drop, errors='ignore')
                
                # Raw text equivalent for excel
                raw_text_repr = safe_df.to_string(index=False)
                raw_pages.append({
                    "document_id": "ACAD_01",
                    "source_file": os.path.basename(file_path),
                    "page_number": table_idx + 1,
                    "raw_text": raw_text_repr
                })
                
                # Extracted Tables
                for row_idx, row in safe_df.iterrows():
                    for col_name, cell_val in row.items():
                        if pd.notna(cell_val):
                            extracted_tables.append({
                                "document_id": "ACAD_01",
                                "source_file": os.path.basename(file_path),
                                "page_number": table_idx + 1,
                                "table_index": table_idx,
                                "row_index": row_idx,
                                "column_name": str(col_name),
                                "cell_value": cell_val,
                                "source_bbox": None,
                                "extraction_method": "Excel Parser",
                                "confidence_score": 1.0
                            })
                            
                total_students += len(safe_df)
                
                status_cols = [c for c in safe_df.columns if "statut" in str(c).lower() or "resultat" in str(c).lower() or "résultat" in str(c).lower()]
                if status_cols:
                    s_col = status_cols[0]
                    admitted += len(safe_df[safe_df[s_col].astype(str).str.contains('admis', case=False, na=False)])
                    failed += len(safe_df[safe_df[s_col].astype(str).str.contains('refus|ajour', case=False, na=False)])
                
                val_cols = [c for c in safe_df.columns if "moy" in str(c).lower() or "note" in str(c).lower()]
                if val_cols:
                    v_col = val_cols[0]
                    numeric_grades = pd.to_numeric(safe_df[v_col], errors='coerce').dropna()
                    sum_grades += numeric_grades.sum()
                    grade_count += len(numeric_grades)
                    
            def add_field(name, val, unit):
                extracted_fields.append({
                    "document_id": "ACAD_01",
                    "source_file": os.path.basename(file_path),
                    "field_name": name,
                    "field_value": val,
                    "unit": unit,
                    "extraction_method": "Excel Parser",
                    "confidence_score": 1.0,
                    "validation_status": "Auto Validated"
                })
                
            if total_students > 0:
                add_field("total_students", total_students, "count")
            if admitted > 0:
                add_field("admitted_students", admitted, "count")
            if failed > 0:
                add_field("failed_students", failed, "count")
            if grade_count > 0:
                add_field("average_grade", round(sum_grades/grade_count, 2), "grade")
            if total_students > 0 and admitted > 0:
                add_field("success_rate", round((admitted/total_students)*100, 2), "%")

            return {
                "status": "success",
                "methods": ["Excel Parser"],
                "total_pages": len(excel.sheet_names),
                "raw_pages": raw_pages,
                "extracted_tables": extracted_tables,
                "extracted_fields": extracted_fields
            }
                
        except Exception as e:
            return {
                "status": f"error: {str(e)}",
                "methods": ["Excel Parser"],
                "total_pages": 0,
                "raw_pages": [],
                "extracted_tables": [],
                "extracted_fields": []
            }
