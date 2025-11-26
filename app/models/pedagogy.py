# app/models/pedagogy.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class EvalType(str, enum.Enum):
    DEVOIR = "DEVOIR"
    EXAMEN = "EXAMEN"
    TP = "TP"
    PROJET = "PROJET"

class UE(Base):
    __tablename__ = "ues"
    id = Column(Integer, primary_key=True, index=True)
    filiere_id = Column(Integer, ForeignKey("filieres.id"))
    code = Column(String, unique=True, index=True) 
    name = Column(String)
    credits = Column(Float)
    
    filiere = relationship("Filiere")
    ecues = relationship("ECUE", back_populates="ue")

class ECUE(Base):
    __tablename__ = "ecues"
    id = Column(Integer, primary_key=True, index=True)
    ue_id = Column(Integer, ForeignKey("ues.id"))
    name = Column(String)
    coefficient = Column(Float) # Coeff dans l'UE
    competence_tag = Column(String, nullable=True) 

    # --- LOGIQUE ENSPD : Configuration des pondérations ---
    # L'admin définit ici : Devoirs=20%, Exam=80%. (La somme doit faire 1.0)
    weight_devoir = Column(Float, default=0.0) 
    weight_tp = Column(Float, default=0.0)
    weight_examen = Column(Float, default=1.0) # Par défaut 100% Exam
    weight_projet = Column(Float, default=0.0)

    ue = relationship("UE", back_populates="ecues")
    evaluations = relationship("Evaluation", back_populates="ecue")

class Evaluation(Base):
    """
    Si tu on a 3 Devoirs, le système fera (D1+D2+D3)/3 * weight_devoir
    """
    __tablename__ = "evaluations"
    id = Column(Integer, primary_key=True, index=True)
    ecue_id = Column(Integer, ForeignKey("ecues.id"))
    
    name = Column(String) # ex: "Devoir Surprise 1"
    type = Column(String) # DEVOIR, TP, EXAMEN...
    
    ecue = relationship("ECUE", back_populates="evaluations")
