import pandas as pd
import os
from typing import List
from app.models.schemas import ExtractionResult

class CSVExporter:
    
    @staticmethod
    def export_all(results: List[ExtractionResult], output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        
        doc_logs = []
        raw_pages = []
        extracted_tables = []
        extracted_fields = []
        kpis = []
        validation_queue = []
        
        for res in results:
            doc_logs.append({
                "document_id": res.document_id,
                "source_file": res.source_file,
                "document_type": res.document_type,
                "total_pages": res.total_pages,
                "extraction_status": res.extraction_status,
                "extraction_methods_used": ", ".join(res.extraction_methods_used),
            })
            raw_pages.extend([p.model_dump() for p in res.raw_pages])
            extracted_tables.extend([t.model_dump() for t in res.extracted_tables])
            extracted_fields.extend([f.model_dump() for f in res.extracted_fields])
            kpis.extend([k.model_dump() for k in res.kpis])
            validation_queue.extend([v.model_dump() for v in res.validation_queue])
            
        def safe_export(df_list, name, cols_required=None):
            df = pd.DataFrame(df_list)
            if cols_required:
                for c in cols_required:
                    if c not in df.columns:
                        df[c] = None
                df = df[cols_required]
            try:
                df.to_csv(os.path.join(output_dir, name), index=False)
            except PermissionError:
                print(f"\n[AVERTISSEMENT] Impossible d'écrire '{name}' car le fichier est ouvert. Veuillez le fermer dans Excel et réessayer.")
            
        # 1. documents_log.csv
        safe_export(doc_logs, "documents_log.csv")
        
        # 2. raw_pages_text.csv
        safe_export(raw_pages, "raw_pages_text.csv")
        
        # 3. extracted_tables.csv
        safe_export(extracted_tables, "extracted_tables.csv")
        
        # 4. extracted_fields.csv
        safe_export(extracted_fields, "extracted_fields.csv")
        
        # 5. extracted_kpis.csv
        safe_export(kpis, "extracted_kpis.csv")
        
        # 6. dashboard_ready_data.csv
        dr_cols = [
            "institution_id", "institution_name", "document_id", "document_type", 
            "domain", "kpi_name", "kpi_label", "kpi_value", "unit", 
            "period", "academic_year", "source_file", "source_page", 
            "source_bbox", "extraction_method", "confidence_score", 
            "validation_status", "fallback_demo_extraction", "created_at"
        ]
        # Filter kpis for dashboard ready (only those passing validation)
        dashboard_ready = [k for k in kpis if k.get("validation_status") != "Manual Review Required"]
        safe_export(dashboard_ready, "dashboard_ready_data.csv", dr_cols)
        
        # 7. validation_queue.csv
        vq_cols = dr_cols + ["validation_reason"]
        safe_export(validation_queue, "validation_queue.csv", vq_cols)
