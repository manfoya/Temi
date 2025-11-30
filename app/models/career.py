# app/models/career.py
from sqlalchemy import Column, Integer, String, ForeignKey, Table, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

#TABLES DE LIAISON (Le Graphe)

# 1. Qu'est-ce qu'un Domaine demande comme Compétence ?
# Ex: Data Science -> Python
domain_skill_association = Table(
    'domain_skills', Base.metadata,
    Column('domain_id', Integer, ForeignKey('domains.id')),
    Column('skill_id', Integer, ForeignKey('skills.id'))
)

# 2. Qu'est-ce qu'une Matière (ECUE) enseigne comme Compétence ?
# Ex: "Informatique L2" -> Python
# C'est le pont entre le Pédagogique (Module 2) et l'IA (Module 4)
ecue_skill_association = Table(
    'ecue_skills', Base.metadata,
    Column('ecue_id', Integer, ForeignKey('ecues.id')),
    Column('skill_id', Integer, ForeignKey('skills.id'))
)

#LES ENTITÉS

class Domain(Base):
    """
    La Cible Métier / Domaine (ex: Data Scientist, Actuaire)
    """
    __tablename__ = "domains"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True) # Utile pour le prompt Gemini

    # Relation : Un domaine requiert plusieurs compétences
    required_skills = relationship("Skill", secondary=domain_skill_association, back_populates="domains")

class Skill(Base):
    """
    L'Atome de connaissance (ex: Python, Probabilités, Droit)
    C'est l'unité de mesure de l'écart (en anglais Gap Analysis).
    """
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) # ex: "Programmation Python"
    
    domains = relationship("Domain", secondary=domain_skill_association, back_populates="required_skills")
    
    # Relation inverse : Quelles matières enseignent ça ?
    # Note: On utilise une string pour 'ECUE' pour éviter les imports circulaires immédiats
    ecues = relationship("app.models.pedagogy.ECUE", secondary=ecue_skill_association, backref="taught_skills")
