import { useNavigate } from "react-router-dom";
import DashboardSidebar from "./DashboardSidebar";

const BUYER_ACTIONS = {
  pending: [{ key: "cancelled", label: "Cancel Order" }],
  confirmed: [],
  ready_for_pickup: [],
  completed: [],
  rejected: [],
  cancelled: [],
};

const SELLER_ACTIONS = {
  pending: [
    { key: "confirmed", label: "Approve" },
    { key: "rejected", label: "Reject" },
  ],
  confirmed: [{ key: "ready_for_pickup", label: "Mark Ready" }],
  ready_for_pickup: [{ key: "completed", label: "Complete Pickup" }],
  completed: [],
  rejected: [],
  cancelled: [],
};

export default function OrdersPage({
  currentUser,
  orders,
  loading,
  statusFilter,
  onFilterChange,
  onStatusChange,
}) {
  const isBuyer = currentUser?.role === "buyer";
  const actionsByStatus = isBuyer ? BUYER_ACTIONS : SELLER_ACTIONS;
  const navigate = useNavigate();

  return (
    <div className="dashboard-shell">
      <DashboardSidebar
        currentUser={currentUser}
        activeSection="orders"
        action={
          <button
            className="button button--primary dashboard-sidebar__button"
            type="button"
            onClick={() =>
              isBuyer
                ? document.getElementById("orders-list")?.scrollIntoView({ behavior: "smooth" })
                : navigate("/marketplace#live-marketplace")
            }
          >
            {isBuyer ? "Track Order" : "Manage Listings"}
          </button>
        }
      />

      <section className="dashboard-content">
        <div className="section-heading">
          <p className="eyebrow">{isBuyer ? "Order Ledger" : "Inventory Alerts"}</p>
          <h1>
            {isBuyer
              ? "My Orders"
              : "Inventory Alerts"}
          </h1>
          <p>
            {isBuyer
              ? "Track the order lifecycle from request to pickup and completion."
              : "Monitor pending requests and move them through the pickup pipeline."}
          </p>
        </div>

        <label className="sort-bar__control dashboard-filter">
          <span>Status filter</span>
          <select value={statusFilter} onChange={(event) => onFilterChange(event.target.value)}>
            <option value="all">All statuses</option>
            <option value="pending">Pending</option>
            <option value="confirmed">Confirmed</option>
            <option value="ready_for_pickup">Ready for pickup</option>
            <option value="completed">Completed</option>
            <option value="rejected">Rejected</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </label>

        {loading ? (
          <div className="empty-state">
            <h3>Loading dashboard...</h3>
          </div>
        ) : (
          <>
            <div className="alert-card-grid">
              {orders.slice(0, 3).map((order) => (
                <article className="inventory-alert-card" key={order.id}>
                  <img
                    src={order.image_url || "/fruits/apple1.png"}
                    alt={order.product_title}
                    onError={(event) => {
                      event.currentTarget.onerror = null;
                      event.currentTarget.src = "/fruits/apple1.png";
                    }}
                  />
                  <h3>{order.product_title}</h3>
                  <p>{isBuyer ? order.farm_name : order.buyer_email}</p>
                  <strong>
                    {isBuyer
                      ? `${order.quantity} item${order.quantity > 1 ? "s" : ""} requested`
                      : `${order.quantity} item${order.quantity > 1 ? "s" : ""} in this order`}
                  </strong>
                  <small>{order.pickup_window || "Pickup window pending"}</small>
                  <div className="product-card__actions">
                    {(actionsByStatus[order.status] || []).map((action) => (
                      <button
                        className="button button--accent"
                        key={action.key}
                        type="button"
                        onClick={() => onStatusChange(order.id, action.key)}
                      >
                        {action.label}
                      </button>
                    ))}
                  </div>
                </article>
              ))}
            </div>

            <section className="forecast-panel">
              <div>
                <h2>{isBuyer ? "Order Forecast" : "Replenishment Forecast"}</h2>
                <p>
                  {isBuyer
                    ? "Your most recent order activity is summarized here so you can time pickup and review submission."
                    : "Based on market activity, we recommend preparing additional inventory for high-demand items."}
                </p>
                <div className="hero-actions">
                  <button
                    className="button button--accent"
                    type="button"
                    onClick={() =>
                      document.getElementById("orders-list")?.scrollIntoView({
                        behavior: "smooth",
                      })
                    }
                  >
                    {isBuyer ? "View Details" : "Review Requests"}
                  </button>
                  <button
                    className="button button--outline-light"
                    type="button"
                    onClick={() =>
                      isBuyer
                        ? navigate("/community")
                        : navigate("/marketplace")
                    }
                  >
                    {isBuyer ? "Open Reviews" : "Manage Listings"}
                  </button>
                </div>
              </div>

              <div className="forecast-chart">
                {[36, 58, 41, 74, 49, 28, 68].map((height, index) => (
                  <span key={height + index} style={{ height: `${height}%` }} />
                ))}
              </div>
            </section>

            {orders.length === 0 ? (
              <div className="empty-state" id="orders-list">
                <h3>No orders match this filter.</h3>
                <p>
                  {isBuyer
                    ? "Place a marketplace order to start tracking it here."
                    : "Incoming order requests will appear here once buyers start ordering."}
                </p>
              </div>
            ) : (
              <div className="order-grid" id="orders-list">
                {orders.map((order) => (
                  <article className="order-card" key={order.id}>
                    <div className="order-card__header">
                      <div>
                        <p className="eyebrow">Order #{order.id}</p>
                        <h3>{order.product_title}</h3>
                      </div>
                      <span className={`status-pill status-pill--${order.status}`}>
                        {order.status.replaceAll("_", " ")}
                      </span>
                    </div>

                    <div className="order-card__body">
                      <p>
                        <strong>{isBuyer ? order.farm_name : order.buyer_email}</strong>
                      </p>
                      <p>Quantity: {order.quantity}</p>
                      <p>Total: ${Number(order.total_price || 0).toFixed(2)}</p>
                      <p>Pickup Window: {order.pickup_window || "Not set"}</p>
                      <p>Updated: {new Date(order.updated_at).toLocaleString()}</p>
                    </div>

                    <div className="product-card__actions">
                      {(actionsByStatus[order.status] || []).map((action) => (
                        <button
                          className="button button--secondary"
                          key={action.key}
                          type="button"
                          onClick={() => onStatusChange(order.id, action.key)}
                        >
                          {action.label}
                        </button>
                      ))}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
}
