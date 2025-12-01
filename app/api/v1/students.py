# app/api/v1/students.py
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import User, UserRole
from app.services.importer import process_student_import

router = APIRouter()

@router.post("/import", summary="Import en masse des étudiants (CSV/Excel)")
def import_students(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))
):
    return process_student_import(file, db)
