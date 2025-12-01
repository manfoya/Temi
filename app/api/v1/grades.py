# app/api/v1/grades.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_roles
from app.models.grade import Grade
from app.models.user import User, Enrollment, UserRole
from app.models.academic import AcademicYear
from app.models.pedagogy import Evaluation
from app.schemas.grade import GradeCreate, GradeResponse
from app.services.calculator import calculate_student_averages
from app.services.simulator import simulate_grades
from app.services.ai_advisor import diagnostic_student

router = APIRouter()

@router.post("/", response_model=GradeResponse, status_code=status.HTTP_201_CREATED)
def add_grade(
    grade_in: GradeCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))
):
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

    # 7. DÉCLENCHEMENT AUTOMATIQUE DE L'IA
    ai_diagnostic = None
    if student.domain:  # Seulement si l'étudiant a choisi un métier cible
        try:
            ai_diagnostic = diagnostic_student(student.matricule, db)
        except Exception as e:
            # L'échec de l'IA ne doit pas bloquer l'ajout de la note
            print(f"Erreur diagnostic IA : {e}")

    return GradeResponse(
        id=new_grade.id,
        student_name=student.full_name,
        evaluation_name=evaluation.name,
        value=new_grade.value,
        ai_diagnostic=ai_diagnostic
    )
    
@router.get("/bulletin/{matricule}")
def get_student_bulletin(
    matricule: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value, UserRole.STUDENT.value))
):
    from app.core.security import check_own_resource
    
    # Vérifier qu'un étudiant accède uniquement à son bulletin
    check_own_resource(current_user, matricule)
    
    # 1. Récupérer l'étudiant
    student = db.query(User).filter(User.matricule == matricule).first()
    if not student:
        raise HTTPException(404, detail="Étudiant introuvable")
    
    # 2. Récupérer l'année courante
    current_year = db.query(AcademicYear).filter(AcademicYear.is_current == True).first()
    if not current_year:
        raise HTTPException(400, detail="Pas d'année active")

    # 3. Récupérer l'inscription
    enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == student.id,
        Enrollment.academic_year_id == current_year.id
    ).first()
    
    if not enrollment:
        raise HTTPException(404, detail="Étudiant non inscrit cette année")

    # 4. Calculer
    bulletin = calculate_student_averages(enrollment.id, db)
    return bulletin


@router.get("/simulation/{matricule}")
def simulate_target(
    matricule: str, 
    target: float = 15.0, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value, UserRole.STUDENT.value))
):
    from app.core.security import check_own_resource
    
    # Vérifier qu'un étudiant accède uniquement à sa simulation
    check_own_resource(current_user, matricule)
    
    return simulate_grades(matricule, target, db)
