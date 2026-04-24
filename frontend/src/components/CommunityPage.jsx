import { useMemo, useState } from "react";

const galleryImages = [
  "/fruits/apple2.png",
  "/fruits/orange2.png",
  "/fruits/banana2.png",
];

export default function CommunityPage({
  currentUser,
  onRequireAuth,
  reviews,
  reviewOrders,
  onSubmitReview,
}) {
  const [orderId, setOrderId] = useState("");
  const [rating, setRating] = useState("5");
  const [comment, setComment] = useState("");
  const [activeTab, setActiveTab] = useState("recent");
  const [searchTerm, setSearchTerm] = useState("");
  const isBuyer = currentUser?.role === "buyer";
  const selectedOrderId = reviewOrders.some((order) => String(order.id) === orderId)
    ? orderId
    : reviewOrders[0]
      ? String(reviewOrders[0].id)
      : "";

  const avgRating = reviews.length
    ? (reviews.reduce((total, review) => total + review.rating, 0) / reviews.length).toFixed(1)
    : "0.0";

  const filteredReviews = useMemo(() => {
    const lowered = searchTerm.trim().toLowerCase();
    let list = reviews.filter((review) => {
      if (!lowered) return true;
      return `${review.buyer_email} ${review.farm_name} ${review.comment}`
        .toLowerCase()
        .includes(lowered);
    });

    if (activeTab === "highest") {
      list = [...list].sort((a, b) => b.rating - a.rating);
    } else if (activeTab === "critical") {
      list = [...list].filter((review) => review.rating <= 3);
    } else {
      list = [...list].sort(
        (left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime()
      );
    }

    return list;
  }, [activeTab, reviews, searchTerm]);

  return (
    <div className="community-page-shell">
      <section className="dashboard-content dashboard-content--community">
        <div className="community-header">
          <div className="section-heading">
            <p className="eyebrow">Reputation Dashboard</p>
            <h1>Neighbor Testimonials</h1>
            <p>
              A curated look at how your harvest is nourishing the local circle. Every review
              here is tied to a verified completed order.
            </p>
          </div>

          <div className="community-score">
            <div>
              <strong>{avgRating}</strong>
              <span>Avg rating</span>
            </div>
            <div>
              <strong>{reviews.length}</strong>
              <span>Reviews</span>
            </div>
          </div>
        </div>

        <div className="community-toolbar">
          <div className="community-tabs">
            <button
              className={activeTab === "recent" ? "chip-button chip-button--active" : "chip-button"}
              type="button"
              onClick={() => setActiveTab("recent")}
            >
              Recent
            </button>
            <button
              className={activeTab === "highest" ? "chip-button chip-button--active" : "chip-button"}
              type="button"
              onClick={() => setActiveTab("highest")}
            >
              Highest Rated
            </button>
            <button
              className={activeTab === "critical" ? "chip-button chip-button--active" : "chip-button"}
              type="button"
              onClick={() => setActiveTab("critical")}
            >
              Critical
            </button>
          </div>

          <label className="search-field search-field--compact">
            <span>Search comments</span>
            <input
              type="search"
              placeholder="Search comments..."
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
            />
          </label>
        </div>

        <div className="testimonial-grid testimonial-grid--dashboard">
          {filteredReviews.length === 0 ? (
            <article className="testimonial-card testimonial-card--empty">
              <h3>No reviews match this view.</h3>
              <p>Try changing the search term or switching back to recent reviews.</p>
            </article>
          ) : (
            filteredReviews.map((item, index) => (
              <article
                key={item.id}
                className={
                  index === 1 ? "testimonial-card testimonial-card--featured" : "testimonial-card"
                }
              >
                <div className="testimonial-card__header">
                  <div>
                    <h3>{item.buyer_email}</h3>
                    <p>{item.farm_name}</p>
                  </div>
                  <span className="stars">{"★".repeat(item.rating)}</span>
                </div>
                <blockquote>{item.comment}</blockquote>
                <footer>
                  <span>#ORD-{item.order_id} • Verified Order</span>
                  <span>{new Date(item.created_at).toLocaleDateString()}</span>
                </footer>
              </article>
            ))
          )}

          <article className="testimonial-card testimonial-card--request">
            <span>+</span>
            <h3>Request Feedback</h3>
            <p>Invite more neighbors to share their harvest story after pickup.</p>
            <button
              className="button button--ghost"
              type="button"
              onClick={() => document.getElementById("feedback-form")?.scrollIntoView({ behavior: "smooth" })}
            >
              Write One
            </button>
          </article>
        </div>

        <section className="feedback-panel feedback-panel--editorial" id="feedback-form">
          <div className="section-heading">
            <p className="eyebrow">Cultivating Community Feedback</p>
            <h2>Submit My Feedback</h2>
          </div>

          <div className="feedback-panel__body">
            <form
              className="feedback-form feedback-form--figma"
              onSubmit={(event) => {
                event.preventDefault();
                if (!currentUser) {
                  onRequireAuth("Sign in as a buyer to submit a verified review.");
                  return;
                }
                if (!isBuyer || !selectedOrderId || !comment.trim()) {
                  return;
                }
                onSubmitReview({ orderId: Number(selectedOrderId), rating: Number(rating), comment });
                setComment("");
                setRating("5");
              }}
            >
              <label>
                How is your overall experience with the platform?
                <div className="rating-row">
                  <span className="stars">
                    {"★".repeat(Number(rating))}
                    {"☆".repeat(5 - Number(rating))}
                  </span>
                  <strong>{Number(rating).toFixed(1)} / GREAT</strong>
                </div>
              </label>

              <div className="feedback-form__columns">
                <fieldset>
                  <legend>Ease of Use</legend>
                  <label><input type="radio" name="ease" defaultChecked /> Intuitive & Seamless</label>
                  <label><input type="radio" name="ease" /> Mostly Easy</label>
                  <label><input type="radio" name="ease" /> Needs Improvement</label>
                </fieldset>

                <fieldset>
                  <legend>Product Quality</legend>
                  <label><input type="radio" name="quality" defaultChecked /> Exceeds Expectations</label>
                  <label><input type="radio" name="quality" /> Always Fresh</label>
                  <label><input type="radio" name="quality" /> Occasional Issues</label>
                </fieldset>
              </div>

              <label>
                Completed order
                <select value={selectedOrderId} onChange={(event) => setOrderId(event.target.value)}>
                  {reviewOrders.length === 0 ? (
                    <option value="">No completed orders available</option>
                  ) : (
                    reviewOrders.map((order) => (
                      <option key={order.id} value={order.id}>
                        #{order.id} - {order.product_title}
                      </option>
                    ))
                  )}
                </select>
              </label>

              <label>
                Star rating
                <select value={rating} onChange={(event) => setRating(event.target.value)}>
                  <option value="5">5 stars</option>
                  <option value="4">4 stars</option>
                  <option value="3">3 stars</option>
                  <option value="2">2 stars</option>
                  <option value="1">1 star</option>
                </select>
              </label>

              <label>
                What could we do better?
                <textarea
                  rows="5"
                  value={comment}
                  onChange={(event) => setComment(event.target.value)}
                  placeholder="Share your suggestions for improving the harvest experience..."
                />
              </label>

              <button
                className="button button--primary"
                type="submit"
                disabled={!isBuyer || !selectedOrderId || !comment.trim()}
              >
                {!currentUser
                  ? "Sign In To Review"
                  : !isBuyer
                    ? "Buyer Account Required"
                    : !selectedOrderId
                      ? "No Completed Orders Yet"
                      : "Submit My Feedback"}
              </button>
            </form>

            <div className="gallery-strip" aria-hidden="true">
              {galleryImages.map((src) => (
                <img key={src} src={src} alt="" />
              ))}
            </div>
          </div>
        </section>
      </section>
    </div>
  );
}
