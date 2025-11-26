# app/schemas/pedagogy.py
from pydantic import BaseModel
from typing import List, Optional
from app.models.pedagogy import EvalType

#  1. FILIÈRE (Le Domaine)
class FiliereCreate(BaseModel):
    name: str  # ex: "Statistique Appliquée"
    code: str  # ex: "STAT"

class FiliereResponse(FiliereCreate):
    id: int
    class Config:
        from_attributes = True

# 2. CLASSE (Le Niveau, ex: L3-STAT)
# C'est NOUVEAU, c'est ce qui manquait
class ClasseCreate(BaseModel):
    filiere_code: str # Pour savoir à quel domaine ça appartient
    name: str         # ex: "Licence 3 Statistique"
    code: str         # ex: "L3-STAT"
    level: str        # ex: "L3"

class ClasseResponse(ClasseCreate):
    id: int
    class Config:
        from_attributes = True

# 3. ÉVALUATIONS (Juste une Configuration simple)
class EvaluationCreate(BaseModel):
    name: str             # ex: "Devoir 1"
    type: EvalType        # DEVOIR, EXAMEN...

class EvaluationResponse(EvaluationCreate):
    id: int
    ecue_id: int
    class Config:
        from_attributes = True

# 4. ECUE (Matière)
class ECUECreate(BaseModel):
    ue_id: int
    code: str             # ex: "STAT305" (important pour le mapping IA plus tard)
    name: str             
    coefficient: float    
    credits: float        # Les ECUEs ont un coef appelé crédit
    
    # Configuration Poids (Logique ENSPD)
    weight_devoir: float = 0.0
    weight_tp: float = 0.0
    weight_examen: float = 1.0

class ECUEResponse(ECUECreate):
    id: int
    evaluations: List[EvaluationResponse] = []
    class Config:
        from_attributes = True

# 5. UE (Unité d'Enseignement)
class UECreate(BaseModel):
    classe_code: str      # On lie une UE à la CLASSE
    code: str
    name: str
    # credits: float      # facultatif mais o n peut le demander, ou le calculer par la somme des ECUEs

class UEResponse(BaseModel):
    id: int
    code: str
    name: str
    # credits: float
    ecues: List[ECUEResponse] = []
    class Config:
        from_attributes = True
