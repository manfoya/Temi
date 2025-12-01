# app/schemas/academic.py
from pydantic import BaseModel, field_validator
from datetime import date
import re

class AcademicYearCreate(BaseModel):
    name: str
    start_date: date
    end_date: date
    
    @field_validator('name')
    def validate_name_format(cls, v):
        if not re.match(r'^\d{4}-\d{4}$', v):
            raise ValueError('Le nom doit être au format YYYY-YYYY (ex: 2024-2025)')
        
        start_year, end_year = v.split('-')
        if int(end_year) != int(start_year) + 1:
            raise ValueError('L\'année de fin doit être l\'année de début + 1')
        
        return v
    
    @field_validator('end_date')
    def validate_dates(cls, v, info):
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('La date de fin doit être après la date de début')
        return v

class AcademicYearUpdate(BaseModel):
    name: str = None
    start_date: date = None
    end_date: date = None
    
    @field_validator('name')
    def validate_name_format(cls, v):
        if v is None:
            return v
        if not re.match(r'^\d{4}-\d{4}$', v):
            raise ValueError('Le nom doit être au format YYYY-YYYY (ex: 2024-2025)')
        
        start_year, end_year = v.split('-')
        if int(end_year) != int(start_year) + 1:
            raise ValueError('L\'année de fin doit être l\'année de début + 1')
        
        return v

class AcademicYearResponse(BaseModel):
    id: int
    name: str
    start_date: date
    end_date: date
    is_current: bool
    
    class Config:
        from_attributes = True