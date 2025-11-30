# app/main.py
from fastapi import FastAPI
from app.core.database import engine, Base
# Il faut importer les modèles pour que SQLAlchemy les détecte lors du create_all
from app.models import user, academic, pedagogy, grade, career
from app.api.v1 import users, students, pedagogy, grades, auth


# Création des tables dans la base de données
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Temi API")

# Inclusion des routes
# prefix="/api/v1" signifie que toutes les urls commenceront par ça
app.include_router(users.router, prefix="/api/v1", tags=["Utilisateurs"])
app.include_router(students.router, prefix="/api/v1/students", tags=["Étudiants"])
app.include_router(pedagogy.router, prefix="/api/v1/academic", tags=["Pédagogie (Admin)"])
app.include_router(grades.router, prefix="/api/v1/grades", tags=["Notes"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentification"])

@app.get("/")
def read_root():
    return {"message": "API Temi en ligne - Tables créées"}


