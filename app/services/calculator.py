# app/services/calculator.py
from sqlalchemy.orm import Session
from app.models.user import Enrollment
from app.models.pedagogy import ECUE, UE, Evaluation, EvalType
from app.models.grade import Grade

def calculate_student_averages(enrollment_id: int, db: Session):
    """
    Calcule toutes les moyennes (ECUE, UE, Générale) pour une inscription donnée.
    Retourne un dictionnaire structuré (Bulletin).
    """
    enrollment = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
    if not enrollment:
        return None

    # On récupère la classe pour connaitre les UEs
    classe = enrollment.classe
    bulletin = {
        "student": enrollment.student.full_name,
        "classe": classe.name,
        "ues": [],
        "global_average": 0.0,
        "total_credits_attempted": 0.0,
        "total_credits_validated": 0.0
    }

    sum_ue_means_x_credits = 0.0
    sum_ue_credits = 0.0

    # 1. Boucle sur chaque UE de la classe
    for ue in classe.ues:
        ue_data = {
            "code": ue.code,
            "name": ue.name,
            "credits": ue.credits,
            "ecues": [],
            "average": 0.0,
            "validated": False
        }

        sum_ecue_means_x_coef = 0.0
        sum_ecue_coefs = 0.0

        # 2. Boucle sur chaque ECUE de l'UE
        for ecue in ue.ecues:
            # --- CALCUL MOYENNE ECUE ---
            grades = db.query(Grade).filter(
                Grade.enrollment_id == enrollment.id,
                Grade.evaluation_id.in_([e.id for e in ecue.evaluations])
            ).all()

            # Séparer les notes par type
            notes_devoir = [g.value for g in grades if g.evaluation.type == EvalType.DEVOIR]
            notes_tp = [g.value for g in grades if g.evaluation.type == EvalType.TP]
            notes_exam = [g.value for g in grades if g.evaluation.type == EvalType.EXAMEN]
            notes_projet = [g.value for g in grades if g.evaluation.type == EvalType.PROJET]

            # Calcul des moyennes partielles (Moyenne des 15 devoirs par exemple)
            avg_dev = sum(notes_devoir) / len(notes_devoir) if notes_devoir else 0.0
            avg_tp = sum(notes_tp) / len(notes_tp) if notes_tp else 0.0
            avg_exam = sum(notes_exam) / len(notes_exam) if notes_exam else 0.0 # Souvent 1 seul exam
            avg_proj = sum(notes_projet) / len(notes_projet) if notes_projet else 0.0

            # Formule ECUE (Pondération des types)
            # Note: Si un poids est > 0 mais qu'il n'y a pas de note, ça fait baisser la moyenne (c'est normal, c'est zéro)
            ecue_mean = (
                (avg_dev * ecue.weight_devoir) +
                (avg_tp * ecue.weight_tp) +
                (avg_exam * ecue.weight_examen) +
                (avg_proj * getattr(ecue, 'weight_projet', 0.0))
            )

            ecue_data = {
                "code": ecue.code,
                "name": ecue.name,
                "coef": ecue.coefficient,
                "average": round(ecue_mean, 2)
            }
            ue_data["ecues"].append(ecue_data)

            # Préparation calcul UE
            sum_ecue_means_x_coef += (ecue_mean * ecue.coefficient)
            sum_ecue_coefs += ecue.coefficient

        # --- CALCUL MOYENNE UE ---
        if sum_ecue_coefs > 0:
            ue_mean = sum_ecue_means_x_coef / sum_ecue_coefs
        else:
            ue_mean = 0.0
        
        ue_data["average"] = round(ue_mean, 2)
        
        # Validation Crédits (Règle standard LMD : Moyenne UE >= 10)
        if ue_mean >= 10.0:
            ue_data["validated"] = True
            bulletin["total_credits_validated"] += ue.credits

        bulletin["ues"].append(ue_data)

        # Préparation calcul Général (Pondéré par les CREDITS de l'UE)
        sum_ue_means_x_credits += (ue_mean * ue.credits)
        sum_ue_credits += ue.credits
        bulletin["total_credits_attempted"] += ue.credits

    # CALCUL MOYENNE GÉNÉRALE
    if sum_ue_credits > 0:
        bulletin["global_average"] = round(sum_ue_means_x_credits / sum_ue_credits, 2)
    else:
        bulletin["global_average"] = 0.0

    return bulletin
