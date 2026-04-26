from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend import database

router = APIRouter(prefix="/labs", tags=["labs"])


def lab_to_dict(lab) -> dict:
    import json as _json
    domaines = []
    try:
        if lab.domaines:
            domaines = _json.loads(lab.domaines)
    except Exception:
        pass
    return {
        "id": lab.id,
        "name": lab.name,
        "code": lab.code,
        "faculty": lab.faculty,
        "institution_id": lab.institution_id,
        "director": lab.director,
        "nb_etudiants": lab.nb_etudiants,
        "nb_enseignants": lab.nb_enseignants,
        "financement_total": lab.financement_total,
        "financement_alloue": lab.financement_alloue,
        "taux_utilisation": round((lab.financement_alloue / lab.financement_total * 100), 1) if lab.financement_total else 0,
        "projets_actifs": lab.projets_actifs,
        "publications": lab.publications,
        "description": lab.description,
        "domaines": domaines,
        "createdAt": lab.createdAt.isoformat() if lab.createdAt else None,
    }


def detect_lab_from_text(text: str, db: Session, institution_id: int = None):
    """
    Détecte le lab le plus probable depuis un texte.
    Si institution_id est fourni, la recherche est limitée aux labs de cette institution.
    """
    import json as _json
    from backend.models import Lab

    if not text:
        return None

    text_lower = text.lower()
    q = db.query(Lab)
    if institution_id:
        q = q.filter(Lab.institution_id == institution_id)
    labs = q.all()

    best_lab, best_score = None, 0

    for lab in labs:
        score = 0
        if lab.code and lab.code.lower() in text_lower:
            score += 10
        if lab.name:
            words = [w for w in lab.name.lower().split() if len(w) > 4]
            score += sum(2 for w in words if w in text_lower)
        try:
            for d in _json.loads(lab.domaines or "[]"):
                for word in d.lower().split():
                    if len(word) > 4 and word in text_lower:
                        score += 1
        except Exception:
            pass
        if lab.director:
            last_name = lab.director.split()[-1].lower() if lab.director.split() else ""
            if last_name and len(last_name) > 3 and last_name in text_lower:
                score += 5

        print(f"[LAB-DETECT] {lab.code} (inst:{lab.institution_id}): score={score}")
        if score > best_score:
            best_score = score
            best_lab = lab

    return best_lab if best_score >= 3 else None


@router.get("/", summary="Liste les labs (filtrés par institution_id si fourni)")
def get_labs(institution_id: int = None, db: Session = Depends(database.get_db)):
    from backend.models import Lab
    q = db.query(Lab)
    if institution_id is not None:
        q = q.filter(Lab.institution_id == institution_id)
    labs = q.order_by(Lab.name).all()
    return [lab_to_dict(l) for l in labs]


@router.get("/enstab", summary="Labs ENSTAB (legacy)")
def get_enstab_labs(db: Session = Depends(database.get_db)):
    from backend.models import Lab
    labs = db.query(Lab).filter(Lab.faculty == "ENSTAB").order_by(Lab.name).all()
    return [lab_to_dict(l) for l in labs]


@router.get("/{lab_id}", summary="Detail d'un lab")
def get_lab_detail(lab_id: int, db: Session = Depends(database.get_db)):
    from backend.models import Lab
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab non trouve")
    return lab_to_dict(lab)


@router.put("/{lab_id}/funding", summary="Mise a jour du financement d'un lab")
def update_lab_funding(lab_id: int, payload: dict, db: Session = Depends(database.get_db)):
    from backend.models import Lab
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab non trouve")
    amount = float(payload.get("amount", 0))
    if payload.get("add", False):
        lab.financement_alloue = (lab.financement_alloue or 0) + amount
    else:
        lab.financement_alloue = amount
    db.commit()
    db.refresh(lab)
    return lab_to_dict(lab)
