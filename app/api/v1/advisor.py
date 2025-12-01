# app/api/v1/advisor.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import require_roles, check_own_resource
from app.models.user import User, UserRole
from app.models.notification import DiagnosticHistory
from app.services.ai_advisor import diagnostic_student

router = APIRouter()

@router.get("/diagnostic/{matricule}")
def get_student_diagnostic(
    matricule: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value, UserRole.STUDENT.value))
):
    # Vérifier qu'un étudiant accède uniquement à son diagnostic
    check_own_resource(current_user, matricule)
    
    report = diagnostic_student(matricule, db)
    if "error" in report:
        raise HTTPException(400, detail=report["error"])
    return report

@router.get("/history/{matricule}")
def get_diagnostic_history(
    matricule: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value, UserRole.STUDENT.value))
):
    # Vérifier accès ressource propre
    check_own_resource(current_user, matricule)
    
    # Récupérer étudiant
    student = db.query(User).filter(User.matricule == matricule).first()
    if not student:
        raise HTTPException(404, detail="Étudiant introuvable")
    
    # Récupérer historique diagnostics
    history = db.query(DiagnosticHistory).filter(
        DiagnosticHistory.student_id == student.id
    ).order_by(DiagnosticHistory.created_at.desc()).all()
    
    # Formater résultats
    results = []
    for h in history:
        results.append({
            "id": h.id,
            "created_at": h.created_at,
            "diagnostic": h.diagnostic_data,
            "simulation": h.simulation_data
        })
    
    return results
