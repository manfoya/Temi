# app/services/ai_advisor.py
import os
import google.generativeai as genai
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.grade import Grade
from app.models.pedagogy import ECUE

# Charger les variables d'environnement (.env)
load_dotenv()

# Configurer Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    print("ATTENTION: Pas de clé API Google trouvée dans .env")

def diagnostic_student(matricule: str, db: Session):
    """
    1. Analyse les données (Cerveau Froid)
    2. Génère le coaching (Cerveau Chaud - Gemini)
    """
    # PARTIE 1 : ANALYSE FROIDE (Maths)
    student = db.query(User).filter(User.matricule == matricule).first()
    if not student or not student.domain:
        return {"error": "Profil étudiant incomplet"}

    target_domain = student.domain
    enrollment = student.enrollments[-1] if student.enrollments else None
    
    if not enrollment:
        return {"error": "Pas d'inscription active"}

    skills_report = []
    # Pour le prompt, on va construire une phrase résumé
    summary_text = f"L'étudiant vise le métier : {target_domain.name}. "

    for skill in target_domain.required_skills:
        status = "MANQUANT"
        avg_skill = 0.0
        
        teaching_ecues = skill.ecues 
        if not teaching_ecues:
            status = "NON_ENSEIGNÉ"
        else:
            # Calcul moyenne compétence
            total_points = 0
            count = 0
            for ecue in teaching_ecues:
                eval_ids = [e.id for e in ecue.evaluations]
                if not eval_ids: continue
                grades = db.query(Grade).filter(Grade.enrollment_id == enrollment.id, Grade.evaluation_id.in_(eval_ids)).all()
                if grades:
                    notes = [g.value for g in grades]
                    total_points += sum(notes) / len(notes)
                    count += 1
            
            if count > 0:
                avg_skill = total_points / count
                if avg_skill >= 10: status = "ACQUIS"
                elif avg_skill >= 8: status = "EN_DANGER"
                else: status = "ÉCHEC"
            else:
                status = "PAS_ENCORE_NOTÉ"

        skills_report.append({"skill": skill.name, "status": status, "average": round(avg_skill, 2) if count > 0 else None})
        
        # On ajoute une phrase pour Gemini
        summary_text += f"Compétence {skill.name} : {status} (Note: {round(avg_skill, 2) if count>0 else 'N/A'}). "

    # PARTIE 2 : PARTIE GEMINI
    
    ai_message = "Le service d'IA est désactivé (Pas de clé)."
    
    if api_key:
        try:
            # Le Prompt Système (L'instruction au coach)
            prompt = f"""
            Tu es un mentor pédagogique bienveillant et motivant pour un étudiant.
            Ton ton doit être encourageant mais réaliste. Tu ne dois pas être robotique.
            
            Voici la situation de l'étudiant :
            Nom : {student.full_name}
            {summary_text}
            
            Consignes :
            1. Félicite-le pour ses points forts (ACQUIS).
            2. Alerte-le gentiment sur les manques (NON_ENSEIGNÉ ou ÉCHEC) en expliquant pourquoi c'est important pour son métier visé.
            3. Sois concis (max 3 phrases).
            4. Si une compétence manque, suggère-lui de l'apprendre en autodidacte.
            """
            
            # On utilise le modèle le plus récent et rapide
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)
            ai_message = response.text
        except Exception as e:
            ai_message = f"Erreur IA : {str(e)}"

    # Résultat final
    return {
        "student": student.full_name,
        "career_goal": target_domain.name,
        "skills_analysis": skills_report,
        "ai_coach_message": ai_message # C'est ça le CADEAU !
    }
