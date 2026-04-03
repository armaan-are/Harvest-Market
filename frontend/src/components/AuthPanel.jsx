import { useState } from "react";
import { API_BASE } from "../api";

/**
 * Handles login / registration and returns user data to the parent on success.
 */
export default function AuthPanel({ onLoginSuccess }) {
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("buyer");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const endpoint = mode === "login" ? "login" : "register";

      const body =
        mode === "login"
          ? { email, password }
          : { email, password, role };

      const res = await fetch(`${API_BASE}/api/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      let data = {};
      try {
        data = await res.json();
      } catch (_) {
        data = { detail: res.statusText || "Server error" };
      }

      if (!res.ok) {
        setError(data.detail || data.message || "Authentication failed");
        return;
      }

      if (mode === "login") {
        // Pass user info back to App
        onLoginSuccess(data);
      } else {
        alert("Registration successful! Please log in.");
        setMode("login");
      }
    } catch (err) {
      console.error(err);
      setError("Network error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        padding: "20px",
        borderRadius: "10px",
        border: "1px solid #e5e7eb",
        marginBottom: "24px",
        backgroundColor: "rgba(255,255,255,0.95)",
      }}
    >
      <div style={{ marginBottom: "10px" }}>
        <button
          type="button"
          onClick={() => setMode("login")}
          disabled={mode === "login"}
        >
          Login
        </button>
        <button
          type="button"
          onClick={() => setMode("register")}
          disabled={mode === "register"}
          style={{ marginLeft: "8px" }}
        >
          Register
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: "8px" }}>
          <label>
            Email:
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={{ marginLeft: "8px" }}
            />
          </label>
        </div>

        <div style={{ marginBottom: "8px" }}>
          <label>
            Password:
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{ marginLeft: "8px" }}
            />
          </label>
        </div>

        {mode === "register" && (
          <div style={{ marginBottom: "8px" }}>
            <label>
              Role:
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                style={{ marginLeft: "8px" }}
              >
                <option value="buyer">Buyer</option>
                <option value="seller">Seller</option>
              </select>
            </label>
          </div>
        )}

        {error && (
          <div style={{ color: "red", marginBottom: "8px" }}>{error}</div>
        )}

        <button type="submit" disabled={loading}>
          {loading ? "Processing..." : mode === "login" ? "Login" : "Register"}
        </button>
      </form>
    </div>
  );
}