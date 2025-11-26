# app/schemas/pedagogy.py
from pydantic import BaseModel
from typing import List, Optional
from app.models.pedagogy import EvalType

# FILIÈRE
class FiliereCreate(BaseModel):
    name: str 
    code: str 
class FiliereResponse(FiliereCreate):
    id: int
    class Config:
        from_attributes = True

# ÉVALUATIONS (L'épreuve simple) 
class EvaluationCreate(BaseModel):
    name: str             # ex: "Devoir 1"
    type: EvalType        # DEVOIR

class EvaluationResponse(EvaluationCreate):
    id: int
    ecue_id: int
    class Config:
        from_attributes = True

# ECUE (Matière avec Config Poids)
class ECUECreate(BaseModel):
    ue_id: int
    name: str             
    coefficient: float    
    competence_tag: Optional[str] = None
    # Config ENSPD
    weight_devoir: float = 0.0
    weight_tp: float = 0.0
    weight_examen: float = 1.0

class ECUEResponse(ECUECreate):
    id: int
    evaluations: List[EvaluationResponse] = []
    class Config:
        from_attributes = True

# UE
class UECreate(BaseModel):
    filiere_code: str
    code: str
    name: str
    credits: float

class UEResponse(BaseModel):
    id: int
    code: str
    name: str
    credits: float
    ecues: List[ECUEResponse] = []
    class Config:
        from_attributes = True
