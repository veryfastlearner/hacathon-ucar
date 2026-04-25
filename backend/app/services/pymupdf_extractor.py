import fitz
import os
import re

class PyMuPDFExtractor:
    
    @staticmethod
    def extract_pdf(file_path: str, render_dir: str = None) -> dict:
        doc = fitz.open(file_path)
        doc_id = os.path.basename(file_path).split('.')[0].upper()[:10]
        
        raw_pages = []
        extracted_tables = []
        methods_used = set()
        
        for i in range(len(doc)):
            page = doc[i]
            page_num = i + 1
            
            # --- Text Extraction ---
            text = page.get_text("text")
            confidence = 0.95
            method = "PyMuPDF Native Text"
            
            if len(text.strip()) < 20:
                try:
                    text = page.get_textpage_ocr().extractText()
                    method = "PyMuPDF OCR Fallback"
                    confidence = 0.70
                except Exception:
                    pass
            methods_used.add(method)
            
            raw_pages.append({
                "document_id": doc_id,
                "source_file": os.path.basename(file_path),
                "page_number": page_num,
                "raw_text": text
            })
            
            # --- Table Extraction ---
            # Try native tables
            tables = page.find_tables()
            if tables and len(tables.tables) > 0:
                methods_used.add("PyMuPDF Table Extractor")
                for t_idx, tab in enumerate(tables):
                    pandas_df = tab.to_pandas()
                    if pandas_df is None or pandas_df.empty:
                        continue
                    
                    bbox = tab.bbox
                    bbox_str = f"{bbox[0]:.1f},{bbox[1]:.1f},{bbox[2]:.1f},{bbox[3]:.1f}"
                    
                    for row_idx, row in pandas_df.iterrows():
                        for col_name, cell_val in row.items():
                            if cell_val is not None and str(cell_val).strip() != "":
                                extracted_tables.append({
                                    "document_id": doc_id,
                                    "source_file": os.path.basename(file_path),
                                    "page_number": page_num,
                                    "table_index": t_idx,
                                    "row_index": row_idx,
                                    "column_name": str(col_name),
                                    "cell_value": cell_val,
                                    "source_bbox": bbox_str,
                                    "extraction_method": "PyMuPDF Table Extractor",
                                    "confidence_score": 0.95
                                })
            else:
                # Fallback purely manual table reconstruction for visual tables without native lines
                # Useful for timetable where no physical lines exist.
                blocks = page.get_text("blocks")
                if len(blocks) > 0:
                    methods_used.add("PyMuPDF Block Heuristics")
                    t_idx = 99 # artificial table index
                    for b_idx, b in enumerate(blocks):
                        x0, y0, x1, y1, btext, bnum, btype = b
                        if str(btext).strip() != "" and btype == 0:
                            extracted_tables.append({
                                "document_id": doc_id,
                                "source_file": os.path.basename(file_path),
                                "page_number": page_num,
                                "table_index": t_idx,
                                "row_index": b_idx, # using block idx as row proxy
                                "column_name": "BlockText",
                                "cell_value": btext.replace('\n', ' ').strip(),
                                "source_bbox": f"{x0:.1f},{y0:.1f},{x1:.1f},{y1:.1f}",
                                "extraction_method": "PyMuPDF Block Heuristics",
                                "confidence_score": 0.85
                            })

            if render_dir:
                os.makedirs(render_dir, exist_ok=True)
                rendered_path = os.path.join(render_dir, f"page_{page_num}.png")
                pix = page.get_pixmap(dpi=200)
                pix.save(rendered_path)

        return {
            "status": "success",
            "methods": list(methods_used),
            "total_pages": len(doc),
            "raw_pages": raw_pages,
            "extracted_tables": extracted_tables,
            "extracted_fields": []
        }

