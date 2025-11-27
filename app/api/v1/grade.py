# app/api/v1/grades.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.grade import Grade
from app.models.user import User, Enrollment
from app.models.academic import AcademicYear
from app.models.pedagogy import Evaluation
from app.schemas.grade import GradeCreate, GradeResponse

router = APIRouter()

@router.post("/", response_model=GradeResponse, status_code=status.HTTP_201_CREATED)
def add_grade(grade_in: GradeCreate, db: Session = Depends(get_db)):
    # 1. Trouver l'année courante
    current_year = db.query(AcademicYear).filter(AcademicYear.is_current == True).first()
    if not current_year:
        raise HTTPException(400, detail="Aucune année scolaire active définie.")

    # 2. Trouver l'étudiant via Matricule
    student = db.query(User).filter(User.matricule == grade_in.student_matricule).first()
    if not student:
        raise HTTPException(404, detail="Étudiant introuvable.")

    # 3. Trouver son inscription pour l'année en cours
    enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == student.id,
        Enrollment.academic_year_id == current_year.id
    ).first()
    
    if not enrollment:
        raise HTTPException(400, detail="L'étudiant n'est pas inscrit pour l'année en cours.")

    # 4. Vérifier l'évaluation
    evaluation = db.query(Evaluation).filter(Evaluation.id == grade_in.evaluation_id).first()
    if not evaluation:
        raise HTTPException(404, detail="Évaluation introuvable.")

    # 5. Vérifier si note existe déjà (Mise à jour ou Erreur ?)
    # Pour l'instant on bloque les doublons
    existing = db.query(Grade).filter(
        Grade.enrollment_id == enrollment.id,
        Grade.evaluation_id == evaluation.id
    ).first()
    
    if existing:
        raise HTTPException(400, detail="Cet étudiant a déjà une note pour cette évaluation.")

    # 6. Enregistrer
    new_grade = Grade(
        enrollment_id=enrollment.id,
        evaluation_id=evaluation.id,
        value=grade_in.value
    )
    db.add(new_grade)
    db.commit()
    db.refresh(new_grade)

    return GradeResponse(
        id=new_grade.id,
        student_name=student.full_name,
        evaluation_name=evaluation.name,
        value=new_grade.value
    )
