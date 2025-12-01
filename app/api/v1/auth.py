# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash, get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, Token, AccountActivation

router = APIRouter()

# 1. LOGIN (Admin & Étudiant déjà activé)
@router.post("/login", response_model=Token)
def login(form_data: LoginRequest, db: Session = Depends(get_db)):
    # On cherche l'utilisateur par matricule
    user = db.query(User).filter(User.matricule == form_data.username).first()
    
    # Vérifications
    if not user:
        raise HTTPException(status_code=400, detail="Matricule incorrect")
    
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Mot de passe incorrect")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Compte non activé. Veuillez l'activer d'abord.")

    # Création du token
    access_token = create_access_token(data={"sub": user.matricule, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

# 2. ACTIVATION COMPTE ÉTUDIANT (Première fois)
@router.post("/activate", status_code=status.HTTP_200_OK)
def activate_account(activation_data: AccountActivation, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.matricule == activation_data.matricule).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    
    if user.is_active:
        raise HTTPException(status_code=400, detail="Ce compte est déjà activé. Connectez-vous.")

    # Vérification du secret (Date de naissance)
    # Attention : il faut que le format soit exactement le même que dans le CSV (ex: 12/12/2000)
    if user.activation_secret != activation_data.activation_secret:
        raise HTTPException(status_code=400, detail="Date de naissance (secret) incorrecte.")

    # Activation
    user.hashed_password = get_password_hash(activation_data.new_password)
    user.is_active = True
    user.activation_secret = None
    
    db.commit()
    
    return {"message": "Compte activé avec succès ! Vous pouvez vous connecter."}

# 3. PROFIL UTILISATEUR CONNECTÉ
@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "matricule": current_user.matricule,
        "nom": current_user.nom,
        "prenom": current_user.prenom,
        "role": current_user.role,
        "is_active": current_user.is_active
    }

# 4. RENOUVELLEMENT TOKEN
@router.post("/refresh", response_model=Token)
def refresh_token(current_user: User = Depends(get_current_user)):
    # Créer un nouveau token avec les infos actuelles
    new_token = create_access_token(data={"sub": current_user.matricule, "role": current_user.role})
    return {"access_token": new_token, "token_type": "bearer"}
