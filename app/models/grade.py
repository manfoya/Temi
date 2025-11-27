# app/models/grade.py
from sqlalchemy import Column, Integer, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    
    # Qui ? (L'étudiant inscrit cette année-là)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=False)
    
    # Quoi ? (Le Devoir 1, l'Examen, etc.)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id"), nullable=False)
    
    # Combien ?
    value = Column(Float, nullable=False) # ex: 14.5
    
    # Sécurité : Un étudiant ne peut avoir qu'une seule note pour une même épreuve
    __table_args__ = (UniqueConstraint('enrollment_id', 'evaluation_id', name='_student_eval_uc'),)

    enrollment = relationship("app.models.user.Enrollment", backref="grades")
    evaluation = relationship("app.models.pedagogy.Evaluation")
