#!/usr/bin/env python3
"""
Pydantic Data Models

Pydantic data models for structured LinkedIn profile transformation and validation.
Defines schemas for AI-inferred profiles, experiences, and education data with type safety.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel


class Education(BaseModel):
    school: str
    degree: str
    field: str


class Experience(BaseModel):
    org: str
    company_url: str
    title: str
    summary: str
    short_summary: str
    location: str
    company_skills: List[str]
    business_model: Literal["B2B", "B2C", "B2B2C", "C2C", "B2G"]
    product_type: str
    industry_tags: List[str]


class AIInferredProfile(BaseModel):
    name: str
    headline: str
    location: str
    seniority: Literal["Intern", "Entry", "Junior", "Mid", "Senior", "Lead", "Manager", "Director", "VP", "C-Level"]
    years_experience: int
    worked_at_startup: bool
    education: List[Education]
    experiences: List[Experience]