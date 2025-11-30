# app/schemas/career.py

from pydantic import BaseModel
from typing import List, Optional

# SKILLS (Compétences)
class SkillCreate(BaseModel):
    name: str # ex: "Python"

class SkillResponse(SkillCreate):
    id: int
    class Config:
        from_attributes = True

#DOMAINS (Métiers)
class DomainCreate(BaseModel):
    name: str # ex: "Data Scientist"
    description: Optional[str] = None

class DomainResponse(DomainCreate):
    id: int
    required_skills: List[SkillResponse] = []
    class Config:
        from_attributes = True

#LIAISONS
class LinkSkillToDomain(BaseModel):
    skill_ids: List[int] # Liste des IDs à lier

class LinkSkillToECUE(BaseModel):
    skill_ids: List[int] # Liste des IDs à lier à la matière
