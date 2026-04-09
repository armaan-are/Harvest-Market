# Group-21

John Asobayire - 22035

Armaan Arellano - ara23025

Parker Pretty - pgp22001

Tanya Parra-Sanchez - tps20005

Project Board:
https://trello.com/invite/b/698e2401d961fa175dfd93cb/ATTI0aafb4599c5be319bcd05eab7bbbee941CE01B78/kanban-example

Figma:
https://www.figma.com/design/WC4H5oVfW1L2QGnOgPAOV9/Untitled?node-id=0-1&t=dCUMJoSnfAYyCXJ7-1

## Backend Setup For TA

The backend now uses SQLite. The database file is created locally at `backend/data/team21_market.db` and is ignored by git.

### 1. Run the database initialization code

From the repo root:

```bash
python3 -m backend.init_db
```

This creates the SQLite schema and starter data if the database does not already exist.

### 2. Start the backend directly

Install backend dependencies:

```bash
python3 -m pip install -r backend/requirements.txt
```

Initialize the database:

```bash
python3 -m backend.init_db
```

Start the Flask backend:

```bash
python3 -m backend.main
```

The backend runs on `http://localhost:8000`.

Swagger UI is available at:

```text
http://localhost:8000/apidocs
```

### 3. Start the backend with Docker

Build and run the backend container:

```bash
docker compose up --build backend
```

The backend Docker image is named `Team21-backend`.

The container command initializes the SQLite database and then starts the API server automatically.

### 4. Run backend tests

From the repo root:

```bash
python3 -m pytest backend/tests
```

### 5. Run pylint

From the repo root:

```bash
PYLINTHOME=/tmp/pylint python3 -m pylint backend
```
