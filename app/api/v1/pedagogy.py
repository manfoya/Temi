# app/api/v1/pedagogy.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
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

# 1. GESTION DES FILIÈRES (Domaines)
@router.post("/filieres", response_model=FiliereResponse, status_code=status.HTTP_201_CREATED)
def create_filiere(filiere: FiliereCreate, db: Session = Depends(get_db)):
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

# 2. GESTION DES CLASSES (Niveaux, ex: L3-STAT)
@router.post("/classes", response_model=ClasseResponse, status_code=status.HTTP_201_CREATED)
def create_classe(classe_in: ClasseCreate, db: Session = Depends(get_db)):
    # On vérifie que la Filière parente existe
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
        query = query.join(Filiere).filter(Filiere.code == filiere_code)
    return query.all()

# 3. GESTION DES UEs
@router.post("/ues", response_model=UEResponse, status_code=status.HTTP_201_CREATED)
def create_ue(ue_in: UECreate, db: Session = Depends(get_db)):
    # On lie l'UE à une CLASSE désormais
    classe = db.query(Classe).filter(Classe.code == ue_in.classe_code).first()
    if not classe:
        raise HTTPException(404, detail=f"Classe {ue_in.classe_code} introuvable")
    
    new_ue = UE(
        classe_id=classe.id,
        code=ue_in.code,
        name=ue_in.name,
        # credits=ue_in.credits # Optionnel si on veut le stocker dans l'UE
    )
    db.add(new_ue)
    db.commit()
    db.refresh(new_ue)
    new_ue.classe_code = classe.code
    return new_ue

# 4. GESTION DES ECUEs (Matières)
@router.post("/ecues", response_model=ECUEResponse, status_code=status.HTTP_201_CREATED)
def create_ecue(ecue_in: ECUECreate, db: Session = Depends(get_db)):
    # Validation ENSPD : La somme des poids doit être 1.0 (ou 100%)
    # On inclut le projet si jamais il y en a un
    # Note: comme ECUECreate a des valeurs par défaut à 0.0, pas de souci si projet n'est pas fourni
    weight_projet = getattr(ecue_in, 'weight_projet', 0.0) 
    total_weight = ecue_in.weight_devoir + ecue_in.weight_tp + ecue_in.weight_examen + weight_projet
    
    # On accepte une petite marge d'erreur flottante (0.99 - 1.01)
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
        # Config ENSPD
        weight_devoir=ecue_in.weight_devoir,
        weight_tp=ecue_in.weight_tp,
        weight_examen=ecue_in.weight_examen
    )
    db.add(new_ecue)
    db.commit()
    db.refresh(new_ecue)
    return new_ecue

# 5. GESTION DES ÉVALUATIONS 
@router.post("/ecues/{ecue_id}/evaluations", response_model=EvaluationResponse)
def add_evaluation(ecue_id: int, eval_in: EvaluationCreate, db: Session = Depends(get_db)):
    """Ajouter une épreuve (ex: Devoir 1)"""
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
