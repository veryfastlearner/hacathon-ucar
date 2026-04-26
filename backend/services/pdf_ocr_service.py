import os
import json
import re
from datetime import datetime
from typing import Optional


def extract_pdf_to_json(file_path: str, document_type: str = "generic") -> dict:
    """
    Extrait le contenu d'un PDF (texte + tables) via PyMuPDF.
    Retourne un dict JSON structuré prêt à être sauvegardé.

    Args:
        file_path: Chemin absolu vers le fichier PDF
        document_type: Type de document ("generic", "finance", "academic", etc.)

    Returns:
        dict avec metadata, raw_pages, extracted_tables, extracted_fields, summary
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return {
            "metadata": {"filename": os.path.basename(file_path), "error": "PyMuPDF non installé"},
            "status": "error",
            "summary": {}
        }

    filename = os.path.basename(file_path)
    doc = fitz.open(file_path)

    raw_pages = []
    extracted_tables = []
    methods_used = set()
    total_text_chars = 0
    total_tables_found = 0

    for i in range(len(doc)):
        page = doc[i]
        page_num = i + 1

        # --- Extraction texte natif ---
        text = page.get_text("text")
        confidence = 0.95
        method = "PyMuPDF Native Text"

        if len(text.strip()) < 20:
            # Fallback OCR si la page est imagée (scannée)
            try:
                text = page.get_textpage_ocr().extractText()
                method = "PyMuPDF OCR Fallback"
                confidence = 0.70
            except Exception:
                text = ""
                method = "No Text Detected"
                confidence = 0.0

        methods_used.add(method)
        total_text_chars += len(text)

        raw_pages.append({
            "page": page_num,
            "text": text.strip(),
            "char_count": len(text),
            "confidence": confidence,
            "method": method
        })

        # --- Extraction tables natives ---
        try:
            tables = page.find_tables()
            if tables and len(tables.tables) > 0:
                methods_used.add("PyMuPDF Table Extractor")
                for t_idx, tab in enumerate(tables):
                    try:
                        pandas_df = tab.to_pandas()
                        if pandas_df is None or pandas_df.empty:
                            continue
                        total_tables_found += 1
                        bbox = tab.bbox
                        rows_data = []
                        for row_idx, row in pandas_df.iterrows():
                            row_dict = {}
                            for col_name, cell_val in row.items():
                                if cell_val is not None and str(cell_val).strip() != "":
                                    row_dict[str(col_name)] = str(cell_val).strip()
                            if row_dict:
                                rows_data.append(row_dict)

                        if rows_data:
                            extracted_tables.append({
                                "page": page_num,
                                "table_index": t_idx,
                                "bbox": f"{bbox[0]:.1f},{bbox[1]:.1f},{bbox[2]:.1f},{bbox[3]:.1f}",
                                "extraction_method": "PyMuPDF Table Extractor",
                                "confidence": 0.95,
                                "rows": rows_data
                            })
                    except Exception:
                        continue
            else:
                # Fallback : blocs texte comme pseudo-table
                blocks = page.get_text("blocks")
                if blocks:
                    methods_used.add("PyMuPDF Block Heuristics")
                    block_rows = []
                    for b in blocks:
                        x0, y0, x1, y1, btext, bnum, btype = b
                        if str(btext).strip() and btype == 0:
                            block_rows.append({
                                "BlockText": btext.replace('\n', ' ').strip(),
                                "BBox": f"{x0:.1f},{y0:.1f},{x1:.1f},{y1:.1f}"
                            })
                    if block_rows:
                        extracted_tables.append({
                            "page": page_num,
                            "table_index": 99,
                            "extraction_method": "PyMuPDF Block Heuristics",
                            "confidence": 0.85,
                            "rows": block_rows
                        })
        except Exception:
            pass

    doc.close()

    # --- Extraction de champs structurés par regex (KPIs courants) ---
    full_text = "\n".join(p["text"] for p in raw_pages)
    extracted_fields = _extract_common_fields(full_text, filename)

    avg_confidence = (
        sum(p["confidence"] for p in raw_pages) / len(raw_pages)
        if raw_pages else 0.0
    )

    return {
        "metadata": {
            "filename": filename,
            "total_pages": len(raw_pages),
            "extraction_methods": list(methods_used),
            "document_type": document_type,
            "processed_at": datetime.utcnow().isoformat() + "Z",
        },
        "summary": {
            "total_text_chars": total_text_chars,
            "total_tables_found": total_tables_found,
            "total_fields_extracted": len(extracted_fields),
            "avg_confidence": round(avg_confidence, 2),
            "status": "success"
        },
        "raw_pages": raw_pages,
        "extracted_tables": extracted_tables,
        "extracted_fields": extracted_fields
    }


def _extract_common_fields(full_text: str, filename: str) -> list:
    """
    Détection regex de KPIs courants dans le texte extrait.
    Couvre : budgets, étudiants, laboratoires, enseignants, taux, etc.
    """
    fields = []

    patterns = [
        # Finance
        (r'[Bb]udget[^\d]*?([\d\s]+(?:[,\.]\d+)?)\s*(?:TND|DT|MDT|millions?)?',
         "budget_total", "TND"),
        (r'[Mm]ontant[^\d]*?([\d\s]+(?:[,\.]\d+)?)\s*(?:TND|DT)?',
         "montant", "TND"),
        (r'[Cc]o[uû]t[^\d]*?([\d\s]+(?:[,\.]\d+)?)\s*(?:TND|DT)?',
         "cout", "TND"),
        # Académique
        (r'[Nn]ombre\s+d[\'e]étudiants?[^\d]*?(\d[\d\s]*)',
         "nombre_etudiants", "étudiants"),
        (r'[Tt]otal\s+étudiants?[^\d]*?(\d[\d\s]*)',
         "total_etudiants", "étudiants"),
        (r'[Nn]ombre\s+d[\'e]enseignants?[^\d]*?(\d[\d\s]*)',
         "nombre_enseignants", "enseignants"),
        (r'[Nn]ombre\s+de\s+laboratoires?[^\d]*?(\d[\d\s]*)',
         "nombre_laboratoires", "laboratoires"),
        (r'[Nn]ombre\s+de\s+publications?[^\d]*?(\d[\d\s]*)',
         "nombre_publications", "publications"),
        # Taux
        (r'[Tt]aux\s+de\s+(?:réussite|r[eé]ussite)[^\d]*?([\d,\.]+)\s*%?',
         "taux_reussite", "%"),
        (r'[Tt]aux\s+d\'?(insertion|emploi|employabilité)[^\d]*?([\d,\.]+)\s*%?',
         "taux_insertion", "%"),
        (r'[Tt]aux\s+de\s+redoublement[^\d]*?([\d,\.]+)\s*%?',
         "taux_redoublement", "%"),
        # Classement
        (r'[Cc]lassement[^\d]*?(\d+(?:\s*e|er|ème)?)',
         "classement", "rang"),
        (r'[Rr]ang[^\d]*?(\d+)',
         "rang", "rang"),
        # Score / Note
        (r'[Ss]core[^\d]*?([\d,\.]+)',
         "score", "points"),
        (r'[Nn]ote\s+(?:globale|finale|moyenne)[^\d]*?([\d,\.]+)',
         "note_globale", "points"),
    ]

    seen_fields = set()
    for pattern, field_name, unit in patterns:
        try:
            matches = re.findall(pattern, full_text)
            if matches:
                # Prendre la dernière valeur trouvée (souvent la plus pertinente)
                raw_val = matches[-1]
                if isinstance(raw_val, tuple):
                    raw_val = raw_val[-1]
                raw_val = raw_val.replace(" ", "").replace(",", ".")
                try:
                    value = float(raw_val)
                except ValueError:
                    value = raw_val

                if field_name not in seen_fields:
                    seen_fields.add(field_name)
                    fields.append({
                        "field_name": field_name,
                        "field_value": value,
                        "unit": unit,
                        "confidence": 0.80,
                        "extraction_method": "Regex Pattern Matching"
                    })
        except Exception:
            continue

    return fields


def get_primary_method(json_data: dict) -> str:
    """Retourne la méthode d'extraction principale utilisée."""
    methods = json_data.get("metadata", {}).get("extraction_methods", [])
    if not methods:
        return "Unknown"
    # Priorité : Native > OCR Fallback > Block Heuristics
    if "PyMuPDF Native Text" in methods:
        return "PyMuPDF Native Text"
    if "PyMuPDF OCR Fallback" in methods:
        return "PyMuPDF OCR Fallback"
    return methods[0]
