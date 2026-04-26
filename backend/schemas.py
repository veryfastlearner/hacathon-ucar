from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    fullName: str
    email: str
    role: str
    institution_id: Optional[int] = None

    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    token: str
    user: UserResponse

class FinancialRequestResponse(BaseModel):
    id: int
    title: str
    description: str
    type: str
    amount: float
    currency: str
    department: str
    requestedBy: str
    status: str
    decisionBy: Optional[str] = None
    decisionNote: Optional[str] = None
    decisionDate: Optional[datetime] = None
    institution_id: Optional[int] = None
    createdAt: datetime

    class Config:
        from_attributes = True

class DecisionPayload(BaseModel):
    decisionNote: Optional[str] = None
    userId: int


# ── OCR Schemas ─────────────────────────────────────────────────────────────

class OCRDocumentResponse(BaseModel):
    id: int
    filename: str
    original_size_kb: float
    total_pages: int
    extraction_method: str
    document_type: str
    status: str
    json_output_path: str
    uploaded_by: Optional[int] = None
    error_message: Optional[str] = None
    createdAt: datetime

    class Config:
        from_attributes = True
