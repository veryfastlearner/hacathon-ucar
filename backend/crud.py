from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from backend.models import User, FinancialRequest, RoleEnum, RequestStatusEnum, Institution, Lab
import hashlib


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ── USERS ─────────────────────────────────────────────────────────────────────

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


# ── INSTITUTIONS ──────────────────────────────────────────────────────────────

def get_institutions(db: Session, parent_id: int = None):
    """Retourne toutes les institutions, ou seulement les enfants d'un parent."""
    q = db.query(Institution)
    if parent_id is not None:
        q = q.filter(Institution.parent_id == parent_id)
    return q.order_by(Institution.name).all()


def get_institution(db: Session, institution_id: int):
    return db.query(Institution).filter(Institution.id == institution_id).first()


def get_institution_by_code(db: Session, code: str):
    return db.query(Institution).filter(Institution.code == code).first()


def get_institution_stats(db: Session, institution_id: int = None) -> dict:
    """Retourne les statistiques agrégées des labs d'une institution (ou globales)."""
    q = db.query(
        func.count(Lab.id).label("total_labs"),
        func.coalesce(func.sum(Lab.nb_etudiants), 0).label("total_etudiants"),
        func.coalesce(func.sum(Lab.nb_enseignants), 0).label("total_enseignants"),
        func.coalesce(func.sum(Lab.financement_total), 0).label("financement_total"),
        func.coalesce(func.sum(Lab.financement_alloue), 0).label("financement_alloue"),
        func.coalesce(func.sum(Lab.projets_actifs), 0).label("projets_actifs"),
        func.coalesce(func.sum(Lab.publications), 0).label("publications"),
    )
    if institution_id is not None:
        q = q.filter(Lab.institution_id == institution_id)
    row = q.first()
    return {
        "total_labs": row.total_labs or 0,
        "total_etudiants": int(row.total_etudiants or 0),
        "total_enseignants": int(row.total_enseignants or 0),
        "financement_total": float(row.financement_total or 0),
        "financement_alloue": float(row.financement_alloue or 0),
        "projets_actifs": int(row.projets_actifs or 0),
        "publications": int(row.publications or 0),
    }


def get_institutions_with_stats(db: Session, parent_id: int = None) -> list:
    """Retourne chaque institution avec ses stats agrégées."""
    institutions = get_institutions(db, parent_id=parent_id)
    result = []
    for inst in institutions:
        stats = get_institution_stats(db, institution_id=inst.id)
        result.append({
            "id": inst.id,
            "name": inst.name,
            "code": inst.code,
            "type": inst.type.value if inst.type else None,
            "parent_id": inst.parent_id,
            "description": inst.description,
            **stats,
            "createdAt": inst.createdAt.isoformat() if inst.createdAt else None,
        })
    return result


# ── FINANCIAL REQUESTS ────────────────────────────────────────────────────────

def get_financial_requests(db: Session, institution_id: int = None):
    """Retourne les demandes financières, filtrées par institution si précisé."""
    q = db.query(FinancialRequest).order_by(FinancialRequest.createdAt.desc())
    if institution_id is not None:
        q = q.filter(FinancialRequest.institution_id == institution_id)
    return q.all()


def get_financial_request(db: Session, req_id: int):
    return db.query(FinancialRequest).filter(FinancialRequest.id == req_id).first()


def update_request_status(db: Session, req: FinancialRequest, status: RequestStatusEnum, user: User, note: str):
    req.status = status
    req.decisionBy = user.fullName
    req.decisionNote = note
    req.decisionDate = datetime.utcnow()
    db.commit()
    db.refresh(req)
    return req


def create_financial_request_from_ocr(
    db: Session, title: str, amount: float, requestedBy: str,
    department: str = "Inconnu", description: str = None,
    request_type: str = None, institution_id: int = None
):
    from backend.models import RequestTypeEnum
    final_type = RequestTypeEnum.OTHER_EXPENSE
    if request_type:
        try:
            final_type = RequestTypeEnum(request_type.upper())
        except ValueError:
            rt_upper = request_type.upper()
            if "MARCHE" in rt_upper or "PUBLIC" in rt_upper: final_type = RequestTypeEnum.PUBLIC_MARKET
            elif "ACHAT" in rt_upper or "PURCHASE" in rt_upper: final_type = RequestTypeEnum.PURCHASE
            elif "VENTE" in rt_upper or "SALE" in rt_upper: final_type = RequestTypeEnum.SALE
            elif "CONFERENCE" in rt_upper or "EVENT" in rt_upper: final_type = RequestTypeEnum.EVENT_EXPENSE
            elif "LABO" in rt_upper or "RECHERCHE" in rt_upper: final_type = RequestTypeEnum.LAB_FUNDING

    req = FinancialRequest(
        title=title,
        description=description or "Cree automatiquement via extraction OCR",
        type=final_type,
        amount=amount,
        currency="TND",
        department=department,
        requestedBy=requestedBy,
        status=RequestStatusEnum.PENDING,
        institution_id=institution_id
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


# ── OCR ───────────────────────────────────────────────────────────────────────

def create_ocr_document(
    db: Session, filename: str, original_size_kb: float,
    total_pages: int, extraction_method: str, document_type: str,
    status: str, json_output_path: str,
    uploaded_by: int = None, error_message: str = None,
    institution_id: int = None
):
    from backend.models import OCRDocument
    doc = OCRDocument(
        filename=filename, original_size_kb=original_size_kb,
        total_pages=total_pages, extraction_method=extraction_method,
        document_type=document_type, status=status,
        json_output_path=json_output_path, uploaded_by=uploaded_by,
        error_message=error_message, institution_id=institution_id
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_ocr_documents(db: Session, institution_id: int = None):
    from backend.models import OCRDocument
    q = db.query(OCRDocument).order_by(OCRDocument.createdAt.desc())
    if institution_id is not None:
        q = q.filter(OCRDocument.institution_id == institution_id)
    return q.all()


def get_ocr_document(db: Session, doc_id: int):
    from backend.models import OCRDocument
    return db.query(OCRDocument).filter(OCRDocument.id == doc_id).first()


# ── SEED ──────────────────────────────────────────────────────────────────────

def seed_db_if_empty(db: Session):
    if db.query(User).first():
        return

    from backend.models import InstitutionTypeEnum, RequestTypeEnum

    # ── Institutions ─────────────────────────────────────────────────────────
    ucar = Institution(
        name="Université de Carthage (UCAR)", code="UCAR",
        type=InstitutionTypeEnum.UNIVERSITY, parent_id=None,
        description="Université publique tunisienne — institution mère"
    )
    db.add(ucar)
    db.flush()

    institutions_data = [
        dict(name="École Nationale des Sciences Appliquées et de Technologie de Bizerte", code="ENSTAB",
             type=InstitutionTypeEnum.SCHOOL,
             description="École d'ingénieurs en sciences et technologies"),
        dict(name="Faculté des Sciences Économiques et de Gestion de Tunis", code="FSEGT",
             type=InstitutionTypeEnum.FACULTY,
             description="Faculté de sciences économiques, gestion et finance"),
        dict(name="Institut Préparatoire aux Études d'Ingénieurs de Sfax", code="IPEIS",
             type=InstitutionTypeEnum.INSTITUTE,
             description="Classes préparatoires aux grandes écoles d'ingénieurs"),
        dict(name="Institut Supérieur de Gestion de Tunis", code="ISG",
             type=InstitutionTypeEnum.INSTITUTE,
             description="Institut de formation en gestion, management et commerce"),
        dict(name="Faculté des Sciences Juridiques, Politiques et Sociales", code="FSJPS",
             type=InstitutionTypeEnum.FACULTY,
             description="Droit, sciences politiques et sociales"),
        dict(name="Institut Préparatoire aux Études d'Ingénieurs de Tunis", code="IPEIT",
             type=InstitutionTypeEnum.INSTITUTE,
             description="Classes préparatoires aux grandes écoles d'ingénieurs - Tunis"),
    ]

    inst_map = {}
    for d in institutions_data:
        inst = Institution(**d, parent_id=ucar.id)
        db.add(inst)
        db.flush()
        inst_map[d["code"]] = inst

    # ── Utilisateurs ─────────────────────────────────────────────────────────
    users = [
        User(fullName="M. le Président", email="president@ucar.tn",
             passwordHash=hash_password("admin123"), role=RoleEnum.PRESIDENT,
             institution_id=ucar.id),
        User(fullName="Secrétaire Général", email="sg@ucar.tn",
             passwordHash=hash_password("admin123"), role=RoleEnum.SECRETARY_GENERAL,
             institution_id=ucar.id),
        User(fullName="Admin UCAR", email="ucar@ucar.tn",
             passwordHash=hash_password("admin123"), role=RoleEnum.UCAR_ADMIN,
             institution_id=ucar.id),
        User(fullName="Direction ENSTAB", email="enstab@ucar.tn",
             passwordHash=hash_password("admin123"), role=RoleEnum.FACULTY_ADMIN,
             institution_id=inst_map["ENSTAB"].id),
        User(fullName="Direction FSEGT", email="fsegt@ucar.tn",
             passwordHash=hash_password("admin123"), role=RoleEnum.FACULTY_ADMIN,
             institution_id=inst_map["FSEGT"].id),
        User(fullName="Direction IPEIS", email="ipeis@ucar.tn",
             passwordHash=hash_password("admin123"), role=RoleEnum.FACULTY_ADMIN,
             institution_id=inst_map["IPEIS"].id),
        User(fullName="Direction ISG", email="isg@ucar.tn",
             passwordHash=hash_password("admin123"), role=RoleEnum.FACULTY_ADMIN,
             institution_id=inst_map["ISG"].id),
    ]
    db.add_all(users)
    db.flush()

    # ── Demandes financières ──────────────────────────────────────────────────
    sample_requests = [
        FinancialRequest(title="Achat equipement laboratoire IA", type=RequestTypeEnum.LAB_FUNDING,
                         amount=85000.0, currency="TND", department="ENSTAB - Genie Informatique",
                         requestedBy="Dr. Amine Ben Salah", status=RequestStatusEnum.PENDING,
                         description="Serveurs GPU pour le laboratoire de recherche en IA",
                         institution_id=inst_map["ENSTAB"].id),
        FinancialRequest(title="Organisation Conference Internationale", type=RequestTypeEnum.EVENT_EXPENSE,
                         amount=42000.0, currency="TND", department="ENSTAB - Genie Energetique",
                         requestedBy="Pr. Fatma Khelifi", status=RequestStatusEnum.PENDING,
                         description="5eme conference internationale sur les energies renouvelables",
                         institution_id=inst_map["ENSTAB"].id),
        FinancialRequest(title="Marche public - Mobilier bibliotheque", type=RequestTypeEnum.PUBLIC_MARKET,
                         amount=120000.0, currency="TND", department="FSEGT",
                         requestedBy="M. Karim Bouaziz", status=RequestStatusEnum.PENDING,
                         description="Renouvellement du mobilier de la bibliotheque centrale",
                         institution_id=inst_map["FSEGT"].id),
        FinancialRequest(title="Achat licences logiciels", type=RequestTypeEnum.PURCHASE,
                         amount=28500.0, currency="TND", department="ISG Tunis",
                         requestedBy="Mme. Sonia Trabelsi", status=RequestStatusEnum.PENDING,
                         description="Licences MATLAB et SPSS pour les travaux pratiques",
                         institution_id=inst_map["ISG"].id),
        FinancialRequest(title="Renovation salle de cours B12", type=RequestTypeEnum.OTHER_EXPENSE,
                         amount=55000.0, currency="TND", department="FSJPS",
                         requestedBy="M. Nabil Chaabane", status=RequestStatusEnum.APPROVED,
                         description="Travaux de renovation et installation materiel multimedia",
                         decisionBy="Secretaire General", decisionNote="Approuve - Budget Q1 disponible",
                         institution_id=inst_map["FSJPS"].id),
        FinancialRequest(title="Vente ancien materiel informatique", type=RequestTypeEnum.SALE,
                         amount=15000.0, currency="TND", department="IPEIT",
                         requestedBy="Mme. Rim Gharbi", status=RequestStatusEnum.REJECTED,
                         description="Cession de 50 ordinateurs obsoletes",
                         decisionBy="Secretaire General", decisionNote="Rejete - Procedure de cession incomplete",
                         institution_id=inst_map["IPEIT"].id if "IPEIT" in inst_map else None),
    ]
    db.add_all(sample_requests)

    # ── Labs ENSTAB ───────────────────────────────────────────────────────────
    enstab_id = inst_map["ENSTAB"].id
    enstab_labs = [
        Lab(name="Laboratoire de Genie Informatique et Systemes", code="LGIS",
            faculty="ENSTAB", institution_id=enstab_id,
            director="Pr. Mohamed Ali Hadj Amor", nb_etudiants=52, nb_enseignants=9,
            financement_total=180000.0, financement_alloue=130000.0, projets_actifs=6, publications=28,
            description="Recherche en IA, systemes embarques et reseaux intelligents.",
            domaines='["Intelligence Artificielle", "Systemes embarques", "Reseaux", "IoT"]'),
        Lab(name="Laboratoire de Genie Electrique et Energies Renouvelables", code="LGEER",
            faculty="ENSTAB", institution_id=enstab_id,
            director="Pr. Faouzi Ben Amara", nb_etudiants=38, nb_enseignants=7,
            financement_total=210000.0, financement_alloue=155000.0, projets_actifs=4, publications=35,
            description="Recherche sur les systemes electriques, energie solaire et eolienne.",
            domaines='["Energie Renouvelable", "Electrotechnique", "Smart Grid", "Photovoltaique"]'),
        Lab(name="Laboratoire de Genie Mecanique et Materiaux", code="LGMM",
            faculty="ENSTAB", institution_id=enstab_id,
            director="Dr. Sonia Mzali", nb_etudiants=44, nb_enseignants=8,
            financement_total=150000.0, financement_alloue=95000.0, projets_actifs=5, publications=19,
            description="Simulation mecanique, materiaux composites et fabrication additive.",
            domaines='["Mecanique des fluides", "Materiaux Composites", "Impression 3D", "CAO"]'),
        Lab(name="Laboratoire de Physique Appliquee et Optoelectronique", code="LPAO",
            faculty="ENSTAB", institution_id=enstab_id,
            director="Pr. Hatem Elloumi", nb_etudiants=30, nb_enseignants=6,
            financement_total=120000.0, financement_alloue=80000.0, projets_actifs=3, publications=22,
            description="Recherche en physique des semi-conducteurs et photonique.",
            domaines='["Optoelectronique", "Semi-conducteurs", "Photonique", "Nanotechnologie"]'),
        Lab(name="Laboratoire Genie Chimique et Procedes", code="LGCP",
            faculty="ENSTAB", institution_id=enstab_id,
            director="Dr. Rim Gharbi", nb_etudiants=27, nb_enseignants=5,
            financement_total=95000.0, financement_alloue=60000.0, projets_actifs=2, publications=14,
            description="Genie des procedes, catalyse et traitement des eaux.",
            domaines='["Genie chimique", "Traitement des eaux", "Catalyse", "Environnement"]'),
        Lab(name="Laboratoire Mathematiques et Modelisation", code="LMM",
            faculty="ENSTAB", institution_id=enstab_id,
            director="Pr. Kamel Zouari", nb_etudiants=22, nb_enseignants=5,
            financement_total=75000.0, financement_alloue=45000.0, projets_actifs=2, publications=17,
            description="Modelisation mathematique, optimisation et statistiques appliquees.",
            domaines='["Mathematiques appliquees", "Optimisation", "Statistiques", "Modelisation"]'),
    ]
    db.add_all(enstab_labs)

    # ── Labs FSEGT ────────────────────────────────────────────────────────────
    fsegt_id = inst_map["FSEGT"].id
    fsegt_labs = [
        Lab(name="Laboratoire d'Economie et Finance Appliquee", code="LEFA",
            faculty="FSEGT", institution_id=fsegt_id,
            director="Pr. Habib Trabelsi", nb_etudiants=65, nb_enseignants=12,
            financement_total=95000.0, financement_alloue=70000.0, projets_actifs=4, publications=31,
            description="Recherche en economie appliquee, finance et econometrie.",
            domaines='["Econometrie", "Finance", "Marches financiers", "Macroeconomie"]'),
        Lab(name="Laboratoire de Management et Gouvernance", code="LMG",
            faculty="FSEGT", institution_id=fsegt_id,
            director="Dr. Leila Mnif", nb_etudiants=48, nb_enseignants=8,
            financement_total=75000.0, financement_alloue=55000.0, projets_actifs=3, publications=18,
            description="Recherche sur le management strategique et la gouvernance d'entreprise.",
            domaines='["Management", "Gouvernance", "GRH", "Entrepreneuriat"]'),
    ]
    db.add_all(fsegt_labs)

    # ── Labs ISG ──────────────────────────────────────────────────────────────
    isg_id = inst_map["ISG"].id
    isg_labs = [
        Lab(name="Laboratoire de Systemes d'Information et Technologies", code="LSIT",
            faculty="ISG", institution_id=isg_id,
            director="Pr. Karim Missaoui", nb_etudiants=55, nb_enseignants=9,
            financement_total=110000.0, financement_alloue=75000.0, projets_actifs=5, publications=22,
            description="Recherche en systemes d'information, big data et intelligence d'affaires.",
            domaines='["Systemes d\'information", "Big Data", "BI", "ERP"]'),
        Lab(name="Laboratoire de Comptabilite et Audit", code="LCA",
            faculty="ISG", institution_id=isg_id,
            director="Dr. Nadia Ben Romdhane", nb_etudiants=40, nb_enseignants=7,
            financement_total=60000.0, financement_alloue=42000.0, projets_actifs=2, publications=12,
            description="Normes comptables, audit financier et controle de gestion.",
            domaines='["Comptabilite", "Audit", "Controle de gestion", "IFRS"]'),
    ]
    db.add_all(isg_labs)

    db.commit()
    print("Seed complete: institutions, users, labs, financial requests created.")
