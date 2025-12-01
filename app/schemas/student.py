# app/schemas/student.py
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date

class StudentCreate(BaseModel):
    matricule: str
    full_name: str
    email: Optional[str] = None
    activation_secret: str
    
    @field_validator('matricule')
    def validate_matricule(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Le matricule est obligatoire')
        return v.strip().upper()

class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    domain_id: Optional[int] = None

class StudentResponse(BaseModel):
    id: int
    matricule: str
    full_name: str
    email: Optional[str]
    is_active: bool
    role: str
    domain_id: Optional[int]
    
    class Config:
        from_attributes = True

class EnrollmentCreate(BaseModel):
    student_matricule: str
    classe_id: int
    academic_year_id: int

class EnrollmentResponse(BaseModel):
    id: int
    student_id: int
    classe_id: int
    academic_year_id: int
    
    class Config:
        from_attributes = True
