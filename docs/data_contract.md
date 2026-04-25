# Data Contract 

This document defines the schema for `dashboard_ready_data.csv`. The Track 1 module guarantees this exact format.

| Column | Description | Type |
|--------|-------------|------|
| `institution_id` | Mapped normalized UCAR ID. | `string` |
| `institution_name` | Original institution string. | `string` |
| `document_id` | Identifier of source document. | `string` |
| `document_type` | Detected type (e.g., pdf_timetable). | `string` |
| `domain` | The functional domain (Académique, Finance, Infrastructure). | `string` |
| `kpi_name` | System name of the KPI (e.g., success_rate). | `string` |
| `kpi_label` | Human-readable label. | `string` |
| `kpi_value` | The actual numeric or boolean extracted value. | `mixed` |
| `unit` | Unit context (count, %, points, etc). | `string` |
| `period` | Period if applicable. | `string` |
| `academic_year` | Extracted academic year. | `string` |
| `source_file` | Name of raw file used. | `string` |
| `source_page` | PyMuPDF page number (if PDF). | `int` |
| `source_bbox` | PyMuPDF coordinates (if PDF bounding box used). | `string` |
| `extraction_method` | Method employed (PyMuPDF Native Text, Excel Parser, etc). | `string` |
| `confidence_score` | 0.0 to 1.0 numeric estimation. | `float` |
| `validation_status` | `Auto Validated`, `Needs Review`, `Manual Review Required`. | `string` |
| `fallback_demo_extraction` | `True` if it's a mockup for demo without strong confidence. | `boolean` |
| `created_at` | Process ISO timestamp. | `string` |
