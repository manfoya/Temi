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
    classe_id = Column(Integer, ForeignKey("classes.id")) # Lié à la CLASSE (L3-STAT)
    
    code = Column(String, index=True) # ex: UE-MATH
    name = Column(String)
    # Les crédits de l'UE sont la somme, mais on peut garder ce champ pour l'affichage
    credits = Column(Float, default=0.0) 
    
    # IMPORTANT : Il faut faire un import différé pour éviter les boucles
    classe = relationship("app.models.academic.Classe", back_populates="ues")
    ecues = relationship("ECUE", back_populates="ue")

class ECUE(Base):
    __tablename__ = "ecues"
    id = Column(Integer, primary_key=True, index=True)
    ue_id = Column(Integer, ForeignKey("ues.id"))
    
    code = Column(String, index=True) # ex: STAT301 (Important pour le mapping IA plus tard)
    name = Column(String)
    
    # L'ECUE a des crédits
    credits = Column(Float, default=0.0) 
    coefficient = Column(Float, default=1.0) # Poids dans la moyenne

    # Configur Pondération (Système ENSPD)
    weight_devoir = Column(Float, default=0.0) 
    weight_tp = Column(Float, default=0.0)
    weight_examen = Column(Float, default=1.0)

    ue = relationship("UE", back_populates="ecues")
    evaluations = relationship("Evaluation", back_populates="ecue")

class Evaluation(Base):
    __tablename__ = "evaluations"
    id = Column(Integer, primary_key=True, index=True)
    ecue_id = Column(Integer, ForeignKey("ecues.id"))
    
    name = Column(String)
    type = Column(String) # DEVOIR, EXAMEN...
    
    ecue = relationship("ECUE", back_populates="evaluations")
