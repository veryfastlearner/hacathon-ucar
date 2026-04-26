from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend import database, crud
from backend.models import RoleEnum

router = APIRouter(prefix="/institutions", tags=["institutions"])

ALLOWED_ROLES = [RoleEnum.UCAR_ADMIN, RoleEnum.PRESIDENT, RoleEnum.SECRETARY_GENERAL]


@router.get("/", summary="Liste toutes les institutions avec stats")
def list_institutions(db: Session = Depends(database.get_db)):
    """Retourne toutes les institutions enfants de l'UCAR avec leurs stats agrégées."""
    from backend.models import Institution, InstitutionTypeEnum
    # Trouver l'institution racine UCAR
    ucar = db.query(Institution).filter(Institution.code == "UCAR").first()
    parent_id = ucar.id if ucar else None
    return crud.get_institutions_with_stats(db, parent_id=parent_id)


@router.get("/global/stats", summary="Statistiques globales UCAR agrégées depuis toutes les facultés")
def global_stats(db: Session = Depends(database.get_db)):
    """
    Stats globales calculées depuis les labs de toutes les institutions.
    Utilisé par le dashboard PRESIDENT et UCAR_ADMIN.
    """
    global_s = crud.get_institution_stats(db, institution_id=None)
    institutions = crud.get_institutions_with_stats(db, parent_id=None)
    # Filtrer pour exclure l'UCAR elle-même
    faculties = [i for i in institutions if i.get("code") != "UCAR"]
    return {
        "global": global_s,
        "by_institution": faculties
    }


@router.get("/{institution_id}", summary="Détails d'une institution")
def get_institution(institution_id: int, db: Session = Depends(database.get_db)):
    inst = crud.get_institution(db, institution_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Institution non trouvee")
    stats = crud.get_institution_stats(db, institution_id=institution_id)
    return {
        "id": inst.id,
        "name": inst.name,
        "code": inst.code,
        "type": inst.type.value if inst.type else None,
        "parent_id": inst.parent_id,
        "description": inst.description,
        **stats
    }


@router.get("/{institution_id}/labs", summary="Labs d'une institution")
def get_institution_labs(institution_id: int, db: Session = Depends(database.get_db)):
    from backend.models import Lab
    import json as _json
    labs = db.query(Lab).filter(Lab.institution_id == institution_id).order_by(Lab.name).all()
    result = []
    for lab in labs:
        domaines = []
        try:
            if lab.domaines:
                domaines = _json.loads(lab.domaines)
        except Exception:
            pass
        result.append({
            "id": lab.id, "name": lab.name, "code": lab.code,
            "institution_id": lab.institution_id, "director": lab.director,
            "nb_etudiants": lab.nb_etudiants, "nb_enseignants": lab.nb_enseignants,
            "financement_total": lab.financement_total, "financement_alloue": lab.financement_alloue,
            "taux_utilisation": round((lab.financement_alloue / lab.financement_total * 100), 1) if lab.financement_total else 0,
            "projets_actifs": lab.projets_actifs, "publications": lab.publications,
            "description": lab.description, "domaines": domaines,
        })
    return result
