from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

from .db import Base, engine, get_db
from . import schemas
from . import services

app = FastAPI(title="Travel Projects API")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

Base.metadata.create_all(bind=engine)

@app.get("/", response_class=HTMLResponse)
def ui_projects(request: Request):
    return templates.TemplateResponse("projects.html", {"request": request})


@app.get("/projects/{project_id}/ui", response_class=HTMLResponse)
def ui_project_details(project_id: int, request: Request):
    return templates.TemplateResponse("project.html", {"request": request, "project_id": project_id})

# ---------- Projects ----------
@app.post("/projects", response_model=schemas.ProjectOut, status_code=201)
async def create_project(payload: schemas.ProjectCreate, db: Session = Depends(get_db)):
    project = await services.create_project(
        db=db,
        name=payload.name,
        description=payload.description,
        start_date=payload.start_date,
        places_payload=payload.places,
    )
    return project


@app.get("/projects", response_model=list[schemas.ProjectListOut])
def get_projects(db: Session = Depends(get_db)):
    return services.list_projects(db)


@app.get("/projects/{project_id}", response_model=schemas.ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = services.get_project_or_404(db, project_id)
    return project


@app.patch("/projects/{project_id}", response_model=schemas.ProjectOut)
def patch_project(project_id: int, payload: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    project = services.get_project_or_404(db, project_id)
    project = services.update_project(
        db,
        project,
        name=payload.name,
        description=payload.description,
        start_date=payload.start_date,
    )
    return project


@app.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = services.get_project_or_404(db, project_id)
    services.delete_project(db, project)
    return None


# ---------- Places ----------
@app.post("/projects/{project_id}/places", response_model=schemas.PlaceOut, status_code=201)
async def add_place(project_id: int, payload: schemas.PlaceCreate, db: Session = Depends(get_db)):
    project = services.get_project_or_404(db, project_id)
    place = await services.add_place_to_project(
        db=db,
        project=project,
        external_id=payload.external_id,
        notes=payload.notes,
    )
    return place


@app.get("/projects/{project_id}/places", response_model=list[schemas.PlaceOut])
def get_places(project_id: int, db: Session = Depends(get_db)):
    project = services.get_project_or_404(db, project_id)
    return services.list_places(db, project)


@app.get("/projects/{project_id}/places/{place_id}", response_model=schemas.PlaceOut)
def get_place(project_id: int, place_id: int, db: Session = Depends(get_db)):
    _ = services.get_project_or_404(db, project_id)
    place = services.get_place_or_404(db, project_id, place_id)
    return place


@app.patch("/projects/{project_id}/places/{place_id}", response_model=schemas.PlaceOut)
def patch_place(project_id: int, place_id: int, payload: schemas.PlaceUpdate, db: Session = Depends(get_db)):
    project = services.get_project_or_404(db, project_id)
    place = services.get_place_or_404(db, project_id, place_id)
    place = services.update_place(
        db=db,
        project=project,
        place=place,
        notes=payload.notes,
        visited=payload.visited,
    )
    return place