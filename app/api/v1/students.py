# app/api/v1/students.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import User, UserRole, Enrollment
from app.models.academic import Classe, Filiere
from app.services.importer import process_student_import
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse, EnrollmentCreate, EnrollmentResponse
from passlib.context import CryptContext
from typing import Optional, List

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()

@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(
    student_in: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))
):
    # Vérifier doublon matricule
    existing = db.query(User).filter(User.matricule == student_in.matricule).first()
    if existing:
        raise HTTPException(400, detail="Ce matricule existe déjà")
    
    # Créer utilisateur
    new_student = User(
        matricule=student_in.matricule,
        full_name=student_in.full_name,
        email=student_in.email,
        activation_secret=student_in.activation_secret,
        hashed_password=pwd_context.hash("default_password"),
        role=UserRole.STUDENT.value,
        is_active=False
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    
    return new_student

@router.get("/", response_model=List[StudentResponse])
def get_students(
    classe_id: Optional[int] = Query(None),
    filiere_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))
):
    # Récupérer tous les étudiants
    query = db.query(User).filter(User.role == UserRole.STUDENT.value)
    
    # Filtrer par classe si spécifié
    if classe_id:
        student_ids = db.query(Enrollment.student_id).filter(Enrollment.classe_id == classe_id).distinct().all()
        student_ids = [sid[0] for sid in student_ids]
        query = query.filter(User.id.in_(student_ids))
    
    # Filtrer par filière si spécifié
    if filiere_code:
        classe_ids = db.query(Classe.id).filter(Classe.filiere_code == filiere_code).all()
        classe_ids = [cid[0] for cid in classe_ids]
        student_ids = db.query(Enrollment.student_id).filter(Enrollment.classe_id.in_(classe_ids)).distinct().all()
        student_ids = [sid[0] for sid in student_ids]
        query = query.filter(User.id.in_(student_ids))
    
    return query.all()

@router.get("/{matricule}", response_model=StudentResponse)
def get_student_details(
    matricule: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value, UserRole.STUDENT.value))
):
    from app.core.security import check_own_resource
    
    # Vérifier accès ressource propre
    check_own_resource(current_user, matricule)
    
    # Récupérer étudiant
    student = db.query(User).filter(User.matricule == matricule).first()
    if not student:
        raise HTTPException(404, detail="Étudiant introuvable")
    
    return student

@router.put("/{matricule}", response_model=StudentResponse)
def update_student(
    matricule: str,
    student_in: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))
):
    # Vérifier étudiant
    student = db.query(User).filter(User.matricule == matricule).first()
    if not student:
        raise HTTPException(404, detail="Étudiant introuvable")
    
    # Mise à jour
    if student_in.full_name is not None:
        student.full_name = student_in.full_name
    if student_in.email is not None:
        student.email = student_in.email
    if student_in.domain_id is not None:
        student.domain_id = student_in.domain_id
    
    db.commit()
    db.refresh(student)
    
    return student

@router.post("/enroll", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def enroll_student(
    enrollment_in: EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))
):
    # Vérifier étudiant
    student = db.query(User).filter(User.matricule == enrollment_in.student_matricule).first()
    if not student:
        raise HTTPException(404, detail="Étudiant introuvable")
    
    # Vérifier classe
    classe = db.query(Classe).filter(Classe.id == enrollment_in.classe_id).first()
    if not classe:
        raise HTTPException(404, detail="Classe introuvable")
    
    # Vérifier doublon inscription
    existing = db.query(Enrollment).filter(
        Enrollment.student_id == student.id,
        Enrollment.academic_year_id == enrollment_in.academic_year_id
    ).first()
    if existing:
        raise HTTPException(400, detail="Étudiant déjà inscrit pour cette année")
    
    # Créer inscription
    new_enrollment = Enrollment(
        student_id=student.id,
        classe_id=enrollment_in.classe_id,
        academic_year_id=enrollment_in.academic_year_id
    )
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    
    return new_enrollment

@router.delete("/{matricule}/enrollments/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_enrollment(
    matricule: str,
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))
):
    # Vérifier étudiant
    student = db.query(User).filter(User.matricule == matricule).first()
    if not student:
        raise HTTPException(404, detail="Étudiant introuvable")
    
    # Vérifier inscription
    enrollment = db.query(Enrollment).filter(
        Enrollment.id == enrollment_id,
        Enrollment.student_id == student.id
    ).first()
    if not enrollment:
        raise HTTPException(404, detail="Inscription introuvable")
    
    # Vérifier absence notes
    from app.models.grade import Grade
    grades_count = db.query(Grade).filter(Grade.enrollment_id == enrollment_id).count()
    if grades_count > 0:
        raise HTTPException(400, detail="Impossible de supprimer une inscription avec des notes")
    
    # Suppression
    db.delete(enrollment)
    db.commit()

@router.post("/import", summary="Import en masse des étudiants (CSV/Excel)")
def import_students(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))
):
    return process_student_import(file, db)
