# app/main.py
from fastapi import FastAPI
from app.core.database import engine, Base
# Il faut importer les modèles pour que SQLAlchemy les détecte lors du create_all
from app.models import user, academic 

# Création des tables dans la base de données
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Temi API")

@app.get("/")
def read_root():
    return {"message": "API Temi en ligne - Tables créées"}
