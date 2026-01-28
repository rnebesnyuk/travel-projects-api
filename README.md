# Travel Projects API

FastAPI CRUD application for managing travel projects and places.

## Features
- Create travel projects (Name required; Description/Start Date optional)
- Create a project **with places** in a single request (min 1, max 10)
- Add a place to an existing project (validated against ArtIC API)
- Update place notes and mark place as visited
- When all places are visited, the project becomes **completed**
- Prevent duplicates: the same external place cannot be added twice to the same project
- Prevent deleting a project if any of its places are visited
- List endpoints support pagination


## Tech stack

- FastAPI
- SQLAlchemy
- SQLite
- httpx (ArtIC API calls)
- Docker / docker-compose

## Get the project

Clone the repository:

```bash
git clone https://github.com/rnebesnyuk/travel-projects-api.git
cd travel-projects-api
```

## Run locally (without Docker)

1) Create and activate virtualenv, install dependencies:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```
### Start the server:

```bash
uvicorn app.main:app --reload
```
## Run with Docker

```bash
docker compose up --build
```
# Open:

http://localhost:8000/docs

(Optional UI) http://localhost:8000/
