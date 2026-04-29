import { useState } from "react";
import { useNavigate } from "react-router-dom";
import ShareModal from "./ShareModal";

export default function HomePage({
  currentUser,
  highlightedProducts,
  onRequireAuth,
}) {
  const [shareTarget, setShareTarget] = useState(null);
  const navigate = useNavigate();
  const workspaceLabel =
    currentUser?.role === "seller" ? "Incoming Requests" : "My Orders";

  return (
    <div className="editorial-page">
      <section className="editorial-hero">
        <div className="editorial-hero__copy">
          <h1>Harvest Market</h1>
          <p>
            Browse nearby farms, request pickup orders, track every status change,
            and leave verified reviews after pickup.
          </p>
          <div className="hero-actions">
            <button
              className="button button--primary"
              type="button"
              onClick={() => navigate("/marketplace")}
            >
              Open Market
            </button>
            <button
              className="button button--soft"
              type="button"
              onClick={() => {
                if (currentUser) {
                  navigate("/orders");
                } else {
                  onRequireAuth("Create an account to start buying or selling.");
                }
              }}
            >
              {currentUser ? workspaceLabel : "Get Started"}
            </button>
          </div>
        </div>

        <div className="editorial-hero__visual">
          <div className="hero-illustration">
            <div className="hero-illustration__cloud hero-illustration__cloud--one" />
            <div className="hero-illustration__cloud hero-illustration__cloud--two" />
            <div className="hero-illustration__hill hero-illustration__hill--one" />
            <div className="hero-illustration__hill hero-illustration__hill--two" />
            <div className="hero-illustration__field" />
          </div>
          <div className="editorial-note">
            <p>This week under glass</p>
            <strong>Real inventory, pickup requests, farm profiles, and verified reviews.</strong>
          </div>
        </div>
      </section>

      <section className="editorial-how" id="how-it-works">
        <div className="section-heading section-heading--centered">
          <p className="eyebrow">How it Works</p>
          <h2>One flow for neighbors. One dashboard for farmers.</h2>
        </div>

        <div className="editorial-how__grid">
          <article className="editorial-info-card">
            <h3>For Neighbors</h3>
            <ul>
              <li>Filter by category or farm zip code.</li>
              <li>Place pending pickup requests instead of instant checkout.</li>
              <li>Track orders and review farms after completion.</li>
            </ul>
          </article>

          <article className="editorial-basket-card">
            <div className="basket-illustration">
              <span />
              <span />
              <span />
            </div>
            <p>Local inventory moves from farm stand to pickup queue.</p>
          </article>

          <article className="editorial-info-card">
            <h3>For Farmers</h3>
            <ul>
              <li>Create listings with categories, stock, and images.</li>
              <li>Approve, reject, and advance incoming orders.</li>
              <li>Maintain a farm profile and build trust through reviews.</li>
            </ul>
          </article>
        </div>
      </section>

      <section className="editorial-featured">
        <div className="section-heading section-heading--inline">
          <div>
            <p className="eyebrow">Featured Harvests</p>
            <h2>Live products from local farms.</h2>
          </div>
          <button className="button button--ghost" type="button" onClick={() => navigate("/marketplace")}>
            View Market
          </button>
        </div>

        <div className="editorial-featured__grid">
          {highlightedProducts.map((product) => (
            <article className="market-card" key={product.id}>
              <div className="market-card__image">
                <img
                  src={product.image_url || "/fruits/apple1.png"}
                  alt={product.title}
                  onError={(event) => {
                    event.currentTarget.onerror = null;
                    event.currentTarget.src = "/fruits/apple1.png";
                  }}
                />
                <button
                  className="market-card__share"
                  type="button"
                  onClick={() => setShareTarget(product)}
                >
                  ↗
                </button>
              </div>
              <div className="market-card__body">
                <h3>{product.title}</h3>
                <p>{product.description}</p>
                <div className="market-card__meta">
                  <span>${product.price}</span>
                  <small>{product.farm_name}</small>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="editorial-cta">
        <h2>Ready to browse local inventory?</h2>
        <p>The full marketplace is now on a dedicated page for filtering, ordering, and seller tools.</p>
        <div className="hero-actions hero-actions--center">
          <button className="button button--light" type="button" onClick={() => navigate("/marketplace")}>
            Open Market
          </button>
          <button className="button button--outline-light" type="button" onClick={() => navigate("/community")}>
            Read Reviews
          </button>
        </div>
      </section>

      <ShareModal
        key={shareTarget ? `home-share-${shareTarget.id}` : "home-share-empty"}
        product={shareTarget}
        onClose={() => setShareTarget(null)}
      />
    </div>
  );
}
