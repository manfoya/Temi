# app/schemas/auth.py
from pydantic import BaseModel

# Pour recevoir le token
class Token(BaseModel):
    access_token: str
    token_type: str

# Pour la demande de connexion (ce sera un Login classique)
class LoginRequest(BaseModel):
    username: str # Ce sera le matricule
    password: str  # L'utilisateur le d&finit de lui même

# Pour l'activation du compte étudiant
class AccountActivation(BaseModel):
    matricule: str
    activation_secret: str # La date de naissance (ex: 12/12/2000)
    new_password: str
