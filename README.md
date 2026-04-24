# Group-21

John Asobayire - 22035

Armaan Arellano - ara23025

Parker Pretty - pgp22001

Tanya Parra-Sanchez - tps20005

Project Board:
https://trello.com/invite/b/698e2401d961fa175dfd93cb/ATTI0aafb4599c5be319bcd05eab7bbbee941CE01B78/kanban-example

Figma:
https://www.figma.com/design/WC4H5oVfW1L2QGnOgPAOV9/Untitled?node-id=0-1&t=dCUMJoSnfAYyCXJ7-1

## Run With Docker

From the repo root:

```bash
docker compose up --build
```

Open the frontend at:

```text
http://localhost:5173
```

The backend API runs at:

```text
http://localhost:8000
```

Swagger docs are available at:

```text
http://localhost:8000/apidocs/
```

To stop the containers:

```bash
docker compose down
```


- The backend uses SQLite and initializes the database through `backend.init_db`.
- The backend Docker image is named `team21-backend`.
- The frontend and backend are run together through `docker compose`.
- The frontend is a React SPA in the `frontend` folder.
- The backend Swagger UI is available at `/apidocs/`.