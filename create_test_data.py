# create_test_data.py
from app.core.database import SessionLocal
from app.models.academic import Filiere, AcademicYear
from app.models import user 

def create_data():
    db = SessionLocal()
    try:
        print("Création des données de test")
        
        # 1. Créer l'année scolaire
        year = db.query(AcademicYear).filter_by(name="2024-2025").first()
        if not year:
            year = AcademicYear(name="2024-2025", is_current=True)
            db.add(year)
            print("✅ Année 2024-2025 créée.")
        
        # 2. Créer la filière
        filiere = db.query(Filiere).filter_by(code="L3-STAT").first()
        if not filiere:
            filiere = Filiere(name="Licence 3 Statistique Appliquée", code="L3-STAT")
            db.add(filiere)
            print("Filière L3-STAT créée.")
            
        db.commit()
        print("Terminé ")
        
    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_data()
