# app/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserRole

# 1. Ce qui est commun à tout le monde
class UserBase(BaseModel):
    matricule: str
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

# 2. Ce qu'on envoie pour CRÉER un Admin (Le mot de passe est obligatoire)
class AdminCreate(UserBase):
    password: str

# 3. Ce que l'API renvoie après création (On ne renvoie JAMAIS le mot de passe)
class UserResponse(UserBase):
    id: int
    is_active: bool
    role: UserRole

    class Config:
        # Permet à Pydantic de lire les objets SQLAlchemy
        from_attributes = True
