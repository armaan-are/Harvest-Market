import { useCallback, useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { API_BASE } from "./api";

import AppShell from "./components/AppShell";
import AuthPanel from "./components/AuthPanel";
import CheckoutModal from "./components/CheckoutModal";
import CommunityPage from "./components/CommunityPage";
import HomePage from "./components/HomePage";
import EditProductModal from "./components/EditProductModal";
import MarketplacePage from "./components/MarketplacePage";
import MessagesPanel from "./components/MessagesPanel";
import OrdersPage from "./components/OrdersPage";
import ProfilePage from "./components/ProfilePage";

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [token, setToken] = useState("");

  const [products, setProducts] = useState([]);
  const [loadingProducts, setLoadingProducts] = useState(false);
  const [sortOrder, setSortOrder] = useState("default");
  const [activeCategory, setActiveCategory] = useState("all");
  const [zipFilter, setZipFilter] = useState("");
  const [searchTerm, setSearchTerm] = useState("");

  const [activeProduct, setActiveProduct] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [messageError, setMessageError] = useState("");

  const [focusKeyword, setFocusKeyword] = useState("");
  const [boostList, setBoostList] = useState([]);

  const [editTarget, setEditTarget] = useState(null);
  const [savingEdit, setSavingEdit] = useState(false);
  const [savingProduct, setSavingProduct] = useState(false);
  const [savingOrder, setSavingOrder] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [authPrompt, setAuthPrompt] = useState("");

  const [orders, setOrders] = useState([]);
  const [checkoutProduct, setCheckoutProduct] = useState(null);
  const [loadingOrders, setLoadingOrders] = useState(false);
  const [orderFilter, setOrderFilter] = useState("all");

  const [profile, setProfile] = useState(null);
  const [savingProfile, setSavingProfile] = useState(false);

  const [reviews, setReviews] = useState([]);
  const [reviewOrders, setReviewOrders] = useState([]);

  const navigate = useNavigate();
  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    const savedToken = localStorage.getItem("token");

    if (savedUser && savedToken) {
      try {
        const user = normalizeUser(JSON.parse(savedUser));
        if (!user) {
          throw new Error("Invalid saved session");
        }
        setCurrentUser(user);
        setToken(savedToken);
      } catch {
        localStorage.removeItem("user");
        localStorage.removeItem("token");
      }
    }
  }, []);

  const authHeaders = useMemo(
    () =>
      token
        ? {
            Authorization: `Bearer ${token}`,
          }
        : {},
    [token]
  );

  const clearAuthState = useCallback((message = "") => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setToken("");
    setCurrentUser(null);
    setActiveProduct(null);
    setEditTarget(null);
    setMessages([]);
    setMessageError("");
    setOrders([]);
    setProfile(null);
    setReviewOrders([]);
    setOrderFilter("all");
    if (message) {
      setStatusMessage(message);
    }
  }, []);

  const loadProducts = useCallback(async () => {
    setLoadingProducts(true);
    try {
      const params = new URLSearchParams({ sort: sortOrder });
      if (activeCategory !== "all") {
        params.set("category", activeCategory);
      }
      if (zipFilter.trim()) {
        params.set("zipCode", zipFilter.trim());
      }
      const res = await fetch(`${API_BASE}/api/products?${params.toString()}`);
      const data = await res.json();
      setProducts(Array.isArray(data) ? data : []);
    } finally {
      setLoadingProducts(false);
    }
  }, [activeCategory, sortOrder, zipFilter]);

  const loadOrders = useCallback(async () => {
    if (!token || !currentUser) {
      setOrders([]);
      return;
    }
    setLoadingOrders(true);
    try {
      const params = new URLSearchParams();
      if (orderFilter !== "all") {
        params.set("status", orderFilter);
      }
      const suffix = params.toString() ? `?${params.toString()}` : "";
      const res = await fetch(`${API_BASE}/api/orders${suffix}`, { headers: authHeaders });
      if (res.status === 401) {
        clearAuthState("Your session expired. Please sign in again.");
        return;
      }
      const data = await res.json();
      setOrders(Array.isArray(data) ? data : []);
    } finally {
      setLoadingOrders(false);
    }
  }, [authHeaders, clearAuthState, currentUser, orderFilter, token]);

  const loadProfile = useCallback(async () => {
    if (!token || !currentUser) {
      setProfile(null);
      return;
    }
    const res = await fetch(`${API_BASE}/api/profile`, { headers: authHeaders });
    if (res.status === 401) {
      clearAuthState("Your session expired. Please sign in again.");
      return;
    }
    const data = await res.json();
    if (res.ok) {
      setProfile(data);
      if (currentUser?.role === "buyer" && data.home_zip && !zipFilter) {
        setZipFilter(data.home_zip);
      }
    }
  }, [authHeaders, clearAuthState, currentUser, token, zipFilter]);

  const loadReviews = useCallback(async () => {
    const res = await fetch(`${API_BASE}/api/reviews`);
    const data = await res.json();
    setReviews(Array.isArray(data) ? data : []);
  }, []);

  const loadCompletedOrders = useCallback(async () => {
    if (!token || currentUser?.role !== "buyer") {
      setReviewOrders([]);
      return;
    }
    const res = await fetch(`${API_BASE}/api/orders?status=completed`, { headers: authHeaders });
    if (res.status === 401) {
      clearAuthState("Your session expired. Please sign in again.");
      return;
    }
    const data = await res.json();
    if (Array.isArray(data)) {
      const reviewedIds = new Set(reviews.map((review) => review.order_id));
      setReviewOrders(data.filter((order) => !reviewedIds.has(order.id)));
    }
  }, [authHeaders, clearAuthState, currentUser?.role, reviews, token]);

  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  useEffect(() => {
    loadReviews();
  }, [loadReviews]);

  useEffect(() => {
    loadOrders();
    loadProfile();
  }, [loadOrders, loadProfile]);

  useEffect(() => {
    loadCompletedOrders();
  }, [loadCompletedOrders]);

  useEffect(() => {
    if (!statusMessage) return undefined;
    const timeout = window.setTimeout(() => setStatusMessage(""), 3200);
    return () => window.clearTimeout(timeout);
  }, [statusMessage]);

  function handleLogin(user) {
    const normalizedUser = normalizeUser(user);
    if (!normalizedUser) {
      setStatusMessage("Unable to load that account");
      return;
    }
    setCurrentUser(normalizedUser);
    setToken(user.token);
    setActiveCategory("all");
    setZipFilter("");
    setSearchTerm("");
    setFocusKeyword("");
    setBoostList([]);
    setOrderFilter("all");
    localStorage.setItem("token", user.token);
    localStorage.setItem("user", JSON.stringify(normalizedUser));
    setAuthPrompt("");
    setStatusMessage(`Signed in as ${normalizedUser.email}`);
    navigate("/marketplace");
  }

  function handleLogout() {
    clearAuthState("Signed out");
    setProducts([]);
    setSortOrder("default");
    setActiveCategory("all");
    setZipFilter("");
    setSearchTerm("");
    setFocusKeyword("");
    setBoostList([]);
    setAuthPrompt("");
    navigate("/marketplace");
  }

  async function uploadImageIfNeeded(form) {
    if (!form.imageFile) {
      return form.image_url;
    }

    const data = new FormData();
    data.append("image", form.imageFile);
    const res = await fetch(`${API_BASE}/api/uploads`, {
      method: "POST",
      headers: authHeaders,
      body: data,
    });
    const payload = await res.json();
    if (!res.ok) {
      throw new Error(payload.detail || "Image upload failed");
    }
    return `${API_BASE}${payload.imagePath}`;
  }

  async function handleCreateProduct(form) {
    setSavingProduct(true);
    try {
      const imageUrl = await uploadImageIfNeeded(form);
      const res = await fetch(`${API_BASE}/api/products`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify({ ...form, image_url: imageUrl }),
      });
      const result = await res.json();
      if (!res.ok) {
        setStatusMessage(result.detail || result.message || "Unable to create product");
        return;
      }
      setStatusMessage("Listing created");
      await loadProducts();
    } catch (error) {
      setStatusMessage(error.message);
    } finally {
      setSavingProduct(false);
    }
  }

  async function handleDeleteProduct(id) {
    if (!window.confirm("Delete this product?")) return;
    const res = await fetch(`${API_BASE}/api/products/${id}`, {
      method: "DELETE",
      headers: authHeaders,
    });
    const result = await res.json();
    if (!res.ok) {
      setStatusMessage(result.detail || result.message || "Unable to delete product");
      return;
    }
    if (editTarget?.id === id) {
      setEditTarget(null);
    }
    setStatusMessage("Listing removed");
    await loadProducts();
  }

  function handlePurchase(item) {
    if (!token) {
      setAuthPrompt("Please sign in as a neighbor to place an order request.");
      navigate("/auth");
      return;
    }

    if (currentUser?.role !== "buyer") {
      setStatusMessage("Use a neighbor account to request pickup orders");
      return;
    }

    setCheckoutProduct(item);
  }

  async function handleSubmitOrder(item, orderRequest) {
    setSavingOrder(true);
    const { quantity, pickupWindow } = orderRequest;

    try {
      const res = await fetch(`${API_BASE}/api/orders`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify({
          productId: item.id,
          quantity,
          pickupWindow,
        }),
      });

      const result = await res.json();
      if (!res.ok) {
        setStatusMessage(result.detail || result.message || "Order request failed");
        return;
      }

      setCheckoutProduct(null);
      setStatusMessage(`Pending pickup request created for ${quantity} ${item.title}`);
      await Promise.all([loadProducts(), loadOrders()]);
    } finally {
      setSavingOrder(false);
    }
  }

  async function handleOpenMessages(product) {
    if (!token) {
      setAuthPrompt("Please sign in to open the product conversation.");
      navigate("/auth");
      return;
    }

    setActiveProduct(product);
    setMessages([]);
    setMessageError("");
    setLoadingMessages(true);
    try {
      const res = await fetch(`${API_BASE}/api/messages?productId=${product.id}`, {
        headers: authHeaders,
      });
      const data = await res.json();
      if (res.ok) {
        setMessages(data);
      } else {
        setMessageError(data.detail || data.message || "Unable to load messages");
      }
    } catch {
      setMessageError("Network error");
    } finally {
      setLoadingMessages(false);
    }
  }

  async function handleSendMessage(text) {
    if (!activeProduct) return;
    try {
      const res = await fetch(`${API_BASE}/api/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify({ productId: activeProduct.id, content: text }),
      });
      const data = await res.json();
      if (!res.ok) {
        setMessageError(data.detail || data.message || "Unable to send message");
        return;
      }
      await handleOpenMessages(activeProduct);
    } catch {
      setMessageError("Network error");
    }
  }

  function handleEditProduct(product) {
    setEditTarget(product);
    setStatusMessage(`Editing ${product.title}`);
  }

  async function handleSaveEdit(update) {
    if (!editTarget) return;
    setSavingEdit(true);
    try {
      const imageUrl = await uploadImageIfNeeded(update);
      const res = await fetch(`${API_BASE}/api/products/${editTarget.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify({ ...update, image_url: imageUrl }),
      });
      const data = await res.json();
      if (!res.ok) {
        setStatusMessage(data.detail || data.message || "Unable to save changes");
      } else {
        setEditTarget(null);
        setStatusMessage("Listing updated");
        await loadProducts();
      }
    } catch (error) {
      setStatusMessage(error.message);
    } finally {
      setSavingEdit(false);
    }
  }

  function handleFocusSimilar(product) {
    const keywords = `${product.title} ${product.description}`.toLowerCase().split(/\W+/);
    const matches = products
      .filter((candidate) => candidate.id !== product.id)
      .map((candidate) => {
        const haystack = `${candidate.title} ${candidate.description}`.toLowerCase();
        const score = keywords.reduce(
          (total, keyword) => (keyword && haystack.includes(keyword) ? total + 1 : total),
          0
        );
        return { id: candidate.id, score };
      })
      .filter((candidate) => candidate.score > 0)
      .sort((left, right) => right.score - left.score);

    if (matches.length) {
      setBoostList(matches.map((match) => match.id));
      setFocusKeyword(product.title);
    } else {
      setStatusMessage("No closely related products were found for that listing");
    }
  }

  async function handleOrderStatusChange(orderId, status) {
    const res = await fetch(`${API_BASE}/api/orders/${orderId}/status`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders,
      },
      body: JSON.stringify({ status }),
    });
    const data = await res.json();
    if (!res.ok) {
      setStatusMessage(data.detail || data.message || "Unable to update order");
      return;
    }
    setStatusMessage(`Order ${status.replaceAll("_", " ")}`);
    await Promise.all([loadOrders(), loadProducts(), loadReviews(), loadCompletedOrders()]);
  }

  async function handleSaveProfile(update) {
    setSavingProfile(true);
    try {
      const res = await fetch(`${API_BASE}/api/profile`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify(update),
      });
      const data = await res.json();
      if (!res.ok) {
        setStatusMessage(data.detail || data.message || "Unable to save profile");
        return;
      }
      setStatusMessage("Profile updated");
      if (data?.role) {
        setProfile(data);
      } else {
        await loadProfile();
      }
      if (currentUser?.role === "buyer") {
        setZipFilter(data.home_zip || update.home_zip || "");
      }
    } finally {
      setSavingProfile(false);
    }
  }

  async function handleSubmitReview(review) {
    const res = await fetch(`${API_BASE}/api/reviews`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders,
      },
      body: JSON.stringify(review),
    });
    const data = await res.json();
    if (!res.ok) {
      setStatusMessage(data.detail || data.message || "Unable to submit review");
      return;
    }
    setStatusMessage("Review submitted");
    await Promise.all([loadReviews(), loadCompletedOrders()]);
  }

  function clearBoost() {
    setBoostList([]);
    setFocusKeyword("");
  }

  function requireAuth(message) {
    setAuthPrompt(message);
    navigate("/auth");
  }

  const filteredProducts = useMemo(() => {
    const search = searchTerm.trim().toLowerCase();
    return products.filter((product) => {
      const matchesSearch =
        !search ||
        `${product.title} ${product.description} ${product.farm_name}`.toLowerCase().includes(search);
      return matchesSearch;
    });
  }, [products, searchTerm]);

  const finalProducts = useMemo(() => {
    if (!boostList.length) return filteredProducts;
    const map = new Map(filteredProducts.map((product) => [product.id, product]));
    const boosted = boostList.map((id) => map.get(id)).filter(Boolean);
    const rest = filteredProducts.filter((product) => !boostList.includes(product.id));
    return [...boosted, ...rest];
  }, [filteredProducts, boostList]);

  const highlightedProducts = useMemo(() => finalProducts.slice(0, 4), [finalProducts]);

  const featuredStats = useMemo(() => {
    const totalProducts = products.length;
    const sellerCount = new Set(products.map((product) => product.seller_id)).size;
    const pendingOrders = orders.filter((order) => order.status === "pending").length;
    return [
      { label: "Listings live", value: totalProducts },
      { label: "Farms represented", value: sellerCount },
      { label: "Pending orders", value: pendingOrders },
    ];
  }, [orders, products]);

  return (
    <AppShell currentUser={currentUser} onLogout={handleLogout} statusMessage={statusMessage}>
      <Routes>
        <Route
          path="/"
          element={
            <HomePage
              currentUser={currentUser}
              highlightedProducts={highlightedProducts}
              onRequireAuth={requireAuth}
            />
          }
        />
        <Route
          path="/auth"
          element={
            <section className="auth-route">
              <div className="auth-route__intro">
                <p className="eyebrow">Sign In To Harvest Market</p>
                <h1>Join the local marketplace built for neighbors and farmers.</h1>
                <p>
                  Buyers can track order status through pickup. Sellers can manage inventory,
                  incoming requests, profiles, and trust signals from the same SPA.
                </p>
              </div>
              <AuthPanel
                prompt={authPrompt}
                onLoginSuccess={handleLogin}
                onDismissPrompt={() => setAuthPrompt("")}
              />
            </section>
          }
        />
        <Route
          path="/marketplace"
          element={
            <MarketplacePage
              currentUser={currentUser}
              featuredStats={featuredStats}
              focusKeyword={focusKeyword}
              loadingProducts={loadingProducts}
              onClearBoost={clearBoost}
              onCreateProduct={handleCreateProduct}
              onDeleteProduct={handleDeleteProduct}
              onEditProduct={handleEditProduct}
              onFocusKeyword={handleFocusSimilar}
              onOpenMessages={handleOpenMessages}
              onPurchase={handlePurchase}
              onRequireAuth={requireAuth}
              onSearchChange={setSearchTerm}
              onSetCategory={setActiveCategory}
              onSetSortOrder={setSortOrder}
              onSetZipFilter={setZipFilter}
              products={finalProducts}
              savingProduct={savingProduct}
              searchTerm={searchTerm}
              selectedCategory={activeCategory}
              sortOrder={sortOrder}
              zipFilter={zipFilter}
            />
          }
        />
        <Route
          path="/orders"
          element={
            currentUser ? (
              <OrdersPage
                currentUser={currentUser}
                orders={orders}
                loading={loadingOrders}
                statusFilter={orderFilter}
                onFilterChange={setOrderFilter}
                onStatusChange={handleOrderStatusChange}
              />
            ) : (
              <Navigate to="/auth" replace />
            )
          }
        />
        <Route
          path="/profile"
          element={
            currentUser ? (
              <ProfilePage
                key={`${currentUser.id}-${currentUser.role}-${JSON.stringify(profile ?? {})}`}
                currentUser={currentUser}
                profile={profile}
                onSaveProfile={handleSaveProfile}
                loading={savingProfile}
              />
            ) : (
              <Navigate to="/auth" replace />
            )
          }
        />
        <Route
          path="/community"
          element={
            <CommunityPage
              currentUser={currentUser}
              onRequireAuth={requireAuth}
              reviews={reviews}
              reviewOrders={reviewOrders}
              onSubmitReview={handleSubmitReview}
            />
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>

      <MessagesPanel
        product={activeProduct}
        messages={messages}
        messagesLoading={loadingMessages}
        messageError={messageError}
        currentUser={currentUser}
        onClose={() => setActiveProduct(null)}
        onSendMessage={handleSendMessage}
      />
      {checkoutProduct ? (
        <CheckoutModal
          key={checkoutProduct.id}
          product={checkoutProduct}
          loading={savingOrder}
          onClose={() => {
            if (!savingOrder) {
              setCheckoutProduct(null);
            }
          }}
          onSubmit={handleSubmitOrder}
        />
      ) : null}
      {editTarget ? (
        <EditProductModal
          key={`edit-modal-${editTarget.id}`}
          product={editTarget}
          loading={savingEdit}
          onClose={() => {
            if (!savingEdit) {
              setEditTarget(null);
            }
          }}
          onSave={handleSaveEdit}
        />
      ) : null}
    </AppShell>
  );
}

function normalizeUser(user) {
  const id = user?.id ?? user?.userId;
  if (!id || !user?.role || !user?.email) {
    return null;
  }

  return {
    id,
    role: user.role,
    email: user.email,
  };
}
