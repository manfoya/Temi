# app/models/user.py
import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

# On définit les rôles possibles
class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    STUDENT = "STUDENT"

class User(Base):
    """
    L'utilisateur physique (Persistant dans le temps).
    Identifié par son MATRICULE.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    matricule = Column(String, unique=True, index=True) # L'identifiant unique invariant
    
    hashed_password = Column(String)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=False) # False tant que le compte n'est pas activé
    role = Column(String, default=UserRole.STUDENT)
    
    # Secret pour l'activation (ex: Date de naissance ou Code fourni par l'admin)
    activation_secret = Column(String, nullable=True)

    # Un User peut avoir plusieurs Inscriptions (une par an)
    enrollments = relationship("Enrollment", back_populates="student")


class Enrollment(Base):
    """
    L'identité 'Scolaire' pour une année donnée.
    C'est à CA que les notes seront attachées.
    """
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    
    student_id = Column(Integer, ForeignKey("users.id"))
    classe_id = Column(Integer, ForeignKey("classes.id"))
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"))

    # Sécurité : Un étudiant ne peut être inscrit qu'une seule fois dans une année
    __table_args__ = (UniqueConstraint('student_id', 'academic_year_id', name='_student_year_uc'),)

    student = relationship("User", back_populates="enrollments")
    classe = relationship("app.models.academic.Classe", back_populates="enrollments")
    academic_year = relationship("AcademicYear", back_populates="enrollments")
