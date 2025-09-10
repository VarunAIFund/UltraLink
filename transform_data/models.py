from typing import List, Optional
from pydantic import BaseModel


class Education(BaseModel):
    school: str
    degree: str
    field: str


class Position(BaseModel):
    vector_embedding: str
    org: str
    title: str
    summary: str
    short_summary: str
    location: str
    industry_tags: List[str]


class AIInferredProfile(BaseModel):
    name: str
    headline: str
    location: str
    seniority: str
    skills: List[str]
    years_experience: int
    worked_at_startup: bool
    education: List[Education]
    positions: List[Position]