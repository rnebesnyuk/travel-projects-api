from sqlalchemy.orm import Session
from sqlalchemy import select, func, exists

from fastapi import HTTPException, status

from . import models
from .artic_client import artwork_exists, ArticError


MAX_PLACES_PER_PROJECT = 10
MIN_PLACES_PER_PROJECT = 1


def _recalc_project_status(db: Session, project: models.Project) -> None:
    """
    If all places visited and project has at least 1 place => completed, else active.
    """
    total = db.scalar(
        select(func.count(models.ProjectPlace.id)).where(models.ProjectPlace.project_id == project.id)
    ) or 0

    if total == 0:
        project.status = "active"
        return

    unvisited = db.scalar(
        select(func.count(models.ProjectPlace.id)).where(
            models.ProjectPlace.project_id == project.id,
            models.ProjectPlace.visited.is_(False),
        )
    ) or 0

    project.status = "completed" if unvisited == 0 else "active"


def get_project_or_404(db: Session, project_id: int) -> models.Project:
    project = db.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def get_place_or_404(db: Session, project_id: int, place_id: int) -> models.ProjectPlace:
    place = db.get(models.ProjectPlace, place_id)
    if not place or place.project_id != project_id:
        raise HTTPException(status_code=404, detail="Place not found in this project")
    return place


async def create_project(db: Session, name: str, description, start_date, places_payload):
    project = models.Project(name=name, description=description, start_date=start_date)

    if not places_payload or len(places_payload) < MIN_PLACES_PER_PROJECT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project must include at least {MIN_PLACES_PER_PROJECT} place(s)",
        )
    if len(places_payload) > MAX_PLACES_PER_PROJECT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project cannot have more than {MAX_PLACES_PER_PROJECT} places",
        )

    external_ids = [p.external_id for p in places_payload]
    if len(set(external_ids)) != len(external_ids):
        raise HTTPException(status_code=409, detail="Duplicate external_id in request")

    try:
        for ext_id in external_ids:
            if not await artwork_exists(ext_id):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"External place {ext_id} not found in ArtIC",
                )
    except ArticError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Attach places
    for p in places_payload:
        project.places.append(models.ProjectPlace(external_id=p.external_id, notes=p.notes))

    _recalc_project_status(db, project)

    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def list_projects(db: Session, limit: int, offset: int):
    stmt = (
        select(models.Project)
        .order_by(models.Project.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return db.scalars(stmt).all()


def update_project(db: Session, project: models.Project, name, description, start_date):
    if name is not None:
        project.name = name
    if description is not None:
        project.description = description
    if start_date is not None:
        project.start_date = start_date

    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project: models.Project):
    has_visited = db.scalar(
        select(
            exists().where(
                models.ProjectPlace.project_id == project.id,
                models.ProjectPlace.visited.is_(True),
            )
        )
    )
    if has_visited:
        raise HTTPException(
            status_code=409,
            detail="Project cannot be deleted because it has visited places",
        )

    db.delete(project)
    db.commit()


async def add_place_to_project(db: Session, project: models.Project, external_id: int, notes: str | None):
    current_count = db.scalar(
        select(func.count(models.ProjectPlace.id)).where(models.ProjectPlace.project_id == project.id)
    ) or 0
    if current_count >= MAX_PLACES_PER_PROJECT:
        raise HTTPException(
            status_code=409,
            detail=f"Project cannot have more than {MAX_PLACES_PER_PROJECT} places",
        )

    duplicate = db.scalar(
        select(
            exists().where(
                models.ProjectPlace.project_id == project.id,
                models.ProjectPlace.external_id == external_id,
            )
        )
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="This external place is already in the project")

    try:
        if not await artwork_exists(external_id):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"External place {external_id} not found in ArtIC",
            )
    except ArticError as e:
        raise HTTPException(status_code=502, detail=str(e))

    place = models.ProjectPlace(project_id=project.id, external_id=external_id, notes=notes)
    db.add(place)
    db.commit()
    db.refresh(place)

    _recalc_project_status(db, project)
    db.commit()
    db.refresh(project)

    return place


def list_places(db: Session, project: models.Project, limit: int, offset: int):
    stmt = (
        select(models.ProjectPlace)
        .where(models.ProjectPlace.project_id == project.id)
        .order_by(models.ProjectPlace.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return db.scalars(stmt).all()


def update_place(db: Session, project: models.Project, place: models.ProjectPlace, notes, visited):
    if notes is not None:
        place.notes = notes
    if visited is not None:
        place.visited = visited

    db.commit()
    db.refresh(place)

    _recalc_project_status(db, project)
    db.commit()
    db.refresh(project)

    return place