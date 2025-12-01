# app/schemas/grade.py
from pydantic import BaseModel, validator
from typing import Optional, Any

class GradeCreate(BaseModel):
    student_matricule: str # Plus facile pour l'admin que de chercher l'ID enrollment
    evaluation_id: int
    value: float

    @validator('value')
    def validate_note(cls, v):
        if not (0 <= v <= 20):
            raise ValueError('La note doit être comprise entre 0 et 20')
        return v

class GradeUpdate(BaseModel):
    value: float

    @validator('value')
    def validate_note(cls, v):
        if not (0 <= v <= 20):
            raise ValueError('La note doit être comprise entre 0 et 20')
        return v

class GradeResponse(BaseModel):
    id: int
    student_name: str
    evaluation_name: str
    value: float
    ai_diagnostic: Optional[Any] = None  # Diagnostic IA automatique
    
    class Config:
        from_attributes = True
