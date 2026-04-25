from pydantic import BaseModel, Field
from typing import Optional, Any, List, Dict
from datetime import datetime

class DocumentLog(BaseModel):
    document_id: str
    source_file: str
    document_type: str
    total_pages: int
    extraction_status: str
    extraction_methods_used: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class RawPageText(BaseModel):
    document_id: str
    source_file: str
    page_number: int
    raw_text: str

class ExtractedTable(BaseModel):
    document_id: str
    source_file: str
    page_number: int
    table_index: int
    row_index: int
    column_name: str
    cell_value: Any
    source_bbox: Optional[str] = None
    extraction_method: str
    confidence_score: float

class ExtractedField(BaseModel):
    document_id: str
    source_file: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    field_name: str
    field_value: Any
    unit: Optional[str] = None
    period: Optional[str] = None
    academic_year: Optional[str] = None
    source_bbox: Optional[str] = None
    extraction_method: str
    confidence_score: float
    validation_status: str

class KPISchema(BaseModel):
    institution_id: str
    institution_name: str
    document_id: str
    document_type: str
    domain: str
    kpi_name: str
    kpi_label: str
    kpi_value: Any
    unit: Optional[str] = None
    period: Optional[str] = None
    academic_year: Optional[str] = None
    source_file: str
    source_page: Optional[int] = None
    source_bbox: Optional[str] = None
    extraction_method: str
    confidence_score: float
    validation_status: str
    fallback_demo_extraction: bool = False
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ValidationQueue(BaseModel):
    institution_id: str
    institution_name: str
    document_id: str
    document_type: str
    domain: str
    kpi_name: str
    kpi_label: str
    kpi_value: Any
    unit: Optional[str] = None
    period: Optional[str] = None
    academic_year: Optional[str] = None
    source_file: str
    source_page: Optional[int] = None
    source_bbox: Optional[str] = None
    extraction_method: str
    confidence_score: float
    validation_status: str
    fallback_demo_extraction: bool = False
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    validation_reason: str

class ExtractionResult(BaseModel):
    document_id: str
    document_type: str
    source_file: str
    total_pages: int = 1
    extraction_status: str = "success"
    extraction_methods_used: List[str] = []
    
    raw_pages: List[RawPageText] = []
    extracted_tables: List[ExtractedTable] = []
    extracted_fields: List[ExtractedField] = []
    kpis: List[KPISchema] = []
    validation_queue: List[ValidationQueue] = []

