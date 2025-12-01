# app/services/simulator.py
import os
import google.generativeai as genai
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.pedagogy import ECUE, EvalType
from app.models.grade import Grade
from app.models.academic import AcademicYear

# Configurer Gemini
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def simulate_grades(matricule: str, target_average: float, db: Session):
    """
    1. Calcule le plan mathématique (Optimisation sous contrainte).
    2. Génère le conseil stratégique via Gemini.
    """
    #1. INITIALISATION
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
    
    avg_coef = sum(e.coefficient for e in all_ecues) / len(all_ecues) if all_ecues else 0

    # 2. ÉTAT DES LIEUX
    total_coefs = 0
    points_secured = 0.0 
    exams_to_solve = []

    for ue in enrollment.classe.ues:
        for ecue in ue.ecues:
            total_coefs += ecue.coefficient
            
            # Devoirs (Acquis)
            devoir_ids = [e.id for e in ecue.evaluations if e.type == EvalType.DEVOIR]
            avg_devoir = 0.0
            if devoir_ids:
                grades = db.query(Grade).filter(Grade.enrollment_id == enrollment.id, Grade.evaluation_id.in_(devoir_ids)).all()
                if grades:
                    avg_devoir = sum(g.value for g in grades) / len(grades)
            
            points_from_devoir = avg_devoir * ecue.weight_devoir * ecue.coefficient
            points_secured += points_from_devoir

            # Examen (Inconnue ou Acquis)
            exam_ids = [e.id for e in ecue.evaluations if e.type == EvalType.EXAMEN]
            exam_grade = None
            if exam_ids:
                exam_grade = db.query(Grade).filter(Grade.enrollment_id == enrollment.id, Grade.evaluation_id.in_(exam_ids)).first()

            if exam_grade:
                points_secured += exam_grade.value * ecue.weight_examen * ecue.coefficient
            else:
                # Calcul priorité
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

    # 3. RÉSOLUTION MATHÉMATIQUE
    target_points_total = target_average * total_coefs
    missing_points = target_points_total - points_secured
    
    simulation_results = []
    possible = True
    coach_text = "L'objectif semble déjà atteint ou impossible à calculer."

    if missing_points > 0 and exams_to_solve:
        total_effort_units = sum(ex["coef"] * ex["weight_exam"] * ex["priority_factor"] for ex in exams_to_solve)
        
        if total_effort_units > 0:
            base_effort = missing_points / total_effort_units
            
            summary_for_ai = f"Objectif global: {target_average}/20. Plan proposé :\n"

            for ex in exams_to_solve:
                target_grade = base_effort * ex["priority_factor"]
                if target_grade > 20: 
                    target_grade = 20.0
                    possible = False 
                elif target_grade < 0: target_grade = 0.0

                simulation_results.append({
                    "matiere": ex["ecue_name"],
                    "categorie": ex["category"],
                    "note_exam_cible": round(target_grade, 2)
                })
                summary_for_ai += f"- {ex['ecue_name']} ({ex['category']}) : Viser {round(target_grade, 2)}/20.\n"

            # 4. APPEL GEMINI (COACHING)
            if api_key:
                try:
                    prompt = f"""
                    Agis comme un stratège académique pour l'étudiant {student.full_name}.
                    Il vise {target_average}/20 de moyenne.
                    Voici le plan de bataille mathématique calculé :
                    {summary_for_ai}
                    
                    Consignes :
                    1. Résume la stratégie en 2-3 phrases simples.
                    2. Mets l'accent sur les matières CRITIQUES ou STRATEGIQUES (ce sont les clés de la réussite).
                    3. Si les notes cibles sont élevées (>16), sois motivant ("C'est un challenge, mais tu peux le faire").
                    4. Si c'est facile (<12), dis-lui d'assurer l'essentiel.
                    """
                    model = genai.GenerativeModel('gemini-2.0-flash')
                    response = model.generate_content(prompt)
                    coach_text = response.text
                except Exception as e:
                    coach_text = f"Erreur IA : {str(e)}"
    
    elif missing_points <= 0:
        possible = True
        coach_text = "Félicitations ! Avec tes notes actuelles, tu as déjà mathématiquement atteint ton objectif. Continue comme ça !"

    return {
        "status": "POSSIBLE" if possible else "DIFFICILE",
        "target_average": target_average,
        "plan": simulation_results,
        "ai_strategy_advice": coach_text # La touche finale
    }
