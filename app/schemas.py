from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict


# ---------- Places ----------
class PlaceImport(BaseModel):
    external_id: int = Field(..., gt=0)
    notes: str | None = None


class PlaceCreate(BaseModel):
    external_id: int = Field(..., gt=0)
    notes: str | None = None


class PlaceUpdate(BaseModel):
    notes: str | None = None
    visited: bool | None = None


class PlaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: int
    notes: str | None
    visited: bool
    created_at: datetime


# ---------- Projects ----------
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    start_date: date | None = None
    places: list[PlaceImport] | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    start_date: date | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    start_date: date | None
    status: str
    created_at: datetime
    places: list[PlaceOut] = []


class ProjectListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: str
    start_date: date | None
    created_at: datetime