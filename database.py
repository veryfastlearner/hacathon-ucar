import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import enum
import hashlib

# Use SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./ucar_app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class RoleEnum(str, enum.Enum):
    PRESIDENT = "PRESIDENT"
    SECRETARY_GENERAL = "SECRETARY_GENERAL"

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

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    fullName = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    passwordHash = Column(String)
    role = Column(SQLEnum(RoleEnum))
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
    requestedBy = Column(String) # usually implies another user, but string is fine based on schema
    status = Column(SQLEnum(RequestStatusEnum), default=RequestStatusEnum.PENDING)
    decisionBy = Column(String, nullable=True)
    decisionNote = Column(String, nullable=True)
    decisionDate = Column(DateTime, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def hash_password(password: str) -> str:
    # Basic hashing for demo purposes (the prompt says use password hashing)
    # Fast to setup natively without bcrypt issues on windows sometimes
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def seed_db(db):
    if db.query(User).first():
        return # DB already seeded

    # Seed Users
    president = User(
        fullName="M. le Président",
        email="president@ucar.tn",
        passwordHash=hash_password("admin123"),
        role=RoleEnum.PRESIDENT
    )
    sg = User(
        fullName="Secrétaire Général",
        email="sg@ucar.tn",
        passwordHash=hash_password("admin123"),
        role=RoleEnum.SECRETARY_GENERAL
    )
    db.add(president)
    db.add(sg)
    db.commit()

    # Seed Financial Requests
    requests = [
        FinancialRequest(
            title="Achat d'équipements informatiques pour ENSI",
            description="Acquisition de 20 serveurs pour le nouveau laboratoire AI.",
            type=RequestTypeEnum.PUBLIC_MARKET,
            amount=150000.00,
            department="ENSI",
            requestedBy="Directeur ENSI"
        ),
        FinancialRequest(
            title="Subvention Pôle de Recherche",
            description="Financement du projet de recherche sur les énergies renouvelables.",
            type=RequestTypeEnum.LAB_FUNDING,
            amount=45000.00,
            department="FSB",
            requestedBy="Chef Labo FSB"
        ),
        FinancialRequest(
            title="Cérémonie de remise des diplômes",
            description="Frais d'organisation et logistique.",
            type=RequestTypeEnum.EVENT_EXPENSE,
            amount=8500.00,
            department="ISG",
            requestedBy="Service Evénementiel"
        ),
        FinancialRequest(
            title="Renouvellement Licences Logicielles",
            description="Suite bureautique et outils de gestion pour l'administration centrale.",
            type=RequestTypeEnum.PURCHASE,
            amount=12000.00,
            department="Administration Centrale",
            requestedBy="DSI"
        )
    ]
    db.add_all(requests)
    db.commit()

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_db(db)
    db.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized and seeded.")
