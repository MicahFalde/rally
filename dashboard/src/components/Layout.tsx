import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  BarChart3,
  Users,
  Map,
  ClipboardList,
  LogOut,
  Upload,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useCampaign } from "../context/CampaignContext";

export default function Layout() {
  const { user, logout } = useAuth();
  const { campaigns, activeCampaign, setActiveCampaign } = useCampaign();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const isAdmin = user?.platform_role === "platform_admin";

  const navItems = [
    { to: "/dashboard", label: "Dashboard", icon: BarChart3 },
    { to: "/voters", label: "Voters", icon: Users },
    { to: "/turfs", label: "Turfs", icon: Map },
    { to: "/surveys", label: "Surveys", icon: ClipboardList },
    ...(isAdmin
      ? [{ to: "/import", label: "Import Data", icon: Upload }]
      : []),
  ];

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <nav
        style={{
          width: 240,
          background: "#1a1a2e",
          color: "#fff",
          display: "flex",
          flexDirection: "column",
          padding: "16px 0",
        }}
      >
        <div style={{ padding: "0 16px 24px", borderBottom: "1px solid #333" }}>
          <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>Rally</h1>
          <p style={{ fontSize: 12, color: "#888", margin: "4px 0 0" }}>
            Field Operations
          </p>
        </div>

        {/* Campaign selector */}
        <div style={{ padding: "16px", borderBottom: "1px solid #333" }}>
          <label
            style={{ fontSize: 11, color: "#888", textTransform: "uppercase" }}
          >
            Campaign
          </label>
          <select
            value={activeCampaign?.id || ""}
            onChange={(e) => {
              const c = campaigns.find((c) => c.id === e.target.value);
              if (c) setActiveCampaign(c);
            }}
            style={{
              width: "100%",
              marginTop: 4,
              padding: "6px 8px",
              background: "#16213e",
              color: "#fff",
              border: "1px solid #333",
              borderRadius: 4,
              fontSize: 13,
            }}
          >
            {campaigns.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        {/* Nav links */}
        <div style={{ flex: 1, padding: "8px 0" }}>
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              style={({ isActive }) => ({
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "10px 16px",
                color: isActive ? "#fff" : "#999",
                background: isActive ? "#16213e" : "transparent",
                textDecoration: "none",
                fontSize: 14,
                borderLeft: isActive ? "3px solid #4361ee" : "3px solid transparent",
              })}
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </div>

        {/* User info + logout */}
        <div
          style={{
            padding: "12px 16px",
            borderTop: "1px solid #333",
            fontSize: 13,
          }}
        >
          <div style={{ color: "#ccc" }}>{user?.full_name}</div>
          <div style={{ color: "#666", fontSize: 11 }}>{user?.email}</div>
          <button
            onClick={handleLogout}
            style={{
              marginTop: 8,
              display: "flex",
              alignItems: "center",
              gap: 6,
              background: "none",
              border: "none",
              color: "#888",
              cursor: "pointer",
              padding: 0,
              fontSize: 12,
            }}
          >
            <LogOut size={14} />
            Sign out
          </button>
        </div>
      </nav>

      <main style={{ flex: 1, background: "#f5f5f5", padding: 24 }}>
        <Outlet />
      </main>
    </div>
  );
}
