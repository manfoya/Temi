# app/api/v1/career.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.career import Skill, Domain
from app.models.pedagogy import ECUE
from app.schemas.career import (
    SkillCreate, SkillResponse, 
    DomainCreate, DomainResponse,
    LinkSkillToDomain, LinkSkillToECUE
)

router = APIRouter()

# 1. GESTION DES SKILLS (La bibliothèque)

@router.post("/skills", response_model=SkillResponse)
def create_skill(skill: SkillCreate, db: Session = Depends(get_db)):
    """Ajouter une compétence à la liste globale (ex: Python)"""
    exists = db.query(Skill).filter(Skill.name == skill.name).first()
    if exists:
        raise HTTPException(400, detail="Cette compétence existe déjà")
    
    new_skill = Skill(name=skill.name)
    db.add(new_skill)
    db.commit()
    db.refresh(new_skill)
    return new_skill

@router.get("/skills", response_model=List[SkillResponse])
def list_skills(db: Session = Depends(get_db)):
    """Récupérer la liste pour le menu déroulant"""
    return db.query(Skill).all()

# 2. GESTION DES DOMAINES (Métiers)

@router.post("/domains", response_model=DomainResponse)
def create_domain(domain: DomainCreate, db: Session = Depends(get_db)):
    """Créer un métier cible (ex: Data Scientist)"""
    new_domain = Domain(name=domain.name, description=domain.description)
    db.add(new_domain)
    db.commit()
    db.refresh(new_domain)
    return new_domain

@router.post("/domains/{domain_id}/skills", response_model=DomainResponse)
def link_skills_to_domain(domain_id: int, link: LinkSkillToDomain, db: Session = Depends(get_db)):
    """Définir ce qu'il faut savoir pour faire ce métier"""
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(404, detail="Domaine introuvable")
    
    # On récupère les skills via leurs IDs
    skills = db.query(Skill).filter(Skill.id.in_(link.skill_ids)).all()
    
    # On remplace ou on ajoute ? Ici on étend la liste
    domain.required_skills.extend(skills)
    db.commit()
    db.refresh(domain)
    return domain

# 3. LIAISON MATIÈRE -> COMPÉTENCE
# C'est ici que l'Admin dit "Ce cours enseigne Python"

@router.post("/ecues/{ecue_id}/skills", status_code=200)
def link_skills_to_ecue(ecue_id: int, link: LinkSkillToECUE, db: Session = Depends(get_db)):
    """Taguer une matière avec des compétences"""
    ecue = db.query(ECUE).filter(ECUE.id == ecue_id).first()
    if not ecue:
        raise HTTPException(404, detail="Matière (ECUE) introuvable")
    
    skills = db.query(Skill).filter(Skill.id.in_(link.skill_ids)).all()
    
    # On ajoute les skills à la matière
    ecue.taught_skills.extend(skills)
    db.commit()
    
    return {"message": "Compétences associées avec succès", "skills_count": len(skills)}
