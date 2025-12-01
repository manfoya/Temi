# app/api/v1/career.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import User, UserRole
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
def create_skill(
    skill: SkillCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
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
    return db.query(Skill).all()

@router.get("/skills/{skill_id}", response_model=SkillResponse)
def get_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(404, detail="Compétence introuvable")
    return skill

@router.put("/skills/{skill_id}", response_model=SkillResponse)
def update_skill(
    skill_id: int,
    skill_in: SkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(404, detail="Compétence introuvable")
    
    skill.name = skill_in.name
    db.commit()
    db.refresh(skill)
    return skill

@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(404, detail="Compétence introuvable")
    
    # Vérifier absence liens
    if skill.domains or skill.ecues:
        raise HTTPException(
            400,
            detail="Impossible de supprimer: compétence liée à des domaines ou ECUE"
        )
    
    db.delete(skill)
    db.commit()

# 2. GESTION DES DOMAINES (Métiers)

@router.post("/domains", response_model=DomainResponse)
def create_domain(
    domain: DomainCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    new_domain = Domain(name=domain.name, description=domain.description)
    db.add(new_domain)
    db.commit()
    db.refresh(new_domain)
    return new_domain

@router.get("/domains/{domain_id}", response_model=DomainResponse)
def get_domain(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))
):
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(404, detail="Domaine introuvable")
    return domain

@router.put("/domains/{domain_id}", response_model=DomainResponse)
def update_domain(
    domain_id: int,
    domain_in: DomainCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(404, detail="Domaine introuvable")
    
    domain.name = domain_in.name
    domain.description = domain_in.description
    db.commit()
    db.refresh(domain)
    return domain

@router.delete("/domains/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_domain(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(404, detail="Domaine introuvable")
    
    # Vérifier absence utilisateurs ciblant ce domaine
    if domain.students:
        raise HTTPException(
            400,
            detail=f"Impossible de supprimer: {len(domain.students)} étudiant(s) cible(nt) ce domaine"
        )
    
    db.delete(domain)
    db.commit()

@router.post("/domains/{domain_id}/skills", response_model=DomainResponse)
def link_skills_to_domain(
    domain_id: int, 
    link: LinkSkillToDomain, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(404, detail="Domaine introuvable")
    
    skills = db.query(Skill).filter(Skill.id.in_(link.skill_ids)).all()
    
    domain.required_skills.extend(skills)
    db.commit()
    db.refresh(domain)
    return domain

@router.delete("/domains/{domain_id}/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlink_skill_from_domain(
    domain_id: int,
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(404, detail="Domaine introuvable")
    
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(404, detail="Compétence introuvable")
    
    if skill in domain.required_skills:
        domain.required_skills.remove(skill)
        db.commit()
    
# 3. LIAISON MATIÈRE -> COMPÉTENCE

@router.post("/ecues/{ecue_id}/skills", status_code=200)
def link_skills_to_ecue(
    ecue_id: int, 
    link: LinkSkillToECUE, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    ecue = db.query(ECUE).filter(ECUE.id == ecue_id).first()
    if not ecue:
        raise HTTPException(404, detail="Matière (ECUE) introuvable")
    
    skills = db.query(Skill).filter(Skill.id.in_(link.skill_ids)).all()
    
    ecue.taught_skills.extend(skills)
    db.commit()
    
    return {"message": "Compétences associées avec succès", "skills_count": len(skills)}

@router.delete("/ecues/{ecue_id}/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlink_skill_from_ecue(
    ecue_id: int,
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    ecue = db.query(ECUE).filter(ECUE.id == ecue_id).first()
    if not ecue:
        raise HTTPException(404, detail="ECUE introuvable")
    
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(404, detail="Compétence introuvable")
    
    if skill in ecue.taught_skills:
        ecue.taught_skills.remove(skill)
        db.commit()
