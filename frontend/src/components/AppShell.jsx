import { NavLink } from "react-router-dom";

export default function AppShell({ children, currentUser, onLogout, statusMessage }) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <NavLink className="brand-mark brand-mark--editorial" to="/">
          Harvest Market
        </NavLink>

        <nav className="topbar__nav" aria-label="Primary">
          <NavLink
            to="/"
            className={({ isActive }) =>
              isActive ? "topbar__link topbar__link--active" : "topbar__link"
            }
            end
          >
            Home
          </NavLink>
          <NavLink
            to="/marketplace"
            className={({ isActive }) =>
              isActive ? "topbar__link topbar__link--active" : "topbar__link"
            }
          >
            Market
          </NavLink>
          {currentUser ? (
            <NavLink
              to="/orders"
              className={({ isActive }) =>
                isActive ? "topbar__link topbar__link--active" : "topbar__link"
              }
            >
              Orders
            </NavLink>
          ) : null}
          <NavLink
            to="/community"
            className={({ isActive }) =>
              isActive ? "topbar__link topbar__link--active" : "topbar__link"
            }
          >
            Reviews
          </NavLink>
          {currentUser ? (
            <NavLink
              to="/profile"
              className={({ isActive }) =>
                isActive ? "topbar__link topbar__link--active" : "topbar__link"
              }
            >
              Profile
            </NavLink>
          ) : null}
        </nav>

        <div className="topbar__actions">
          {currentUser ? (
            <>
              <NavLink className="topbar__utility" to="/orders">
                Orders
              </NavLink>
              <div className="topbar__identity">
                <span>{currentUser.role}</span>
                <strong>{currentUser.email}</strong>
              </div>
              <button className="button button--ghost" type="button" onClick={onLogout}>
                Logout
              </button>
            </>
          ) : (
            <>
              <NavLink className="topbar__utility" to="/auth">
                Sign in
              </NavLink>
              <NavLink className="button button--ghost topbar__avatar" to="/auth">
                Login
              </NavLink>
            </>
          )}
        </div>
      </header>

      {statusMessage ? <div className="status-banner">{statusMessage}</div> : null}

      <main className="page-shell">{children}</main>
    </div>
  );
}
