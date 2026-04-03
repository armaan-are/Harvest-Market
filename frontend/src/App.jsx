import { useState, useEffect, useMemo } from "react";
import { API_BASE } from "./api";

import AuthPanel from "./components/AuthPanel";
import ProductList from "./components/ProductList";
import CreateProductForm from "./components/CreateProductForm";
import MessagesPanel from "./components/MessagesPanel";
import SortBar from "./components/SortBar";

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [token, setToken] = useState("");

  const [products, setProducts] = useState([]);
  const [loadingProducts, setLoadingProducts] = useState(false);
  const [sortOrder, setSortOrder] = useState("default");

  const [activeProduct, setActiveProduct] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [messageError, setMessageError] = useState("");

  const [focusKeyword, setFocusKeyword] = useState("");
  const [boostList, setBoostList] = useState([]);

  const [editTarget, setEditTarget] = useState(null);
  const [savingEdit, setSavingEdit] = useState(false);

  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    const savedToken = localStorage.getItem("token");

    if (savedUser && savedToken) {
      try {
        const u = JSON.parse(savedUser);
        setCurrentUser({
          id: u.userId,
          role: u.role,
          email: u.email,
        });
        setToken(savedToken);
      } catch {}
    }
  }, []);

  useEffect(() => {
    loadProducts();
  }, [sortOrder]);

  async function loadProducts() {
    setLoadingProducts(true);
    try {
      const res = await fetch(`${API_BASE}/api/products?sort=${sortOrder}`);
      const data = await res.json();
      setProducts(data);
    } finally {
      setLoadingProducts(false);
    }
  }

  function handleLogin(user) {
    setCurrentUser({
      id: user.userId,
      role: user.role,
      email: user.email,
    });
    setToken(user.token);
    localStorage.setItem("token", user.token);
    localStorage.setItem("user", JSON.stringify(user));
  }

  function handleLogout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setToken("");
    setCurrentUser(null);
  }

  async function handleCreateProduct(form) {
    const res = await fetch(`${API_BASE}/api/products`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(form),
    });

    const result = await res.json();
    if (!res.ok) {
      alert(result.message);
      return;
    }

    loadProducts();
  }

  async function handleDeleteProduct(id) {
    if (!window.confirm("Delete this product?")) return;

    const res = await fetch(`${API_BASE}/api/products/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });

    const result = await res.json();
    if (!res.ok) {
      alert(result.message);
      return;
    }

    loadProducts();
  }

  async function handlePurchase(item) {
    const res = await fetch(`${API_BASE}/api/purchases/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ productId: item.id }),
    });

    let result = {};
    try {
      result = await res.json();
    } catch (_) {
      result = { detail: "Request failed" };
    }
    if (!res.ok) {
      alert(result.detail || result.message || "Purchase failed");
      return;
    }

    loadProducts();
  }

  async function handleOpenMessages(product) {
    setActiveProduct(product);
    setmessages([]);
    setMessageError("");
    setLoadingMessages(true);

    try {
      const res = await fetch(
        `${API_BASE}/api/messages?productId=${product.id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      const data = await res.json();
      if (res.ok) {
        setMessages(data);
      } else {
        setMessageError(data.message);
      }
    } catch {
      setMessageError("Network error");
    }

    setLoadingMessages(false);
  }

  async function handleSendMessage(text) {
    if (!activeProduct) return;

    try {
      const res = await fetch(`${API_BASE}/api/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          productId: activeProduct.id,
          content: text,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        setMessageError(data.message);
        return;
      }

      handleOpenMessages(activeProduct);
    } catch {
      setMessageError("Network error");
    }
  }

  function handleEditProduct(p) {
    setEditTarget(p);
  }

  async function handleSaveEdit(update) {
    setSavingEdit(true);

    try {
      const res = await fetch(`${API_BASE}/api/products/${editTarget.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(update),
      });

      const data = await res.json();
      if (!res.ok) {
        alert(data.message);
      } else {
        setEditTarget(null);
        loadProducts();
      }
    } finally {
      setSavingEdit(false);
    }
  }

  async function handleFocusSimilar(p) {
    try {
      const res = await fetch(
        `${API_BASE}/api/products/similar?productId=${p.id}`
      );
      const list = await res.json();

      if (Array.isArray(list)) {
        setBoostList(list.map((t) => t.id));
        setFocusKeyword(p.title);
      }
    } catch {}
  }

  function clearBoost() {
    setBoostList([]);
    setFocusKeyword("");
  }

  const finalProducts = useMemo(() => {
    if (!boostList.length) return products;

    const map = new Map(products.map((p) => [p.id, p]));
    const boosted = boostList.map((id) => map.get(id)).filter(Boolean);
    const rest = products.filter((p) => !boostList.includes(p.id));

    return [...boosted, ...rest];
  }, [products, boostList]);

  return (
    <main
      style={{
        minHeight: "100vh",
        backgroundImage: "url('/farm.png')",
        backgroundSize: "cover",
        padding: "20px",
      }}
    >
      <div
        style={{
          maxWidth: "960px",
          margin: "0 auto",
          backgroundColor: "rgba(255,255,255,0.85)",
          padding: "20px",
          borderRadius: "12px",
        }}
      >
        <header
          style={{
            display: "flex",
            justifyContent: "space-between",
            marginBottom: "20px",
          }}
        >
          <h1>Local Farm Market</h1>

          {currentUser && (
            <div>
              {currentUser.email} ({currentUser.role})
              <button onClick={handleLogout} style={{ marginLeft: "10px" }}>
                Logout
              </button>
            </div>
          )}
        </header>

        {!currentUser && (
          <AuthPanel onLoginSuccess={handleLogin} />
        )}

        {currentUser && currentUser.role === "seller" && (
          <CreateProductForm
            mode={editTarget ? "edit" : "create"}
            initialData={editTarget}
            onCreate={handleCreateProduct}
            onEdit={handleSaveEdit}
            loading={savingEdit}
          />
        )}

        {activeProduct && (
          <MessagesPanel
            product={activeProduct}
            messages={messages}
            messagesLoading={loadingMessages}
            messageError={messageError}
            currentUser={currentUser}
            onClose={() => setActiveProduct(null)}
            onSendMessage={handleSendMessage}
          />
        )}

        <SortBar
          sortOrder={sortOrder}
          onSortChange={(e) => setSortOrder(e.target.value)}
          focusedKeyword={focusKeyword}
          onClearKeyword={clearBoost}
        />

        <ProductList
          products={finalProducts}
          loading={loadingProducts}
          currentUser={currentUser}
          onFocusKeyword={handleFocusSimilar}
          onDeleteProduct={handleDeleteProduct}
          onPurchase={handlePurchase}
          onOpenMessages={handleOpenMessages}
          onEditProduct={handleEditProduct}
        />
      </div>
    </main>
  );
}