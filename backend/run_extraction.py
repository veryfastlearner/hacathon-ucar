import os
import sys
import argparse
from typing import List
from app.services.document_classifier import DocumentClassifier
from app.services.excel_parser import ExcelParser
from app.services.pymupdf_extractor import PyMuPDFExtractor
from app.services.field_extractor import FieldExtractor
from app.services.kpi_generator import KPIGenerator
from app.services.validator import DataValidator
from app.services.exporter import CSVExporter
from app.models.schemas import ExtractionResult, ValidationQueue, ExtractedField, ExtractedTable, KPISchema, RawPageText

def process_file(fpath: str) -> ExtractionResult:
    fname = os.path.basename(fpath)
    doc_type = DocumentClassifier.classify_file(fpath)
    
    res = ExtractionResult(
        document_id=fname.split('.')[0].upper()[:10],
        document_type=doc_type,
        source_file=fname
    )
    
    try:
        raw_fields = {}
        raw_kpis = []
        
        if doc_type == "excel_academic_results":
            excel_res = ExcelParser.parse_academic_results(fpath)
            res.extraction_status = excel_res.get("status", "error")
            res.extraction_methods_used = excel_res.get("methods", [])
            res.total_pages = excel_res.get("total_pages", 1)
            
            # Map raw objects into schemas
            for r in excel_res.get("raw_pages", []):
                res.raw_pages.append(RawPageText(**r))
            for t in excel_res.get("extracted_tables", []):
                res.extracted_tables.append(ExtractedTable(**t))
            for f in excel_res.get("extracted_fields", []):
                res.extracted_fields.append(ExtractedField(**f))
                
            raw_kpis = KPIGenerator.generate_academic(excel_res, fname)
            
        elif doc_type.startswith("pdf_"):
            pdf_res = PyMuPDFExtractor.extract_pdf(fpath)
            res.extraction_status = pdf_res.get("status", "error")
            res.extraction_methods_used = pdf_res.get("methods", [])
            res.total_pages = pdf_res.get("total_pages", 1)
            
            for r in pdf_res.get("raw_pages", []):
                res.raw_pages.append(RawPageText(**r))
            for t in pdf_res.get("extracted_tables", []):
                res.extracted_tables.append(ExtractedTable(**t))
                
            if doc_type == "pdf_finance_admin":
                raw_fields = FieldExtractor.extract_finance_admin_fields(pdf_res)
                raw_kpis = KPIGenerator.generate_finance(raw_fields, fname)
            elif doc_type == "pdf_timetable":
                raw_fields = FieldExtractor.extract_timetable_fields(pdf_res)
                raw_kpis = KPIGenerator.generate_timetable(raw_fields, fname)
            elif doc_type == "pdf_dep_fr":
                raw_fields = FieldExtractor.extract_dep_fr_fields(pdf_res)
                raw_kpis = KPIGenerator.generate_dep_fr(raw_fields, fname)
                
            if raw_fields:
                for k, v in raw_fields.items():
                    if k not in ["confidence", "method", "institution_name", "department"]:
                        res.extracted_fields.append(ExtractedField(
                            document_id=res.document_id,
                            source_file=fname,
                            field_name=k,
                            field_value=v,
                            extraction_method=raw_fields.get("method", "Unknown"),
                            confidence_score=raw_fields.get("confidence", 0.0),
                            validation_status="Pending"
                        ))
        else:
            res.extraction_status = "Unclassified document"
            
        # Validation layer
        valid_kpis, queue_kpis = DataValidator.validate_kpis(raw_kpis)
        
        for k in valid_kpis:
            res.kpis.append(KPISchema(**k))
        for vq in queue_kpis:
            res.validation_queue.append(ValidationQueue(**vq))
            
    except Exception as e:
        res.extraction_status = f"Failed: {str(e)}"
        
    return res


def main():
    parser = argparse.ArgumentParser(description="UCAR DataHub Extraction Engine")
    parser.add_argument("--input", required=True, help="Directory containing raw PDF/Excel files")
    parser.add_argument("--output", required=True, help="Directory to save the generated CSV files")
    args = parser.parse_args()

    input_dir = args.input
    output_dir = args.output

    if not os.path.exists(input_dir):
        print(f"Error: Input directory {input_dir} does not exist.")
        sys.exit(1)

    print(f"Starting Data Extraction Pipeline...\nInput: {input_dir}\nOutput: {output_dir}\n")

    results = []
    processed = 0

    for fname in os.listdir(input_dir):
        fpath = os.path.join(input_dir, fname)
        if os.path.isfile(fpath) and not fname.startswith("."):
            print(f"Processing: {fname}")
            res = process_file(fpath)
            results.append(res)
            processed += 1

    print("\nExtraction Complete. Exporting 7 valid CSV tables...")
    CSVExporter.export_all(results, output_dir)

    print("\nSUMMARY:")
    print(f"- Documents processed: {processed}")
    total_kpis = sum(len(r.kpis) for r in results)
    total_vq = sum(len(r.validation_queue) for r in results)
    print(f"- FAQs/KPIs correctly extracted: {total_kpis}")
    print(f"- Validation queue count: {total_vq}")
    
    for r in results:
        if r.extraction_status.startswith("Failed"):
            print(f"   [ERROR] {r.source_file}: {r.extraction_status}")

if __name__ == "__main__":
    main()
