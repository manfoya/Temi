# fix_year.py
from app.core.database import SessionLocal
from app.models.academic import AcademicYear
# L'import ci-dessous est obligatoire pour que SQLAlchemy connaisse les liens
from app.models import user    # Pour Enrollment
from app.models import pedagogy    # Pour UE
from app.models import academic   # Pour Classe

def activate_year():
    db = SessionLocal()
    try:
        print("--- Activation de l'année scolaire ---")
        year = db.query(AcademicYear).filter(AcademicYear.name == "2024-2025").first()
        
        if year:
            year.is_current = True
            db.commit()
            print("Année '2024-2025' définie comme ACTIVE.")
        else:
            print("Année introuvable, création en cours...")
            new_year = AcademicYear(name="2024-2025", is_current=True)
            db.add(new_year)
            db.commit()
            print("Année '2024-2025' créée et activée.")
            
    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    activate_year()
