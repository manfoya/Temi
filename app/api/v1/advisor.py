# app/api/v1/advisor.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.ai_advisor import diagnostic_student

router = APIRouter()

@router.get("/diagnostic/{matricule}")
def get_student_diagnostic(matricule: str, db: Session = Depends(get_db)):
    """
    Génère le rapport de compétences (Le Cerveau Froid)
    """
    report = diagnostic_student(matricule, db)
    if "error" in report:
        raise HTTPException(400, detail=report["error"])
    return report
