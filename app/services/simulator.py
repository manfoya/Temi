# app/services/simulator.py
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.pedagogy import ECUE, EvalType
from app.models.grade import Grade
from app.models.academic import AcademicYear

def simulate_grades(matricule: str, target_average: float, db: Session):
    """
    Simulateur LMD Intelligent.
    """
    # 1. INITIALISATION
    student = db.query(User).filter(User.matricule == matricule).first()
    if not student: return {"error": "Étudiant introuvable"}
    enrollment = student.enrollments[-1] if student.enrollments else None
    if not enrollment: return {"error": "Pas d'inscription active"}

    passion_ecue_ids = []
    if student.domain:
        for skill in student.domain.required_skills:
            for ecue in skill.ecues:
                passion_ecue_ids.append(ecue.id)

    all_ecues = []
    for ue in enrollment.classe.ues:
        all_ecues.extend(ue.ecues)
    
    avg_coef = 0
    if all_ecues:
        avg_coef = sum(e.coefficient for e in all_ecues) / len(all_ecues)

    # 2. ÉTAT DES LIEUX
    total_coefs = 0
    points_secured = 0.0 
    
    exams_to_solve = []

    for ue in enrollment.classe.ues:
        for ecue in ue.ecues:
            total_coefs += ecue.coefficient
            
            # A. DEVOIRS (Points Acquis)
            devoir_ids = [e.id for e in ecue.evaluations if e.type == EvalType.DEVOIR]
            avg_devoir = 0.0
            
            if devoir_ids:
                # Filtre par IDs au lieu de JOIN
                grades_devoir = db.query(Grade).filter(
                    Grade.enrollment_id == enrollment.id,
                    Grade.evaluation_id.in_(devoir_ids)
                ).all()
                
                if grades_devoir:
                    vals = [g.value for g in grades_devoir]
                    avg_devoir = sum(vals) / len(vals)
            
            points_from_devoir = avg_devoir * ecue.weight_devoir * ecue.coefficient
            points_secured += points_from_devoir

            # B. EXAMEN (Inconnue ou Acquis)
            exam_ids = [e.id for e in ecue.evaluations if e.type == EvalType.EXAMEN]
            exam_grade = None
            
            if exam_ids:
                # Filtre par IDs
                exam_grade = db.query(Grade).filter(
                    Grade.enrollment_id == enrollment.id,
                    Grade.evaluation_id.in_(exam_ids)
                ).first()

            if exam_grade:
                # Examen déjà passé
                points_from_exam = exam_grade.value * ecue.weight_examen * ecue.coefficient
                points_secured += points_from_exam
            else:
                # Examen À VENIR (Simulation)
                is_passion = ecue.id in passion_ecue_ids
                is_gros_coef = ecue.coefficient >= avg_coef
                
                category = "SECONDAIRE"
                priority_factor = 1.0 

                if is_passion and is_gros_coef:
                    category = "CRITIQUE"
                    priority_factor = 3.0 
                elif not is_passion and is_gros_coef:
                    category = "STRATEGIQUE"
                    priority_factor = 2.0 
                elif is_passion and not is_gros_coef:
                    category = "COMPETENCE"
                    priority_factor = 1.5 
                
                exams_to_solve.append({
                    "ecue_name": ecue.name,
                    "category": category,
                    "coef": ecue.coefficient,
                    "weight_exam": ecue.weight_examen,
                    "priority_factor": priority_factor,
                    "avg_devoir": avg_devoir
                })

    # 3. RÉSOLUTION
    target_points_total = target_average * total_coefs
    missing_points = target_points_total - points_secured
    
    if missing_points <= 0:
        return {"status": "SUCCESS", "message": "Objectif déjà atteint !"}

    total_effort_units = sum(
        ex["coef"] * ex["weight_exam"] * ex["priority_factor"] for ex in exams_to_solve
    )

    if total_effort_units == 0:
        return {"status": "IMPOSSIBLE", "message": "Plus d'examens disponibles."}

    base_effort = missing_points / total_effort_units

    # 4. GÉNÉRATION PLAN
    simulation_results = []
    possible = True

    for ex in exams_to_solve:
        target_grade = base_effort * ex["priority_factor"]
        
        if target_grade > 20:
            target_grade = 20.0
            possible = False 
        elif target_grade < 0:
            target_grade = 0.0

        projected_ecue_avg = (ex["avg_devoir"] * (1 - ex["weight_exam"])) + (target_grade * ex["weight_exam"])

        simulation_results.append({
            "matiere": ex["ecue_name"],
            "categorie": ex["category"],
            "note_exam_cible": round(target_grade, 2),
            "moyenne_dev_actuelle": round(ex["avg_devoir"], 2),
            "moyenne_finale_projete": round(projected_ecue_avg, 2)
        })

    return {
        "status": "POSSIBLE" if possible else "DIFFICILE",
        "target_average": target_average,
        "global_advice": "Objectif atteignable" if possible else "Objectif mathématiquement impossible.",
        "plan": simulation_results
    }
