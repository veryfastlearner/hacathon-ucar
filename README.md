# UCAR DataHub - Track 1: Document-to-KPI Engine

## Overview
This module transforms pre-existing academic, HR, and financial university documents (Excel, textual PDFs, visual PDFs) into structured key performance indicators (KPIs). The extracted data is output to a standardized `dashboard_ready_data.csv` for use by the analytics dashboard team.

## Architecture
We use a **PyMuPDF-first** approach rather than falling back immediately to OCR:
1. **PyMuPDF Engine**: Parses native text blocks, bounding boxes, and detects page strategy (e.g., text, layout, form).
2. **Regex/Rule-based Extractors**: Find specific KPIs within extracted blocks.
3. **Data Normalizer & Validator**: Cleans outputs and assigns a confidence score. High score (>0.90) gets "Auto Validated", medium score gets "Needs Review".

### Why PyMuPDF first?
OCR (like Tesseract) is error-prone, slow, and loses native PDF document structure. By leveraging PyMuPDF, we can exactly reconstruct page bounding boxes, tables, and paragraphs where native text exists. We only fallback to OCR or heuristic demo modes when native text is stripped or absent.

## Installation
```bash
python -m venv venv
source venv/Scripts/activate # Windows
pip install -r requirements.txt
```

## Running the Pipeline
Place your raw files in `data/raw/`:
- `01_academique_resultats_fsjpst.xlsx`
- `02_emploi_du_temps_1TA_S2.pdf`
- `03_finance_tdrs_smartgreenecos_ucar.pdf`

Run the process:
```bash
python run_process_all.py
```

Check `data/exports/dashboard_ready_data.csv` for the final structured schema.

## Starting the API
```bash
cd backend
uvicorn app.main:app --reload
```
Access the swagger docs at `http://127.0.0.1:8000/docs`

## Limitations
- In case timetable PDFs are fully rasterized without native block detection, a mock bounding box fallback is actively implemented for demonstration, marked properly as `fallback_demo_extraction`.
