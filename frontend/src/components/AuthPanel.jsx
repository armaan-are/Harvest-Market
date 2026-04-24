import { useState } from "react";
import { API_BASE } from "../api";

export default function AuthPanel({ onLoginSuccess, prompt, onDismissPrompt }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("buyer");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      const endpoint = mode === "login" ? "login" : "register";
      const body = mode === "login" ? { email, password } : { email, password, role };

      const res = await fetch(`${API_BASE}/api/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      let data = {};
      try {
        data = await res.json();
      } catch {
        data = { detail: res.statusText || "Server error" };
      }

      if (!res.ok) {
        setError(data.detail || data.message || "Authentication failed");
        return;
      }

      if (mode === "login") {
        onLoginSuccess(data);
      } else {
        setSuccess("Registration successful. Sign in with your new account.");
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
    <section className="auth-card">
      <div className="auth-card__switcher">
        <button
          className={mode === "login" ? "chip-button chip-button--active" : "chip-button"}
          type="button"
          onClick={() => setMode("login")}
        >
          Login
        </button>
        <button
          className={mode === "register" ? "chip-button chip-button--active" : "chip-button"}
          type="button"
          onClick={() => setMode("register")}
        >
          Register
        </button>
      </div>

      {prompt ? (
        <div className="info-banner">
          <span>{prompt}</span>
          <button type="button" onClick={onDismissPrompt}>
            Dismiss
          </button>
        </div>
      ) : null}

      {success ? <div className="success-banner">{success}</div> : null}
      {error ? <div className="error-banner">{error}</div> : null}

      <form className="auth-form" onSubmit={handleSubmit}>
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
            placeholder="neighbor@example.com"
          />
        </label>

        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
            placeholder="Enter your password"
          />
        </label>

        {mode === "register" ? (
          <label>
            Account role
            <select value={role} onChange={(event) => setRole(event.target.value)}>
              <option value="buyer">Neighbor / Buyer</option>
              <option value="seller">Farmer / Seller</option>
            </select>
          </label>
        ) : null}

        <button className="button button--primary auth-form__submit" type="submit" disabled={loading}>
          {loading ? "Processing..." : mode === "login" ? "Login" : "Register"}
        </button>
      </form>
    </section>
  );
}
