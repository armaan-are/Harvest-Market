from fastapi import APIRouter, Depends, HTTPException, Request, status

from .auth import get_current_user
from .db import get_db


router = APIRouter(prefix="/api/purchases", tags=["purchases"])


@router.post("/")
async def create_purchase(
    request: Request,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    body = await request.json()
    product_id = body.get("productId")
    user_id = current_user["userId"]
    user_role = current_user["role"]

    if not product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="productId is required",
        )

    if user_role != "buyer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only buyers can purchase products",
        )

    cursor = db.execute(
        "SELECT id, seller_id FROM products WHERE id = ?",
        (product_id,),
    )
    product = cursor.fetchone()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    seller_id = product["seller_id"]

    try:
        db.execute(
            "INSERT INTO purchases (buyer_id, seller_id, product_id) "
            "VALUES (?, ?, ?)",
            (user_id, seller_id, product_id),
        )
        db.execute(
            "UPDATE products "
            "SET purchase_count = purchase_count + 1 "
            "WHERE id = ?",
            (product_id,),
        )
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Purchase saved, but failed to update purchase count",
        )

    return {"message": "Purchase successful"}

