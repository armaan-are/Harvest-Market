export default function ProductList({
  products,
  loading,
  onFocusKeyword,
  currentUser,
  onEditProduct,
  onDeleteProduct,
  onOpenMessages,
  onPurchase,
}) {
  return (
    <section className="product-section">
      {loading ? (
        <div className="empty-state">
          <h3>Loading inventory...</h3>
          <p>Pulling the latest products from the marketplace.</p>
        </div>
      ) : products.length === 0 ? (
        <div className="empty-state">
          <h3>No products match this view.</h3>
          <p>Try clearing the category filter or search term.</p>
        </div>
      ) : (
        <div className="product-grid">
          {products.map((product) => {
            const isOwner =
              currentUser?.role === "seller" && product.seller_id === currentUser.id;
            const isBuyer = currentUser?.role === "buyer";
            const isSoldOut = Number(product.quantity_available) <= 0;

            return (
              <article className="product-card" key={product.id}>
                <div className="product-card__image">
                  <img
                    src={product.image_url || "/fruits/apple1.png"}
                    alt={product.title}
                    onError={(event) => {
                      event.currentTarget.onerror = null;
                      event.currentTarget.src = "/fruits/apple1.png";
                    }}
                  />
                </div>

                <div className="product-card__body">
                  <div className="product-card__header">
                    <div>
                      <p className="product-card__eyebrow">
                        {product.farm_name || "Farm listing"}
                      </p>
                      <h3>{product.title}</h3>
                    </div>
                    <strong>${product.price}</strong>
                  </div>

                  <p className="product-card__description">{product.description}</p>
                  <p className="product-card__meta">
                    {product.category?.replaceAll("_", " ")} | {product.zip_code || "local zip"} |{" "}
                    {isSoldOut ? "Sold out" : `${product.quantity_available} available`} | Bought{" "}
                    {product.purchase_count ?? 0}{" "}
                    {(product.purchase_count ?? 0) === 1 ? "time" : "times"} | Rating{" "}
                    {Number(product.average_rating || 0).toFixed(1)}
                  </p>

                  <div className="product-card__actions">
                    <button className="button button--ghost" type="button" onClick={() => onFocusKeyword(product)}>
                      Similar products
                    </button>

                    {isBuyer ? (
                      <button
                        className="button button--primary"
                        type="button"
                        onClick={() => onPurchase(product)}
                        disabled={isSoldOut}
                      >
                        {isSoldOut ? "Sold Out" : "Request Pickup"}
                      </button>
                    ) : null}

                    {currentUser ? (
                      <button className="button button--secondary" type="button" onClick={() => onOpenMessages(product)}>
                        Messages
                      </button>
                    ) : null}

                    {isOwner ? (
                      <>
                        <button className="button button--secondary" type="button" onClick={() => onEditProduct(product)}>
                          Edit
                        </button>
                        <button className="button button--danger" type="button" onClick={() => onDeleteProduct(product.id)}>
                          Delete
                        </button>
                      </>
                    ) : null}
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
