"""
Migration vers l'architecture multi-institutions.
Execute: python migrate_multi_institution.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import engine, Base, SessionLocal
from sqlalchemy import text

def run():
    print("=== Migration Multi-Institutions ===")

    # 1. Supprimer la base existante (chemin SQLite)
    db_path = "ucar_app.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Base de donnees '{db_path}' supprimee.")

    # 2. Recreer toutes les tables
    Base.metadata.create_all(bind=engine)
    print("Toutes les tables recreees.")

    # 3. Seeder les donnees
    from backend.crud import seed_db_if_empty
    db = SessionLocal()
    try:
        seed_db_if_empty(db)
        print("Seed effectue avec succes.")
    except Exception as e:
        print(f"Erreur seed: {e}")
        import traceback; traceback.print_exc()
    finally:
        db.close()

    print("\n=== Migration terminee ===")
    print("Comptes disponibles:")
    print("  ucar@ucar.tn       / admin123  -> UCAR_ADMIN (vue globale)")
    print("  president@ucar.tn  / admin123  -> PRESIDENT")
    print("  sg@ucar.tn         / admin123  -> SECRETARY_GENERAL")
    print("  enstab@ucar.tn     / admin123  -> FACULTY_ADMIN (ENSTAB)")
    print("  fsegt@ucar.tn      / admin123  -> FACULTY_ADMIN (FSEGT)")
    print("  ipeis@ucar.tn      / admin123  -> FACULTY_ADMIN (IPEIS)")
    print("  isg@ucar.tn        / admin123  -> FACULTY_ADMIN (ISG)")

if __name__ == "__main__":
    run()
