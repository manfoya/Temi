# app/models/academic.py
from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class AcademicYear(Base):
    __tablename__ = "academic_years"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_current = Column(Boolean, default=False)
    enrollments = relationship("Enrollment", back_populates="academic_year")

class Filiere(Base):
    """
    Le Département / La Spécialité.
    Ex: 'Statistique Appliquée', 'Planification'
    """
    __tablename__ = "filieres"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True) # "Statistique Appliquée"
    code = Column(String, unique=True) # "STAT"
    
    classes = relationship("Classe", back_populates="filiere")

class Classe(Base):
    """
    La Classe réelle où on inscrit les élèves.
    Ex: 'L3-STAT'
    """
    __tablename__ = "classes"
    id = Column(Integer, primary_key=True, index=True)
    filiere_id = Column(Integer, ForeignKey("filieres.id"))
    
    name = Column(String) # "Licence 3 Statistique"
    code = Column(String, unique=True) # "L3-STAT" (C'est ce code qu'on utilisera dans l'import Excel)
    level = Column(String) # "L1", "L2", "L3", "M1"...
    
    filiere = relationship("Filiere", back_populates="classes")
    enrollments = relationship("Enrollment", back_populates="classe")
    ues = relationship("app.models.pedagogy.UE", back_populates="classe") # Les UEs sont liées à une classe
