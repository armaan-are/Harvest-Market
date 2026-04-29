import { useMemo, useState } from "react";

export default function CheckoutModal({
  product,
  loading = false,
  onClose,
  onSubmit,
}) {
  const [quantity, setQuantity] = useState("1");
  const [pickupWindow, setPickupWindow] = useState("Saturday 10:00 AM");
  const [error, setError] = useState("");

  const maxQuantity = Number(product?.quantity_available || 0);
  const total = useMemo(() => {
    const parsedQuantity = Number.parseInt(quantity, 10);
    if (!Number.isInteger(parsedQuantity)) return 0;
    return parsedQuantity * Number(product?.price || 0);
  }, [product?.price, quantity]);

  if (!product) {
    return null;
  }

  function handleSubmit(event) {
    event.preventDefault();
    const parsedQuantity = Number.parseInt(quantity, 10);

    if (!Number.isInteger(parsedQuantity) || parsedQuantity <= 0) {
      setError("Enter a whole number quantity.");
      return;
    }

    if (parsedQuantity > maxQuantity) {
      setError(`Only ${maxQuantity} available for this listing.`);
      return;
    }

    if (!pickupWindow.trim()) {
      setError("Choose a pickup window for the farmer to review.");
      return;
    }

    setError("");
    onSubmit(product, {
      quantity: parsedQuantity,
      pickupWindow: pickupWindow.trim(),
    });
  }

  return (
    <div className="modal-overlay" role="presentation" onMouseDown={onClose}>
      <section
        className="checkout-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="checkout-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="messages-modal__header">
          <div>
            <p className="eyebrow">Pickup Request</p>
            <h2 id="checkout-title">Request {product.title}</h2>
          </div>
          <button className="button button--ghost" type="button" onClick={onClose}>
            Close
          </button>
        </div>

        <div className="checkout-modal__product">
          <img
            src={product.image_url || "/fruits/apple1.png"}
            alt={product.title}
            onError={(event) => {
              event.currentTarget.onerror = null;
              event.currentTarget.src = "/fruits/apple1.png";
            }}
          />
          <div>
            <strong>{product.farm_name}</strong>
            <span>
              ${Number(product.price || 0).toFixed(2)} each | {maxQuantity} available
            </span>
          </div>
        </div>

        <form className="seller-form" onSubmit={handleSubmit}>
          <label>
            Quantity
            <input
              type="number"
              min="1"
              max={maxQuantity}
              step="1"
              value={quantity}
              onChange={(event) => setQuantity(event.target.value)}
              required
            />
          </label>

          <label>
            Pickup window
            <input
              type="text"
              value={pickupWindow}
              onChange={(event) => setPickupWindow(event.target.value)}
              placeholder="Saturday 10:00 AM"
              required
            />
          </label>

          <div className="checkout-modal__summary">
            <span>Estimated total</span>
            <strong>${total.toFixed(2)}</strong>
          </div>

          {error ? <div className="error-banner">{error}</div> : null}

          <button className="button button--primary" type="submit" disabled={loading}>
            {loading ? "Submitting..." : "Submit Pickup Request"}
          </button>
        </form>
      </section>
    </div>
  );
}
