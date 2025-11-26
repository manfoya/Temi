# app/api/v1/students.py
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.importer import process_student_import

router = APIRouter()

@router.post("/import", summary="Import en masse des étudiants (CSV/Excel)")
def import_students(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Colonnes attendues : matricule, nom, prenom, filiere_code, annee, (date_naissance optionnel)
    """
    return process_student_import(file, db)
