import { NavLink, useLocation } from "react-router-dom";

export default function DashboardSidebar({ currentUser, activeSection, action = null }) {
  const isBuyer = currentUser?.role === "buyer";
  const location = useLocation();
  const links = isBuyer ? buyerLinks : sellerLinks;

  return (
    <aside className="dashboard-sidebar">
      <div className="dashboard-sidebar__brand">
        <strong>Harvest Market</strong>
        <span>{isBuyer ? "Neighbor Account" : "Digital Agrarian Member"}</span>
      </div>

      <nav className="dashboard-sidebar__nav" aria-label="Dashboard">
        {links.map((item) => (
          <NavLink
            key={item.key}
            className={() =>
              isActive(item, activeSection, location)
                ? "dashboard-link dashboard-link--active"
                : "dashboard-link"
            }
            to={item.to}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      {action}
    </aside>
  );
}

const buyerLinks = [
  { key: "orders", label: "My Orders", to: "/orders" },
  { key: "profile", label: "Neighbor Profile", to: "/profile" },
];

const sellerLinks = [
  { key: "orders", label: "Incoming Requests", to: "/orders" },
  { key: "profile", label: "Farm Profile", to: "/profile" },
];

function isActive(item, activeSection, location) {
  if (activeSection) {
    return item.key === activeSection;
  }

  if (item.to.includes("#")) {
    const [path, hash] = item.to.split("#");
    return location.pathname === path && location.hash === `#${hash}`;
  }

  return location.pathname === item.to;
}
