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
from app.models.academic import Filiere, AcademicYear
from app.core.security import get_password_hash
import io

def process_student_import(file: UploadFile, db: Session):
    # 1. Lire le fichier selon l'extension
    content = file.file.read()
    if file.filename.endswith('.csv'):
        df = pd.read_csv(io.BytesIO(content))
    elif file.filename.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(io.BytesIO(content))
    else:
        raise HTTPException(400, "Format non supporté. Utilisez CSV ou Excel.")

    # 2. Normaliser les noms de colonnes (en minuscules pour éviter les erreurs)
    df.columns = [c.lower().strip() for c in df.columns]
    
    required_cols = ['matricule', 'nom', 'prenom', 'filiere_code', 'annee']
    for col in required_cols:
        if col not in df.columns:
            raise HTTPException(400, f"Colonne manquante : {col}")

    report = {"success": 0, "errors": [], "total": len(df)}

    # 3. Boucler sur chaque ligne
    for index, row in df.iterrows():
        try:
            # A. Gestion de l'Année
            annee_name = str(row['annee'])
            year_obj = db.query(AcademicYear).filter(AcademicYear.name == annee_name).first()
            if not year_obj:
                # On crée l'année à la volée si elle n'existe pas (optionnel, dépend de ta rigueur)
                year_obj = AcademicYear(name=annee_name)
                db.add(year_obj)
                db.commit()

            # B. Gestion de la Filière
            filiere_code = str(row['filiere_code'])
            filiere_obj = db.query(Filiere).filter(Filiere.code == filiere_code).first()
            if not filiere_obj:
                report["errors"].append(f"Ligne {index}: Filière {filiere_code} inconnue.")
                continue

            #  C. Gestion de l'Utilisateur (Coquille vide) 
            matricule = str(row['matricule'])
            user = db.query(User).filter(User.matricule == matricule).first()
            
            if not user:
                # Création du compte "En attente"
                # SECRET D'ACTIVATION = DATE DE NAISSANCE (si présente) ou Code par défaut
                # Pour l'exemple simple, on met "1234" si pas de colonne date_naissance
                secret = str(row.get('date_naissance', '1234')) 
                
                user = User(
                    matricule=matricule,
                    full_name=f"{row['nom']} {row['prenom']}",
                    role=UserRole.STUDENT,
                    is_active=False, # Important : Inactif par défaut
                    activation_secret=secret, 
                    hashed_password=get_password_hash("temp_password") # Pass temporaire, sera changé à l'activation
                )
                db.add(user)
                db.commit()
                db.refresh(user)

            #D. Inscription (Enrollment)
            # Vérifier si déjà inscrit cette année
            enrollment = db.query(Enrollment).filter(
                Enrollment.student_id == user.id,
                Enrollment.academic_year_id == year_obj.id
            ).first()

            if not enrollment:
                enrollment = Enrollment(
                    student_id=user.id,
                    filiere_id=filiere_obj.id,
                    academic_year_id=year_obj.id
                )
                db.add(enrollment)
                db.commit()
                report["success"] += 1

        except Exception as e:
            report["errors"].append(f"Ligne {index}: Erreur interne - {str(e)}")
            db.rollback()

    return report
