# app/services/importer.py


"""
Ce serice va :
1 Lire le fichier (csv ou excel)
2 vérifier que les colonnes obligatoires sont là (matricule, nom, prénom, année, filière)
3 créer l'utilisateur user si il n'existe pas
4 créer l'inscription (nommé Enrollment ici) pour l'année donnée
5 générer le "secret" (ici on utilisera la date de naissance par défaut pour l'activation)
"""


import pandas as pd
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from app.models.user import User, Enrollment, UserRole
from app.models.academic import Classe, AcademicYear 
from app.core.security import get_password_hash
import io

def process_student_import(file: UploadFile, db: Session):
    # 1. Lire le fichier
    content = file.file.read()
    if file.filename.endswith('.csv'):
        try:
            df = pd.read_csv(io.BytesIO(content), sep=',')
        except:
            df = pd.read_csv(io.BytesIO(content), sep=';')
    elif file.filename.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(io.BytesIO(content))
    else:
        raise HTTPException(400, "Format non supporté. Utilisez CSV ou Excel.")

    # 2. Normaliser les colonnes
    df.columns = [c.lower().strip() for c in df.columns]
    
    # On vérifie bien la colonne 'classe'
    required_cols = ['matricule', 'nom', 'prenom', "classe", 'annee']
    for col in required_cols:
        if col not in df.columns:
            raise HTTPException(400, f"Colonne manquante : {col}. (Colonnes vues: {list(df.columns)})")

    report = {"success": 0, "errors": [], "total": len(df)}

    # 3. Traitement
    for index, row in df.iterrows():
        try:
            # A. Année
            annee_name = str(row['annee'])
            year_obj = db.query(AcademicYear).filter(AcademicYear.name == annee_name).first()
            if not year_obj:
                year_obj = AcademicYear(name=annee_name, is_current=True)
                db.add(year_obj)
                db.commit()

            # B. CLASSE
            # On lit la colonne 'classe' (ex: L3-STAT) et on cherche l'objet Classe
            classe_code = str(row['classe'])
            classe_obj = db.query(Classe).filter(Classe.code == classe_code).first()
            if not classe_obj:
                report["errors"].append(f"Ligne {index}: Classe '{classe_code}' inconnue. Créez-la d'abord via l'API.")
                continue

            # C. Utilisateur
            matricule = str(row['matricule'])
            user = db.query(User).filter(User.matricule == matricule).first()
            
            if not user:
                secret = str(row.get('date_naissance', '1234'))
                user = User(
                    matricule=matricule,
                    full_name=f"{row['nom']} {row['prenom']}",
                    role=UserRole.STUDENT,
                    is_active=False,
                    activation_secret=secret,
                    hashed_password=get_password_hash("temp_password")
                )
                db.add(user)
                db.commit()
                db.refresh(user)

            # D. Inscription
            enrollment = db.query(Enrollment).filter(
                Enrollment.student_id == user.id,
                Enrollment.academic_year_id == year_obj.id
            ).first()

            if not enrollment:
                enrollment = Enrollment(
                    student_id=user.id,
                    classe_id=classe_obj.id, # Maintenant classe_obj existe !
                    academic_year_id=year_obj.id
                )
                db.add(enrollment)
                db.commit()
                report["success"] += 1
            else:
                 if enrollment.classe_id != classe_obj.id:
                     report["errors"].append(f"Ligne {index}: Étudiant déjà inscrit ailleurs.")
                 else:
                     report["success"] += 1

        except Exception as e:
            report["errors"].append(f"Ligne {index}: Erreur interne - {str(e)}")
            db.rollback()

    return report
