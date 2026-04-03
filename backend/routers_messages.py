from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from .auth import get_current_user
from .db import get_db


router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.get("/")
def get_messages(
    productId: int = Query(..., alias="productId"),
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = current_user["userId"]

    cursor = db.execute(
        """
        SELECT m.*, u.email AS sender_email
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE m.product_id = ?
          AND (m.buyer_id = ? OR m.seller_id = ?)
        ORDER BY m.created_at ASC
        """,
        (productId, user_id, user_id),
    )
    rows = cursor.fetchall()

    return [dict(row) for row in rows]


@router.post("/")
async def post_message(
    request: Request,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    body = await request.json()
    product_id = body.get("productId")
    content = body.get("content")
    user_id = current_user["userId"]
    user_role = current_user["role"]

    if not product_id or not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="productId and content are required",
        )

    cursor = db.execute(
        "SELECT seller_id FROM products WHERE id = ?",
        (product_id,),
    )
    product = cursor.fetchone()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    seller_id = product["seller_id"]

    if user_role not in ("buyer", "seller"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only buyers or sellers can send messages",
        )

    cursor = db.execute(
        """
        SELECT buyer_id, seller_id
        FROM messages
        WHERE product_id = ?
        LIMIT 1
        """,
        (product_id,),
    )
    existing = cursor.fetchone()

    if not existing:
        if user_role != "buyer":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The first message must be sent by a buyer.",
            )
        buyer_id = user_id
    else:
        buyer_id = existing["buyer_id"]
        if user_id not in (buyer_id, existing["seller_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this conversation.",
            )

    cursor = db.execute(
        """
        INSERT INTO messages
          (product_id, buyer_id, seller_id, sender_id, sender_role, content)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (product_id, buyer_id, seller_id, user_id, user_role, content),
    )
    db.commit()

    return {"message": "Message sent", "messageId": cursor.lastrowid}

