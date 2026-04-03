from fastapi import APIRouter, Depends, HTTPException, Request, status

from .auth import create_access_token, hash_password, verify_password
from .db import get_db


router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/register")
async def register(request: Request, db=Depends(get_db)):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body",
        )
    email = body.get("email")
    password = body.get("password")
    role = body.get("role")

    if not email or not password or not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required fields",
        )

    password_hash = hash_password(password)

    try:
        cursor = db.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            (email, password_hash, role),
        )
        db.commit()
        user_id = cursor.lastrowid
    except Exception as exc:
        print("Registration error:", repr(exc))
        db.rollback()
        if "UNIQUE constraint failed" in str(exc) or "unique" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )

    return {"message": "Registration successful", "userId": user_id}


@router.post("/login")
async def login(request: Request, db=Depends(get_db)):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body",
        )
    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing email or password",
        )

    cursor = db.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,),
    )
    row = cursor.fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not verify_password(password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong password",
        )

    token = create_access_token(user_id=row["id"], role=row["role"])

    return {
        "message": "Login successful",
        "token": token,
        "role": row["role"],
        "email": row["email"],
        "userId": row["id"],
    }

