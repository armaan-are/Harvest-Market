/**
 * Displays a grid of products and exposes actions via callbacks.
 */
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
    <section>
      <h2 style={{ marginBottom: "12px" }}>Product List</h2>

      {loading ? (
        <p>Loading...</p>
      ) : products.length === 0 ? (
        <p>No products yet.</p>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "16px",
          }}
        >
          {products.map((p) => {
            const isOwner =
              currentUser &&
              currentUser.role === "seller" &&
              p.seller_id === currentUser.id;

            const isBuyer = currentUser && currentUser.role === "buyer";

            return (
              <div
                key={p.id}
                style={{
                  border: "1px solid #e5e7eb",
                  borderRadius: "8px",
                  padding: "12px",
                  backgroundColor: "rgba(255, 255, 255, 0.96)",
                }}
              >
                {p.image_url && (
                  <div
                    style={{
                      width: "100%",
                      paddingBottom: "56%",
                      position: "relative",
                      marginBottom: "8px",
                      overflow: "hidden",
                      borderRadius: "6px",
                      backgroundColor: "#e5e7eb",
                    }}
                  >
                    <img
                      src={p.image_url}
                      alt={p.title}
                      onError={(e) => {
                        e.target.onerror = null;
                        e.target.src = "/fruits/apple1.png";
                      }}
                      style={{
                        position: "absolute",
                        top: 0,
                        left: 0,
                        width: "100%",
                        height: "100%",
                        objectFit: "cover",
                      }}
                    />
                  </div>
                )}

                <h3 style={{ margin: "4px 0" }}>{p.title}</h3>
                <p style={{ margin: "4px 0", color: "#4b5563" }}>
                  {p.description}
                </p>
                <p style={{ margin: "4px 0", fontWeight: "bold" }}>
                  ${p.price}
                </p>

                <p
                  style={{
                    margin: "2px 0 6px",
                    fontSize: "13px",
                    color: "#6b7280",
                  }}
                >
                  Bought {p.purchase_count ?? 0}{" "}
                  {(p.purchase_count ?? 0) === 1 ? "time" : "times"}
                </p>

                <div
                  style={{
                    marginTop: "6px",
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "6px",
                  }}
                >
                  {onFocusKeyword && (
                    <button
                      type="button"
                      onClick={() => onFocusKeyword(p)}
                      style={{
                        padding: "4px 8px",
                        borderRadius: "6px",
                        border: "1px solid #d1d5db",
                        backgroundColor: "#e5e7eb",
                        cursor: "pointer",
                        fontSize: "12px",
                      }}
                    >
                      See similar products
                    </button>
                  )}

                  {isBuyer && (
                    <button
                      type="button"
                      onClick={() => onPurchase && onPurchase(p)}
                      style={{
                        padding: "4px 8px",
                        borderRadius: "6px",
                        border: "1px solid #4ade80",
                        backgroundColor: "#bbf7d0",
                        cursor: "pointer",
                        fontSize: "12px",
                      }}
                    >
                      Buy
                    </button>
                  )}

                  {onOpenMessages && currentUser && (
                    <button
                      type="button"
                      onClick={() => onOpenMessages(p)}
                      style={{
                        padding: "4px 8px",
                        borderRadius: "6px",
                        border: "1px solid #d1d5db",
                        backgroundColor: "#eef2ff",
                        cursor: "pointer",
                        fontSize: "12px",
                      }}
                    >
                      Messages
                    </button>
                  )}

                  {isOwner && (
                    <>
                      <button
                        type="button"
                        onClick={() => onEditProduct && onEditProduct(p)}
                        style={{
                          padding: "4px 8px",
                          borderRadius: "6px",
                          border: "1px solid #d1d5db",
                          backgroundColor: "#e0f2fe",
                          cursor: "pointer",
                          fontSize: "12px",
                        }}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() =>
                          onDeleteProduct && onDeleteProduct(p.id)
                        }
                        style={{
                          padding: "4px 8px",
                          borderRadius: "6px",
                          border: "1px solid #fecaca",
                          backgroundColor: "#fee2e2",
                          cursor: "pointer",
                          fontSize: "12px",
                        }}
                      >
                        Delete
                      </button>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}