# app/api/v1/pedagogy.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.pedagogy import UE, ECUE, Evaluation
from app.models.academic import Filiere
from app.schemas.pedagogy import (
    UECreate, UEResponse, ECUECreate, ECUEResponse, 
    EvaluationCreate, EvaluationResponse, FiliereCreate, FiliereResponse
)

router = APIRouter()

# FILIÈRES
@router.post("/filieres", response_model=FiliereResponse, status_code=status.HTTP_201_CREATED)
def create_filiere(filiere: FiliereCreate, db: Session = Depends(get_db)):
    existing = db.query(Filiere).filter(Filiere.code == filiere.code).first()
    if existing:
        raise HTTPException(400, detail="Code filière existant")
    new_fil = Filiere(name=filiere.name, code=filiere.code)
    db.add(new_fil)
    db.commit()
    db.refresh(new_fil)
    return new_fil

# UEs
@router.post("/ues", response_model=UEResponse, status_code=status.HTTP_201_CREATED)
def create_ue(ue_in: UECreate, db: Session = Depends(get_db)):
    filiere = db.query(Filiere).filter(Filiere.code == ue_in.filiere_code).first()
    if not filiere:
        raise HTTPException(404, detail="Filière introuvable")
    
    new_ue = UE(
        filiere_id=filiere.id,
        code=ue_in.code,
        name=ue_in.name,
        credits=ue_in.credits
    )
    db.add(new_ue)
    db.commit()
    db.refresh(new_ue)
    return new_ue

@router.get("/ues", response_model=List[UEResponse])
def list_ues(filiere_code: str = None, db: Session = Depends(get_db)):
    query = db.query(UE)
    if filiere_code:
        query = query.join(Filiere).filter(Filiere.code == filiere_code)
    return query.all()

# ECUEs (Matières)
@router.post("/ecues", response_model=ECUEResponse, status_code=status.HTTP_201_CREATED)
def create_ecue(ecue_in: ECUECreate, db: Session = Depends(get_db)):
    # Validation : La somme des poids doit être proche de 1.0 (ou 100%)
    total_weight = ecue_in.weight_devoir + ecue_in.weight_tp + ecue_in.weight_examen
    if not (0.99 <= total_weight <= 1.01):
        raise HTTPException(400, detail=f"La somme des poids (Devoir+TP+Exam) doit faire 1.0 (Actuellement: {total_weight})")

    ue = db.query(UE).filter(UE.id == ecue_in.ue_id).first()
    if not ue:
        raise HTTPException(404, detail="UE introuvable")

    new_ecue = ECUE(
        ue_id=ecue_in.ue_id,
        name=ecue_in.name,
        coefficient=ecue_in.coefficient,
        competence_tag=ecue_in.competence_tag,
        # Config ENSPD
        weight_devoir=ecue_in.weight_devoir,
        weight_tp=ecue_in.weight_tp,
        weight_examen=ecue_in.weight_examen
    )
    db.add(new_ecue)
    db.commit()
    db.refresh(new_ecue)
    return new_ecue

# ÉVALUATIONS
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
