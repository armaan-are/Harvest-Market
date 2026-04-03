from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers_auth import router as auth_router
from .routers_products import router as products_router
from .routers_messages import router as messages_router
from .routers_purchases import router as purchases_router

app = FastAPI(title="Local Farm Market API (FastAPI)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "message": "FastAPI backend is running!"}


app.include_router(auth_router)
app.include_router(products_router)
app.include_router(messages_router)
app.include_router(purchases_router)

