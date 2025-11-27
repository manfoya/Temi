# init_db.py
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models import user as user_model
from app.core.security import get_password_hash
from app.models import academic
from app.models import pedagogy
from app.models import grade

def init_db():
    db = SessionLocal()
    
    try:
        # Vérifier si le SuperAdmin existe déjà
        super_admin = db.query(user_model.User).filter(user_model.User.role == user_model.UserRole.SUPER_ADMIN).first()
        
        if not super_admin:
            print("Création du SuperAdmin...")
            super_admin = user_model.User(
                matricule="SUPER_ADMIN",
                full_name="Administrateur Système",
                email="admin@temi.school",
                hashed_password=get_password_hash("admin123"), # mot de passe par défaut
                role=user_model.UserRole.SUPER_ADMIN,
                is_active=True # Le SuperAdmin est toujours actif par défaut
            )
            db.add(super_admin)
            db.commit()
            print("SuperAdmin créé avec succès ! (Matricule: SUPER_ADMIN / Pass: admin123)")
        else:
            print("Le SuperAdmin existe déjà.")
            
    except Exception as e:
        print(f"Erreur lors de l'initialisation : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Initialisation de la base de données...")
    
    init_db()
