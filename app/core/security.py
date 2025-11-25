# app/core/security.py
from passlib.context import CryptContext

# On configure le contexte de hachage (Bcrypt est robuste)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si le mot de passe correspond au hash en BDD"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Transforme un mot de passe en hash illisible"""
    return pwd_context.hash(password)
