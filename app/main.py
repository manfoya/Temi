# app/main.py
from fastapi import FastAPI
from app.core.database import engine, Base
# Il faut importer les modèles pour que SQLAlchemy les détecte lors du create_all
from app.models import user, academic
from app.api.v1 import users, students


# Création des tables dans la base de données
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Temi API")

# Inclusion des routes
# prefix="/api/v1" signifie que toutes les urls commenceront par ça
app.include_router(users.router, prefix="/api/v1", tags=["Utilisateurs"])
app.include_router(students.router, prefix="/api/v1/students", tags=["Étudiants"])

@app.get("/")
def read_root():
    return {"message": "API Temi en ligne - Tables créées"}


