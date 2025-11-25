# app/models/academic.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

class AcademicYear(Base):
    __tablename__ = "academic_years"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)  # ex: "2024-2025"
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    is_current = Column(Boolean, default=False)  # Une seule année active à la fois

    # Relation avec les inscriptions (Un étudiant s'inscrit pour une année)
    enrollments = relationship("Enrollment", back_populates="academic_year")


class Filiere(Base):
    __tablename__ = "filieres"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)  # ex: "Statistique Appliquée L3"
    code = Column(String, unique=True, index=True)  # ex: "STAT-L3" (Code court pour admin)
    
    # Relation avec les inscriptions
    enrollments = relationship("Enrollment", back_populates="filiere")
