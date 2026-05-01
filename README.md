# Harvest Market

Harvest Market is a full-stack local food marketplace for connecting neighborhood buyers with independent farms and small producers. It supports the core workflow a real pickup-based marketplace needs: buyers discover nearby inventory, place pickup requests, message sellers, track fulfillment, and leave verified reviews; sellers manage farm profiles, product listings, inventory, order decisions, and customer communication from one dashboard.

The app is built as a React single-page application backed by a Flask JSON API and a SQLite persistence layer. It is designed for a clean local developer workflow with Docker Compose, seeded demo data, Swagger API documentation, and focused backend/frontend verification commands.

## Technical Stack

- Frontend: React 19, React Router 7, Vite 7, ESLint
- Backend: Python 3, Flask 3, Flasgger / Swagger UI
- Database: SQLite with deterministic initialization and seed data
- Authentication: local email/password sessions, optional Auth0 OAuth integration
- Deployment workflow: Docker Compose for local full-stack startup
- Testing and quality: pytest backend tests, ESLint frontend checks, Vite production build

## Product Capabilities

- Buyer and seller account registration with role-specific onboarding
- Salted password hashing and random bearer session tokens
- Optional Auth0 Universal Login mapped into local buyer/seller profiles
- Marketplace browsing with product category and zip-code based discovery
- Seller product CRUD with inventory counts, reserved quantities, categories, and images
- Product image upload flow from the React frontend to the Flask API
- Buyer pickup request creation with inventory reservation
- Seller order review with confirmed, rejected, ready-for-pickup, and completed states
- Buyer cancellation flow with inventory release
- Product-linked buyer/seller messaging
- Verified reviews restricted to completed orders
- Buyer profile management with contact and home zip details
- Seller farm profile management with pickup address, operating hours, biography, and zip code
- Swagger documentation for the backend API

## Architecture

```text
frontend/                 React SPA served by Vite
  src/                    routes, API client logic, auth flow, and UI screens
  Dockerfile              frontend container for local Compose runs

backend/                  Flask application and persistence layer
  main.py                 route definitions, Swagger configuration, request/response handling
  api_handlers.py         business logic for auth, profiles, products, orders, messages, reviews
  db.py                   SQLite connection helpers, schema utilities, upload handling
  init_db.py              database initialization and seeded demo records
  tests/                  pytest coverage for API behavior
  Dockerfile              backend container for local Compose runs

docker-compose.yml        local full-stack orchestration
```

The frontend talks to the backend through JSON endpoints under `/api/*`. The backend owns authorization checks, status transitions, inventory reservation/release rules, and review eligibility. SQLite keeps the project easy to run locally while still modeling the relational data needed by the marketplace.

## Data Model

The backend stores separate records for authentication, buyer profiles, farm profiles, product listings, orders, order items, messages, reviews, categories, and session tokens. This keeps account identity separate from role-specific marketplace data and makes the order workflow explicit.

Important backend rules:

- Only authenticated sellers can create or edit their own listings.
- Pending orders reserve inventory immediately.
- Rejected or cancelled orders release reserved inventory.
- Completed orders unlock review creation for the buyer.
- Buyers and sellers can only view messages tied to products and orders they are involved with.
- OAuth users are mapped to normal local sessions after Auth0 token validation.

## Run With Docker

From the repository root:

```bash
docker compose up --build
```

Open the app:

```text
http://localhost:5173
```

Backend API:

```text
http://localhost:8000
```

Swagger API docs:

```text
http://localhost:8000/apidocs/
```

Stop the stack:

```bash
docker compose down
```

## Run Locally

Start the backend:

```bash
python3 -m pip install -r backend/requirements.txt
python3 -m backend.init_db
python3 -m backend.main
```

Start the frontend in a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open:

```text
http://localhost:5173
```

## Configuration

For local frontend configuration, copy `frontend/.env.example` to `frontend/.env` and set:

```text
VITE_API_BASE=http://localhost:8000
```

Auth0 is optional. To enable it, configure the backend and frontend with matching Auth0 tenant values.

Backend:

```text
AUTH0_DOMAIN=your-tenant.us.auth0.com
AUTH0_AUDIENCE=https://harvest-market-api
```

Frontend:

```text
VITE_AUTH0_DOMAIN=your-tenant.us.auth0.com
VITE_AUTH0_CLIENT_ID=your_spa_client_id
VITE_AUTH0_AUDIENCE=https://harvest-market-api
```

For Docker Compose, place the same values in a repo-root `.env` file.

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

## Demo Flow

Recommended buyer flow:

1. Log in as `buyer@example.com`.
2. Browse Market, filter by category or zip code, and request pickup for a product.
3. Open Orders and confirm the new request is pending.
4. Open Messages from a product card and send a product-linked message.
5. Submit a review after an order has been completed.

Recommended seller flow:

1. Log in as `seller@example.com`.
2. Update the farm profile and public pickup details.
3. Create or edit a listing with category, inventory, price, and image data.
4. Review incoming pickup requests.
5. Approve a pending order, mark it ready for pickup, and complete it.

## Verification

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

## API Surface

The Flask API includes endpoints for:

- Health checks and category listing
- Local registration and login
- Auth0 session exchange
- Buyer and seller profile retrieval and updates
- Product listing, creation, update, deletion, and image upload
- Order creation, listing, status updates, cancellation, and completion
- Product-scoped messages
- Verified review creation and review listing

Interactive API documentation is available at `/apidocs/` when the backend is running.

## Known Limitations

- Zip filtering uses exact zip-code matching instead of geographic radius distance.
- Pickup scheduling is captured as a requested pickup window text field rather than a fixed time-slot calendar.
- Uploaded images are stored in the backend container filesystem for local demo use.
- Payment processing is intentionally outside the current scope because the workflow is pickup approval, not instant checkout.
