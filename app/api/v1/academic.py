# app/api/v1/academic.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import User, UserRole
from app.models.academic import AcademicYear
from app.schemas.academic import AcademicYearCreate, AcademicYearUpdate, AcademicYearResponse

router = APIRouter()

@router.post("/years", response_model=AcademicYearResponse, status_code=status.HTTP_201_CREATED)
def create_year(
    year_in: AcademicYearCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    # Vérifier doublon
    existing = db.query(AcademicYear).filter(AcademicYear.name == year_in.name).first()
    if existing:
        raise HTTPException(400, detail="Cette année scolaire existe déjà")
    
    # Créer année
    new_year = AcademicYear(
        name=year_in.name,
        start_date=year_in.start_date,
        end_date=year_in.end_date,
        is_current=False
    )
    db.add(new_year)
    db.commit()
    db.refresh(new_year)
    return new_year

@router.get("/years", response_model=List[AcademicYearResponse])
def list_years(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))
):
    return db.query(AcademicYear).all()

@router.get("/years/current", response_model=AcademicYearResponse)
def get_current_year(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))
):
    current = db.query(AcademicYear).filter(AcademicYear.is_current == True).first()
    if not current:
        raise HTTPException(404, detail="Aucune année scolaire active")
    return current

@router.get("/years/{year_id}", response_model=AcademicYearResponse)
def get_year(
    year_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))
):
    year = db.query(AcademicYear).filter(AcademicYear.id == year_id).first()
    if not year:
        raise HTTPException(404, detail="Année scolaire introuvable")
    return year

@router.put("/years/{year_id}", response_model=AcademicYearResponse)
def update_year(
    year_id: int,
    year_in: AcademicYearUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    year = db.query(AcademicYear).filter(AcademicYear.id == year_id).first()
    if not year:
        raise HTTPException(404, detail="Année scolaire introuvable")
    
    # Mise à jour champs fournis
    if year_in.name:
        year.name = year_in.name
    if year_in.start_date:
        year.start_date = year_in.start_date
    if year_in.end_date:
        year.end_date = year_in.end_date
    
    db.commit()
    db.refresh(year)
    return year

@router.delete("/years/{year_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_year(
    year_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    year = db.query(AcademicYear).filter(AcademicYear.id == year_id).first()
    if not year:
        raise HTTPException(404, detail="Année scolaire introuvable")
    
    # Vérifier absence inscriptions
    if year.enrollments:
        raise HTTPException(
            400, 
            detail=f"Impossible de supprimer: {len(year.enrollments)} inscription(s) liée(s)"
        )
    
    db.delete(year)
    db.commit()

@router.put("/years/{year_id}/set-current", response_model=AcademicYearResponse)
def set_current_year(
    year_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value))
):
    year = db.query(AcademicYear).filter(AcademicYear.id == year_id).first()
    if not year:
        raise HTTPException(404, detail="Année scolaire introuvable")
    
    # Désactiver toutes les autres années
    db.query(AcademicYear).update({AcademicYear.is_current: False})
    
    # Activer celle-ci
    year.is_current = True
    db.commit()
    db.refresh(year)
    return year
