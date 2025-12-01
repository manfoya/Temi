# app/api/v1/advisor.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_roles, check_own_resource
from app.models.user import User, UserRole
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
