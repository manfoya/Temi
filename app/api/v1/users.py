# app/api/v1/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import AdminCreate, UserResponse
from app.core.security import get_password_hash

router = APIRouter()

@router.post("/admins", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_admin(user_in: AdminCreate, db: Session = Depends(get_db)):
    """
    Permet au SuperAdmin de créer un administrateur Scolarité.
    """
    # 1. Vérifier si le matricule existe déjà
    user_exists = db.query(User).filter(User.matricule == user_in.matricule).first()
    if user_exists:
        raise HTTPException(
            status_code=400,
            detail="Un utilisateur avec ce matricule existe déjà."
        )

    # 2. Vérifier si l'email existe déjà (si fourni)
    if user_in.email:
        email_exists = db.query(User).filter(User.email == user_in.email).first()
        if email_exists:
            raise HTTPException(
                status_code=400,
                detail="Cet email est déjà utilisé."
            )

    # 3. Création de l'objet User
    new_admin = User(
        matricule=user_in.matricule,
        full_name=user_in.full_name,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password), # On hache ici
        role=UserRole.ADMIN, # On force le rôle ADMIN
        is_active=True # Un admin créé par le SuperAdmin est actif direct
    )

    # 4. Sauvegarde
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return new_admin
