# Group-21 Local Farm Marketplace

Team members:

- John Asobayire - 22035
- Armaan Arellano - ara23025
- Parker Pretty - pgp22001
- Tanya Parra-Sanchez - tps20005

Project Board:
https://trello.com/invite/b/698e2401d961fa175dfd93cb/ATTI0aafb4599c5be319bcd05eab7bbbee941CE01B78/kanban-example

Figma:
https://www.figma.com/design/WC4H5oVfW1L2QGnOgPAOV9/Untitled?node-id=0-1&t=dCUMJoSnfAYyCXJ7-1

## Project Overview

This project is a three-tier local farm marketplace for neighbors and small farms. Buyers can browse local inventory, request pickup orders, message sellers, track order status, and submit verified reviews. Sellers can manage listings, upload product images, maintain farm profile details, and approve or reject incoming order requests.

The application uses:

- React SPA frontend
- Python Flask JSON API backend
- SQLite database
- Docker Compose for local deployment
- GitHub Actions for linting, testing, and frontend builds

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

The backend container initializes SQLite automatically through `backend.init_db`.

## Run Locally Without Docker

Backend:

```bash
python3 -m pip install -r backend/requirements.txt
python3 -m backend.init_db
python3 -m backend.main
```

Frontend, from a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Then open:

```text
http://localhost:5173
```

## Demo Accounts

Buyer:

```text
buyer@example.com
buyerpass
```

Seller:

```text
seller@example.com
sellerpass
```

Additional seeded accounts:

```text
neighbor.jules@example.com / buyerpass
orchard.collective@example.com / sellerpass
```

## Verification Commands

Backend tests:

```bash
python3 -m pytest backend/tests
```

Frontend lint:

```bash
cd frontend
npm run lint
```

Frontend production build:

```bash
cd frontend
npm run build
```

## Implemented Requirements

- Dual buyer and seller roles
- Registration and login with salted password hashes and stored random session tokens
- Buyer profile with contact information and home zip code
- Farm profile with farm name, biography, pickup address, operating hours, and zip code
- Seller product CRUD
- Product categories: Produce, Dairy, Meat, Baked Goods
- Zip-code marketplace filtering
- Product image upload endpoint and frontend file upload flow
- Pending, Confirmed, Ready for Pickup, Completed, Rejected, and Cancelled order lifecycle
- Buyer "My Orders" dashboard
- Seller "Incoming Requests" dashboard
- Inventory reservation and release logic for pending, rejected, and cancelled orders
- Product-linked messaging
- Verified reviews restricted to completed buyer orders
- Role checks on protected backend routes
- React Router SPA navigation
- Swagger API documentation
- Backend pytest coverage and frontend lint/build CI steps

## Demo Flow

Recommended buyer flow:

1. Log in as `buyer@example.com`.
2. Open Profile and confirm the home zip code.
3. Browse Market, filter by category or zip code, and request pickup for a product.
4. Open Orders and confirm the new order is pending.
5. Open Messages from a product card and send a product-linked message.
6. Open Reviews and submit feedback for an existing completed order.

Recommended seller flow:

1. Log in as `seller@example.com`.
2. Open Profile and confirm farm public details.
3. Open Market and create or edit a listing with an uploaded image.
4. Open Orders / Incoming Requests.
5. Approve a pending order, mark it ready for pickup, and complete it.

## Known Limitations

- Zip filtering uses exact zip-code matching, not geographic radius distance.
- Pickup scheduling is captured as a requested pickup window text field rather than a fixed time-slot calendar.
- Uploaded images are stored in the backend container filesystem for local demo use.
- Payment processing is intentionally not implemented because the required transaction model is pickup approval, not instant checkout.

## Extra Credit

No extra credit features are included in this submission.

The project does not attempt:

- Circuit Breaker pattern
- OAuth login with Auth0
- AWS cloud deployment

## AI / Vibe Coding Usage

AI assistance was used for implementation support, refactoring, debugging, documentation drafting, and final polish. The team remained responsible for understanding, reviewing, testing, and submitting the code. AI assistance was not used as a substitute for team review or for bypassing the project requirements.
