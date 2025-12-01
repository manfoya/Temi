# app/api/v1/pedagogy.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import User, UserRole
from app.models.academic import Filiere, Classe
from app.models.pedagogy import UE, ECUE, Evaluation
from app.schemas.pedagogy import (
    FiliereCreate, FiliereResponse,
    ClasseCreate, ClasseResponse,
    UECreate, UEResponse,
    ECUECreate, ECUEResponse,
    EvaluationCreate, EvaluationResponse
)

router = APIRouter()

# 1. GESTION DES FILIÈRES
@router.post("/filieres", response_model=FiliereResponse, status_code=status.HTTP_201_CREATED)
def create_filiere(
    filiere: FiliereCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    existing = db.query(Filiere).filter(Filiere.code == filiere.code).first()
    if existing:
        raise HTTPException(400, detail="Ce code de filière existe déjà")
    
    new_fil = Filiere(name=filiere.name, code=filiere.code)
    db.add(new_fil)
    db.commit()
    db.refresh(new_fil)
    return new_fil

@router.get("/filieres", response_model=List[FiliereResponse])
def list_filieres(db: Session = Depends(get_db)):
    return db.query(Filiere).all()

@router.get("/filieres/{filiere_id}", response_model=FiliereResponse)
def get_filiere(
    filiere_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))
):
    filiere = db.query(Filiere).filter(Filiere.id == filiere_id).first()
    if not filiere:
        raise HTTPException(404, detail="Filière introuvable")
    return filiere

@router.put("/filieres/{filiere_id}", response_model=FiliereResponse)
def update_filiere(
    filiere_id: int,
    filiere_in: FiliereCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    filiere = db.query(Filiere).filter(Filiere.id == filiere_id).first()
    if not filiere:
        raise HTTPException(404, detail="Filière introuvable")
    
    filiere.name = filiere_in.name
    filiere.code = filiere_in.code
    db.commit()
    db.refresh(filiere)
    return filiere

@router.delete("/filieres/{filiere_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_filiere(
    filiere_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    filiere = db.query(Filiere).filter(Filiere.id == filiere_id).first()
    if not filiere:
        raise HTTPException(404, detail="Filière introuvable")
    
    if filiere.classes:
        raise HTTPException(
            400,
            detail=f"Impossible de supprimer: {len(filiere.classes)} classe(s) liée(s)"
        )
    
    db.delete(filiere)
    db.commit()

# 2. GESTION DES CLASSES
@router.post("/classes", response_model=ClasseResponse, status_code=status.HTTP_201_CREATED)
def create_classe(
    classe_in: ClasseCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    filiere = db.query(Filiere).filter(Filiere.code == classe_in.filiere_code).first()
    if not filiere:
        raise HTTPException(404, detail=f"Filière {classe_in.filiere_code} introuvable")

    existing = db.query(Classe).filter(Classe.code == classe_in.code).first()
    if existing:
        raise HTTPException(400, detail="Ce code de classe existe déjà")

    new_classe = Classe(
        filiere_id=filiere.id,
        name=classe_in.name,
        code=classe_in.code,
        level=classe_in.level
    )
    db.add(new_classe)
    db.commit()
    db.refresh(new_classe)
    
    new_classe.filiere_code = filiere.code
    
    return new_classe

@router.get("/classes", response_model=List[ClasseResponse])
def list_classes(filiere_code: str = None, db: Session = Depends(get_db)):
    query = db.query(Classe)
    if filiere_code:
        clean_code = filiere_code.replace('"', '').replace("'", "")
        query = query.join(Filiere).filter(Filiere.code == clean_code)
    
    classes = query.all()
    
    for c in classes:
        c.filiere_code = c.filiere.code
        
    return classes

@router.get("/classes/{classe_id}", response_model=ClasseResponse)
def get_classe(
    classe_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))
):
    classe = db.query(Classe).filter(Classe.id == classe_id).first()
    if not classe:
        raise HTTPException(404, detail="Classe introuvable")
    
    classe.filiere_code = classe.filiere.code
    return classe

@router.put("/classes/{classe_id}", response_model=ClasseResponse)
def update_classe(
    classe_id: int,
    classe_in: ClasseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    classe = db.query(Classe).filter(Classe.id == classe_id).first()
    if not classe:
        raise HTTPException(404, detail="Classe introuvable")
    
    # Vérifier filière
    filiere = db.query(Filiere).filter(Filiere.code == classe_in.filiere_code).first()
    if not filiere:
        raise HTTPException(404, detail=f"Filière {classe_in.filiere_code} introuvable")
    
    # Mise à jour
    classe.filiere_id = filiere.id
    classe.name = classe_in.name
    classe.code = classe_in.code
    classe.level = classe_in.level
    db.commit()
    db.refresh(classe)
    
    classe.filiere_code = filiere.code
    return classe

@router.delete("/classes/{classe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_classe(
    classe_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    classe = db.query(Classe).filter(Classe.id == classe_id).first()
    if not classe:
        raise HTTPException(404, detail="Classe introuvable")
    
    # Vérifier absence étudiants
    if classe.enrollments:
        raise HTTPException(
            400,
            detail=f"Impossible de supprimer: {len(classe.enrollments)} étudiant(s) inscrit(s)"
        )
    
    db.delete(classe)
    db.commit()
        
    return classes

# 3. GESTION DES UEs
@router.post("/ues", response_model=UEResponse, status_code=status.HTTP_201_CREATED)
def create_ue(
    ue_in: UECreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    classe = db.query(Classe).filter(Classe.code == ue_in.classe_code).first()
    if not classe:
        raise HTTPException(404, detail=f"Classe {ue_in.classe_code} introuvable")
    
    new_ue = UE(
        classe_id=classe.id,
        code=ue_in.code,
        name=ue_in.name,
        credits=ue_in.credits
    )
    db.add(new_ue)
    db.commit()
    db.refresh(new_ue)
    
    # Injection manuelle pour Pydantic
    new_ue.classe_code = classe.code
    
    return new_ue

@router.get("/ues", response_model=List[UEResponse])
def list_ues(classe_code: str = None, db: Session = Depends(get_db)):
    query = db.query(UE)
    if classe_code:
        clean_code = classe_code.replace('"', '').replace("'", "")
        query = query.join(Classe).filter(Classe.code == clean_code)
    
    ues = query.all()
    
    for u in ues:
        u.classe_code = u.classe.code
        
    return ues

@router.get("/ues/{ue_id}", response_model=UEResponse)
def get_ue(
    ue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))
):
    ue = db.query(UE).filter(UE.id == ue_id).first()
    if not ue:
        raise HTTPException(404, detail="UE introuvable")
    
    ue.classe_code = ue.classe.code
    return ue

@router.put("/ues/{ue_id}", response_model=UEResponse)
def update_ue(
    ue_id: int,
    ue_in: UECreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    ue = db.query(UE).filter(UE.id == ue_id).first()
    if not ue:
        raise HTTPException(404, detail="UE introuvable")
    
    # Vérifier classe
    classe = db.query(Classe).filter(Classe.code == ue_in.classe_code).first()
    if not classe:
        raise HTTPException(404, detail=f"Classe {ue_in.classe_code} introuvable")
    
    # Mise à jour
    ue.classe_id = classe.id
    ue.code = ue_in.code
    ue.name = ue_in.name
    ue.credits = ue_in.credits
    db.commit()
    db.refresh(ue)
    
    ue.classe_code = classe.code
    return ue

@router.delete("/ues/{ue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ue(
    ue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    ue = db.query(UE).filter(UE.id == ue_id).first()
    if not ue:
        raise HTTPException(404, detail="UE introuvable")
    
    # Vérifier absence ECUE
    if ue.ecues:
        raise HTTPException(
            400,
            detail=f"Impossible de supprimer: {len(ue.ecues)} ECUE(s) liée(s)"
        )
    
    db.delete(ue)
    db.commit()

# 4. GESTION DES ECUEs
@router.post("/ecues", response_model=ECUEResponse, status_code=status.HTTP_201_CREATED)
def create_ecue(
    ecue_in: ECUECreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    weight_projet = getattr(ecue_in, 'weight_projet', 0.0) 
    total_weight = ecue_in.weight_devoir + ecue_in.weight_tp + ecue_in.weight_examen + weight_projet
    
    if not (0.99 <= total_weight <= 1.01):
        raise HTTPException(
            400, 
            detail=f"La somme des poids (Devoir+TP+Exam) doit faire 1.0 (Actuellement: {total_weight})"
        )

    ue = db.query(UE).filter(UE.id == ecue_in.ue_id).first()
    if not ue:
        raise HTTPException(404, detail="UE introuvable")

    new_ecue = ECUE(
        ue_id=ecue_in.ue_id,
        code=ecue_in.code,
        name=ecue_in.name,
        coefficient=ecue_in.coefficient,
        credits=ecue_in.credits,
        weight_devoir=ecue_in.weight_devoir,
        weight_tp=ecue_in.weight_tp,
        weight_examen=ecue_in.weight_examen
    )
    db.add(new_ecue)
    db.commit()
    db.refresh(new_ecue)
    return new_ecue

@router.get("/ecues/{ecue_id}", response_model=ECUEResponse)
def get_ecue(
    ecue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))
):
    ecue = db.query(ECUE).filter(ECUE.id == ecue_id).first()
    if not ecue:
        raise HTTPException(404, detail="ECUE introuvable")
    return ecue

@router.put("/ecues/{ecue_id}", response_model=ECUEResponse)
def update_ecue(
    ecue_id: int,
    ecue_in: ECUECreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    ecue = db.query(ECUE).filter(ECUE.id == ecue_id).first()
    if not ecue:
        raise HTTPException(404, detail="ECUE introuvable")
    
    # Vérifier somme poids
    weight_projet = getattr(ecue_in, 'weight_projet', 0.0)
    total_weight = ecue_in.weight_devoir + ecue_in.weight_tp + ecue_in.weight_examen + weight_projet
    
    if not (0.99 <= total_weight <= 1.01):
        raise HTTPException(
            400,
            detail=f"La somme des poids doit faire 1.0 (Actuellement: {total_weight})"
        )
    
    # Vérifier UE
    ue = db.query(UE).filter(UE.id == ecue_in.ue_id).first()
    if not ue:
        raise HTTPException(404, detail="UE introuvable")
    
    # Mise à jour
    ecue.ue_id = ecue_in.ue_id
    ecue.code = ecue_in.code
    ecue.name = ecue_in.name
    ecue.coefficient = ecue_in.coefficient
    ecue.credits = ecue_in.credits
    ecue.weight_devoir = ecue_in.weight_devoir
    ecue.weight_tp = ecue_in.weight_tp
    ecue.weight_examen = ecue_in.weight_examen
    db.commit()
    db.refresh(ecue)
    return ecue

@router.delete("/ecues/{ecue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ecue(
    ecue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    ecue = db.query(ECUE).filter(ECUE.id == ecue_id).first()
    if not ecue:
        raise HTTPException(404, detail="ECUE introuvable")
    
    # Vérifier absence évaluations
    if ecue.evaluations:
        raise HTTPException(
            400,
            detail=f"Impossible de supprimer: {len(ecue.evaluations)} évaluation(s) liée(s)"
        )
    
    db.delete(ecue)
    db.commit()

# 5. GESTION DES ÉVALUATIONS 
@router.post("/ecues/{ecue_id}/evaluations", response_model=EvaluationResponse)
def add_evaluation(
    ecue_id: int, 
    eval_in: EvaluationCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))
):
    ecue = db.query(ECUE).filter(ECUE.id == ecue_id).first()
    if not ecue:
        raise HTTPException(404, detail="ECUE introuvable")
        
    new_eval = Evaluation(
        ecue_id=ecue_id,
        name=eval_in.name,
        type=eval_in.type
    )
    db.add(new_eval)
    db.commit()
    db.refresh(new_eval)
    return new_eval

@router.get("/evaluations/{eval_id}", response_model=EvaluationResponse)
def get_evaluation(
    eval_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))
):
    evaluation = db.query(Evaluation).filter(Evaluation.id == eval_id).first()
    if not evaluation:
        raise HTTPException(404, detail="Évaluation introuvable")
    return evaluation

@router.put("/evaluations/{eval_id}", response_model=EvaluationResponse)
def update_evaluation(
    eval_id: int,
    eval_in: EvaluationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))
):
    evaluation = db.query(Evaluation).filter(Evaluation.id == eval_id).first()
    if not evaluation:
        raise HTTPException(404, detail="Évaluation introuvable")
    
    # Mise à jour
    evaluation.name = eval_in.name
    evaluation.type = eval_in.type
    db.commit()
    db.refresh(evaluation)
    return evaluation

@router.delete("/evaluations/{eval_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evaluation(
    eval_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))
):
    evaluation = db.query(Evaluation).filter(Evaluation.id == eval_id).first()
    if not evaluation:
        raise HTTPException(404, detail="Évaluation introuvable")
    
    # Vérifier absence notes
    if evaluation.grades:
        raise HTTPException(
            400,
            detail=f"Impossible de supprimer: {len(evaluation.grades)} note(s) liée(s)"
        )
    
    db.delete(evaluation)
    db.commit()
