# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.models import user, academic, pedagogy, grade, career, notification
from app.api.v1 import users, students, pedagogy, grades, auth, career, advisor, academic as academic_routes, notifications

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Temi API")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api/v1", tags=["Utilisateurs"])
app.include_router(students.router, prefix="/api/v1/students", tags=["Étudiants"])
app.include_router(pedagogy.router, prefix="/api/v1/academic", tags=["Pédagogie (Admin)"])
app.include_router(academic_routes.router, prefix="/api/v1/academic", tags=["Années Scolaires"])
app.include_router(grades.router, prefix="/api/v1/grades", tags=["Notes"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentification"])
app.include_router(career.router, prefix="/api/v1/career", tags=["Carrière & IA"])
app.include_router(advisor.router, prefix="/api/v1/advisor", tags=["IA & Coaching"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])

@app.get("/")
def read_root():
    return {"message": "API Temi en ligne"}

