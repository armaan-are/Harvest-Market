import { useMemo, useState } from "react";

export default function ShareModal({ product, onClose }) {
  const [copied, setCopied] = useState(false);
  const shareUrl = useMemo(() => {
    if (!product) {
      return "";
    }
    const origin = window.location.origin || "http://localhost:5173";
    return `${origin}/marketplace?product=${product.id}`;
  }, [product]);

  if (!product) return null;

  function openShare(target) {
    if (target === "facebook") {
      window.open(
        `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`,
        "_blank",
        "noopener,noreferrer"
      );
      return;
    }

    if (target === "twitter") {
      window.open(
        `https://twitter.com/intent/tweet?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(`Check out ${product.title} from ${product.farm_name || "The Editorial Harvest"}`)}`,
        "_blank",
        "noopener,noreferrer"
      );
      return;
    }

    window.location.href = `mailto:?subject=${encodeURIComponent(`Share the Harvest: ${product.title}`)}&body=${encodeURIComponent(shareUrl)}`;
  }

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="modal-overlay" role="presentation" onClick={onClose}>
      <section
        className="share-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="share-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="share-modal__header">
          <div>
            <h2 id="share-title">Share the Harvest</h2>
            <p>Spread the word about this farm listing.</p>
          </div>
          <button className="button button--ghost" type="button" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="share-modal__product">
          <img
            src={product.image_url || "/fruits/apple1.png"}
            alt={product.title}
            onError={(event) => {
              event.currentTarget.onerror = null;
              event.currentTarget.src = "/fruits/apple1.png";
            }}
          />
          <div>
            <strong>{product.title}</strong>
            <span>{product.category?.replaceAll("_", " ") || "Regenerative Agriculture"}</span>
          </div>
        </div>

        <div className="share-modal__icons">
          <button className="share-icon" type="button" onClick={() => openShare("facebook")}>
            <span>f</span>
            <p>Facebook</p>
          </button>
          <button className="share-icon" type="button" onClick={() => openShare("twitter")}>
            <span>t</span>
            <p>Twitter</p>
          </button>
          <button className="share-icon" type="button" onClick={() => openShare("email")}>
            <span>@</span>
            <p>Email</p>
          </button>
        </div>

        <label className="share-modal__link">
          <span>Profile Link</span>
          <div>
            <input readOnly value={shareUrl} />
            <button
              className="button button--primary"
              type="button"
              onClick={handleCopy}
            >
              {copied ? "Copied" : "Copy Link"}
            </button>
          </div>
        </label>

        <p className="share-modal__footer">Harvested with Care</p>
      </section>
    </div>
  );
}
