# seed_full_demo.py
from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from app.models import academic, user, pedagogy, grade, career
from app.models.academic import AcademicYear, Filiere, Classe
from app.models.pedagogy import UE, ECUE, Evaluation, EvalType
from app.models.user import User, UserRole, Enrollment
from app.models.grade import Grade
from app.models.career import Skill, Domain

def run_seed():
    # 1. Création des tables
    academic.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    print("--- DÉMARRAGE DU SEEDING COMPLET ---")

    try:
        # 2. Année Scolaire
        year = AcademicYear(name="2024-2025", is_current=True)
        db.add(year)
        db.commit()
        print("✅ Année 2024-2025 créée")

        # 3. Filière & Classe
        filiere = Filiere(name="Statistique", code="STAT")
        db.add(filiere)
        db.commit()
        
        classe = Classe(filiere_id=filiere.id, name="Licence 3 Statistique", code="L3-STAT", level="L3")
        db.add(classe)
        db.commit()
        print("✅ Classe L3-STAT créée")

        # 4. Compétences (Skills) & Domaine
        skill_python = Skill(name="Python")
        skill_stats = Skill(name="Statistiques Avancées")
        skill_sql = Skill(name="SQL") # Compétence manquante exprès
        
        domain_ds = Domain(name="Data Scientist", description="Expert en données")
        # On dit que Data Scientist requiert Python, Stats et SQL
        domain_ds.required_skills = [skill_python, skill_stats, skill_sql]
        
        db.add_all([skill_python, skill_stats, skill_sql, domain_ds])
        db.commit()
        print("✅ Domaine Data Scientist & Skills créés")

        # 5. Architecture Pédagogique (UEs & ECUEs)
        # UE INFO
        ue_info = UE(classe_id=classe.id, code="UE-INFO", name="Informatique", credits=4)
        db.add(ue_info)
        db.commit()

        # Matière : Programmation Python
        ecue_python = ECUE(
            ue_id=ue_info.id, code="INF301", name="Programmation Python", 
            coefficient=2, credits=2, weight_examen=1.0
        )
        # *** LE TAGGAGE *** : On dit que ce cours enseigne le skill Python
        ecue_python.taught_skills.append(skill_python)
        db.add(ecue_python)

        # UE MATHS
        ue_math = UE(classe_id=classe.id, code="UE-MATH", name="Mathématiques", credits=6)
        db.add(ue_math)
        db.commit()

        # Matière : Stat Inférentielle
        ecue_stat = ECUE(
            ue_id=ue_math.id, code="STAT305", name="Statistique Inférentielle", 
            coefficient=3, credits=3, weight_examen=1.0
        )
        # *** LE TAGGAGE ***
        ecue_stat.taught_skills.append(skill_stats)
        db.add(ecue_stat)
        
        db.commit()
        print("✅ Matières créées et TAGUÉES avec les compétences")

        # 6. Étudiants & Inscriptions
        # Étudiant 1 : TCHOKPON (Veut faire Data Scientist)
        student = User(
            matricule="194508", full_name="TCHOKPON Manfoya", 
            role=UserRole.STUDENT, is_active=True, hashed_password=get_password_hash("pass"),
            domain_id=domain_ds.id # <--- Il a choisi sa voie !
        )
        db.add(student)
        db.commit()

        enrollment = Enrollment(student_id=student.id, classe_id=classe.id, academic_year_id=year.id)
        db.add(enrollment)
        db.commit()
        print("✅ Étudiant TCHOKPON inscrit avec profil 'Data Scientist'")

        # 7. Notes
        # On crée l'éval pour Python
        eval_py = Evaluation(ecue_id=ecue_python.id, name="Exam Python", type=EvalType.EXAMEN)
        db.add(eval_py)
        db.commit()

        # Note en Python (14/20) -> Il valide la compétence
        grade_py = Grade(enrollment_id=enrollment.id, evaluation_id=eval_py.id, value=14.0)
        db.add(grade_py)
        db.commit()
        print("✅ Notes ajoutées (14/20 en Python)")

        print("\n--- SEEDING TERMINÉ AVEC SUCCÈS ---")

    except Exception as e:
        print(f"❌ Erreur : {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
