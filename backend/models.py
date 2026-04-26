from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SQLEnum, ForeignKey
from backend.database import Base
from datetime import datetime
import enum


class InstitutionTypeEnum(str, enum.Enum):
    UNIVERSITY = "UNIVERSITY"
    FACULTY = "FACULTY"
    INSTITUTE = "INSTITUTE"
    SCHOOL = "SCHOOL"


class RoleEnum(str, enum.Enum):
    PRESIDENT = "PRESIDENT"
    SECRETARY_GENERAL = "SECRETARY_GENERAL"
    FACULTY_ENSTAB = "FACULTY_ENSTAB"   # Legacy — traité comme FACULTY_ADMIN
    FACULTY_ADMIN = "FACULTY_ADMIN"     # Admin d'une institution spécifique
    UCAR_ADMIN = "UCAR_ADMIN"           # Vue globale toutes institutions


class RequestTypeEnum(str, enum.Enum):
    PUBLIC_MARKET = "PUBLIC_MARKET"
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    EVENT_EXPENSE = "EVENT_EXPENSE"
    LAB_FUNDING = "LAB_FUNDING"
    OTHER_EXPENSE = "OTHER_EXPENSE"


class RequestStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Institution(Base):
    """Hiérarchie des institutions : UCAR (root) → facultés/instituts (enfants)."""
    __tablename__ = "institutions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    code = Column(String)                # Ex: "ENSTAB", "FSEGT"
    type = Column(SQLEnum(InstitutionTypeEnum), default=InstitutionTypeEnum.FACULTY)
    parent_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    address = Column(String, nullable=True)
    description = Column(String, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    fullName = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    passwordHash = Column(String)
    role = Column(SQLEnum(RoleEnum))
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FinancialRequest(Base):
    __tablename__ = "financial_requests"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    type = Column(SQLEnum(RequestTypeEnum))
    amount = Column(Float)
    currency = Column(String, default="TND")
    department = Column(String)
    requestedBy = Column(String)
    status = Column(SQLEnum(RequestStatusEnum), default=RequestStatusEnum.PENDING)
    decisionBy = Column(String, nullable=True)
    decisionNote = Column(String, nullable=True)
    decisionDate = Column(DateTime, nullable=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OCRDocument(Base):
    __tablename__ = "ocr_documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    original_size_kb = Column(Float)
    total_pages = Column(Integer, default=0)
    extraction_method = Column(String, default="Unknown")
    document_type = Column(String, default="generic")
    status = Column(String, default="success")
    json_output_path = Column(String)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    error_message = Column(String, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)


class Lab(Base):
    __tablename__ = "labs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    code = Column(String)
    faculty = Column(String, default="ENSTAB")    # Legacy — gardé pour compat
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    director = Column(String, nullable=True)
    nb_etudiants = Column(Integer, default=0)
    nb_enseignants = Column(Integer, default=0)
    financement_total = Column(Float, default=0.0)
    financement_alloue = Column(Float, default=0.0)
    projets_actifs = Column(Integer, default=0)
    publications = Column(Integer, default=0)
    description = Column(String, nullable=True)
    domaines = Column(String, nullable=True)      # JSON string
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
