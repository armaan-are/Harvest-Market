import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from .auth import get_current_user
from .db import get_db


router = APIRouter(prefix="/api/products", tags=["products"])


@router.post("/", status_code=200)
async def create_product(
    request: Request,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    body = await request.json()
    title = body.get("title")
    description = body.get("description")
    price = body.get("price")
    image_url = body.get("image_url")
    if current_user["role"] != "seller":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only sellers can create products",
        )

    if not title or price is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title and price are required",
        )

    # Embeddings are omitted to avoid external dependencies like the OpenAI client.
    # Existing products with embeddings (from the Node backend) will still work
    # for similarity queries.
    try:
        cursor = db.execute(
            """
            INSERT INTO products (title, description, price, image_url, seller_id, purchase_count, embedding)
            VALUES (?, ?, ?, ?, ?, 0, ?)
            """,
            (
                title,
                description,
                price,
                image_url,
                current_user["userId"],
                None,
            ),
        )
        db.commit()
        product_id = cursor.lastrowid
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product",
        )

    return {"message": "Product created", "productId": product_id}


@router.put("/{product_id}")
async def update_product(
    product_id: int,
    request: Request,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    body = await request.json()
    title = body.get("title")
    description = body.get("description")
    price = body.get("price")
    image_url = body.get("image_url")
    if current_user["role"] != "seller":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only sellers can update products",
        )

    # Keep logic similar to original: overwrite all fields
    cursor = db.execute(
        """
        UPDATE products
        SET title = ?, description = ?, price = ?, image_url = ?
        WHERE id = ? AND seller_id = ?
        """,
        (
            title,
            description,
            price,
            image_url,
            product_id,
            current_user["userId"],
        ),
    )
    db.commit()

    if cursor.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own products",
        )

    return {"message": "Product updated"}


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user["role"] != "seller":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only sellers can delete products",
        )

    cursor = db.execute(
        """
        DELETE FROM products
        WHERE id = ? AND seller_id = ?
        """,
        (product_id, current_user["userId"]),
    )
    db.commit()

    if cursor.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own products",
        )

    return {"message": "Product deleted"}


@router.get("/")
def list_products(
    sort: str | None = Query(default=None),
    db=Depends(get_db),
):
    sql = "SELECT * FROM products"

    if sort == "price_asc":
        sql += " ORDER BY price ASC"
    elif sort == "price_desc":
        sql += " ORDER BY price DESC"
    elif sort == "popular":
        sql += " ORDER BY purchase_count DESC, id DESC"
    else:
        sql += " ORDER BY id DESC"

    cursor = db.execute(sql)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@router.get("/similar")
def similar_products(
    productId: int = Query(..., alias="productId"),
    db=Depends(get_db),
):
    cursor = db.execute(
        "SELECT embedding FROM products WHERE id = ?",
        (productId,),
    )
    target = cursor.fetchone()

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    try:
        target_emb = json.loads(target["embedding"] or "[]")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing embeddings",
        )

    cursor = db.execute(
        "SELECT * FROM products WHERE id != ? AND embedding IS NOT NULL",
        (productId,),
    )
    rows = cursor.fetchall()

    scored = []
    for row in rows:
        try:
            candidate_emb = json.loads(row["embedding"] or "[]")
            similarity = sum(
                (val * candidate_emb[i] for i, val in enumerate(target_emb))
            )
        except Exception:
            continue
        scored.append({**dict(row), "similarity": similarity})

    scored.sort(key=lambda r: r["similarity"], reverse=True)
    scored = scored[:5]

    return scored

