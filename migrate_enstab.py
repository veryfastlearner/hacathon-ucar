import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import engine, Base, SessionLocal
from backend.models import User, RoleEnum, Lab
import hashlib

Base.metadata.create_all(bind=engine)
db = SessionLocal()

def hp(p):
    return hashlib.sha256(p.encode()).hexdigest()

try:
    existing = db.query(User).filter(User.email == "enstab@ucar.tn").first()
    if existing:
        print("Utilisateur enstab@ucar.tn existe deja, role:", existing.role)
    else:
        u = User(
            fullName="Direction ENSTAB",
            email="enstab@ucar.tn",
            passwordHash=hp("admin123"),
            role=RoleEnum.FACULTY_ENSTAB
        )
        db.add(u)
        db.commit()
        print("Utilisateur ENSTAB cree avec succes!")

    lab_count = db.query(Lab).filter(Lab.faculty == "ENSTAB").count()
    if lab_count > 0:
        print(f"{lab_count} labs ENSTAB existent deja.")
    else:
        labs = [
            Lab(name="Laboratoire de Genie Informatique et Systemes", code="LGIS", faculty="ENSTAB",
                director="Pr. Mohamed Ali Hadj Amor", nb_etudiants=52, nb_enseignants=9,
                financement_total=180000.0, financement_alloue=130000.0, projets_actifs=6, publications=28,
                description="Recherche en IA, systemes embarques et reseaux intelligents.",
                domaines='["Intelligence Artificielle", "Systemes embarques", "Reseaux", "IoT"]'),
            Lab(name="Laboratoire de Genie Electrique et Energies Renouvelables", code="LGEER", faculty="ENSTAB",
                director="Pr. Faouzi Ben Amara", nb_etudiants=38, nb_enseignants=7,
                financement_total=210000.0, financement_alloue=155000.0, projets_actifs=4, publications=35,
                description="Recherche sur les systemes electriques, energie solaire et eolienne.",
                domaines='["Energie Renouvelable", "Electrotechnique", "Smart Grid", "Photovoltaique"]'),
            Lab(name="Laboratoire de Genie Mecanique et Materiaux", code="LGMM", faculty="ENSTAB",
                director="Dr. Sonia Mzali", nb_etudiants=44, nb_enseignants=8,
                financement_total=150000.0, financement_alloue=95000.0, projets_actifs=5, publications=19,
                description="Simulation mecanique, materiaux composites et fabrication additive.",
                domaines='["Mecanique des fluides", "Materiaux Composites", "Impression 3D", "CAO"]'),
            Lab(name="Laboratoire de Physique Appliquee et Optoelectronique", code="LPAO", faculty="ENSTAB",
                director="Pr. Hatem Elloumi", nb_etudiants=30, nb_enseignants=6,
                financement_total=120000.0, financement_alloue=80000.0, projets_actifs=3, publications=22,
                description="Recherche en physique des semi-conducteurs et photonique.",
                domaines='["Optoelectronique", "Semi-conducteurs", "Photonique", "Nanotechnologie"]'),
            Lab(name="Laboratoire Genie Chimique et Procedes", code="LGCP", faculty="ENSTAB",
                director="Dr. Rim Gharbi", nb_etudiants=27, nb_enseignants=5,
                financement_total=95000.0, financement_alloue=60000.0, projets_actifs=2, publications=14,
                description="Genie des procedes, catalyse et traitement des eaux.",
                domaines='["Genie chimique", "Traitement des eaux", "Catalyse", "Environnement"]'),
            Lab(name="Laboratoire Mathematiques et Modelisation", code="LMM", faculty="ENSTAB",
                director="Pr. Kamel Zouari", nb_etudiants=22, nb_enseignants=5,
                financement_total=75000.0, financement_alloue=45000.0, projets_actifs=2, publications=17,
                description="Modelisation mathematique, optimisation et statistiques appliquees.",
                domaines='["Mathematiques appliquees", "Optimisation", "Statistiques", "Modelisation"]'),
        ]
        db.add_all(labs)
        db.commit()
        print(f"{len(labs)} labs ENSTAB crees avec succes!")

    print("\nMigration terminee!")
    print("Email : enstab@ucar.tn")
    print("Mot de passe : admin123")

except Exception as e:
    print(f"Erreur: {e}")
    db.rollback()
finally:
    db.close()
