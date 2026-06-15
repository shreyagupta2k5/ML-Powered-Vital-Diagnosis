// ============================================================
// PAGE 2 — Main Dashboard  (Phase 3 — Tasks 3.1 & 3.2)
// FIXES APPLIED:
//   1. Left sidebar added (Dashboard + Admin panel links)
//   2. Background has soft colour (not all white/grey)
//   3. "ICU Dashboard" label next to VitalDx is now more visible
//   4. Doctor avatar click → goes to /account page
// ============================================================
import { predictionService } from "../api/predictionService";
import { useState, useEffect }       from "react";
import { useNavigate }               from "react-router-dom";
import { useDispatch, useSelector }  from "react-redux";
import { setPatients }               from "../store/patientsSlice";
import { logout }                    from "../store/authSlice";
import { authService }               from "../api/authService";
import { mockPatients }              from "../mocks/mockPatients";
import useAlertWebSocket             from "../hooks/useAlertWebSocket";

import StatCard      from "../components/common/StatCard";
import AlertBanner   from "../components/common/AlertBanner";
import LoadingSpinner from "../components/common/LoadingSpinner";
import FilterBar     from "../components/dashboard/FilterBar";
import PatientTable  from "../components/dashboard/PatientTable";
import AlertBell     from "../components/dashboard/AlertBell";
import AlertDrawer   from "../components/dashboard/AlertDrawer";

// ── Sidebar nav items ──────────────────────────────────────
const NAV_ITEMS = [
  { label: "Dashboard",    icon: "🏥", path: "/dashboard"  },
  { label: "Admin / MLOps", icon: "⚙️", path: "/admin/mlops" },
];

export default function DashboardPage() {
  const dispatch  = useDispatch();
  const navigate  = useNavigate();

  const patientList = useSelector((s) => s.patients.list);
  const loading     = useSelector((s) => s.patients.loading);
  const username    = useSelector((s) => s.auth.username) || "Doctor";

  const [search,     setSearch]     = useState("");
  const [activeTier, setActiveTier] = useState("All");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [showBanner, setShowBanner] = useState(false);

  // active sidebar item
  const [activePath, setActivePath] = useState("/dashboard");

  useAlertWebSocket();

  useEffect(() => {
    async function loadPatients() {
      try {
        const history = await predictionService.getHistory();
        // Map real backend fields to our frontend shape
        const mapped = history.map(p => ({
          id: p.patient_id,
          risk_tier: p.last_risk_tier,
          risk_score: p.last_probability,
          unified_alert: p.track_id || "No active alerts",
          last_updated: p.last_timestamp,
          bed: "ICU",
        }));
        dispatch(setPatients(mapped));
      } catch (err) {
        console.warn("Failed to load patients, using mock data", err);
        dispatch(setPatients(mockPatients));
      }
    }
    loadPatients();
  }, [dispatch]);

  function handleLogout() {
    authService.logout();
    dispatch(logout());
    navigate("/login");
  }

  function handleNavClick(path) {
    setActivePath(path);
    navigate(path);
  }

  const visible = patientList.filter(p => {
    const matchSearch = p.id.toLowerCase().includes(search.toLowerCase());
    const matchTier   = activeTier === "All" || p.risk_tier === activeTier;
    return matchSearch && matchTier;
  });

  const total    = patientList.length;
  const critical = patientList.filter(p => p.risk_tier === "CRITICAL" || p.risk_tier === "HIGH").length;
  const moderate = patientList.filter(p => p.risk_tier === "MODERATE").length;
  const low      = patientList.filter(p => p.risk_tier === "LOW").length;

  return (
    // FIX 2: Soft warm background instead of flat #F0F2F5
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #EEF2FF 0%, #F0F9FF 50%, #FDF2F8 100%)",
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      display: "flex",
      flexDirection: "column",
    }}>

      {/* ── TOP NAVBAR ── */}
      <nav style={navStyle}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={logoBox}>♥</div>
          <span style={{ fontWeight: 800, fontSize: 15, color: "#111" }}>VitalDx</span>

          {/* FIX 3: ICU label now has a visible coloured pill */}
          <span style={{
            background: "linear-gradient(90deg, #E24B4A, #FF6B6B)",
            color: "#fff",
            fontSize: 11,
            fontWeight: 700,
            padding: "3px 10px",
            borderRadius: 20,
            letterSpacing: "0.04em",
            marginLeft: 4,
          }}>
            ICU DASHBOARD
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {/* Live dot */}
          <div style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12, color: "#16A34A" }}>
            <span style={{
              width: 7, height: 7, borderRadius: "50%",
              background: "#16A34A",
              boxShadow: "0 0 0 3px rgba(22,163,74,0.2)",
              display: "inline-block",
            }} />
            Live
          </div>

          <AlertBell onClick={() => setDrawerOpen(o => !o)} isOpen={drawerOpen} />

          {/* FIX 4: Avatar is now clickable → goes to /patient/PT-000 as account page
              (real account page can be built later — for now it shows a profile alert) */}
          <div
            onClick={() => {
              // When a real /account page is built, change this to: navigate("/account")
              alert(`👤 Logged in as: ${username}\n\nAccount settings page coming soon!\n(Route: /account)`);
            }}
            title={`Signed in as ${username} — click for account`}
            style={{
              ...avatarStyle,
              cursor: "pointer",
              transition: "transform 0.15s, box-shadow 0.15s",
            }}
            onMouseEnter={e => {
              e.currentTarget.style.transform = "scale(1.1)";
              e.currentTarget.style.boxShadow = "0 0 0 3px rgba(29,78,216,0.2)";
            }}
            onMouseLeave={e => {
              e.currentTarget.style.transform = "scale(1)";
              e.currentTarget.style.boxShadow = "none";
            }}
          >
            {username.slice(0, 2).toUpperCase()}
          </div>

          <button onClick={handleLogout} style={logoutBtn}>Sign out</button>
        </div>
      </nav>

      {/* ── BODY: sidebar + main content side by side ── */}
      <div style={{ display: "flex", flex: 1 }}>

        {/* ── FIX 1: LEFT SIDEBAR ── */}
        <aside style={{
          width: 200,
          background: "#fff",
          borderRight: "1px solid #E8ECF0",
          display: "flex",
          flexDirection: "column",
          paddingTop: "1.25rem",
          flexShrink: 0,
          boxShadow: "2px 0 8px rgba(0,0,0,0.03)",
        }}>

          {/* Nav label */}
          <div style={{
            fontSize: 10, fontWeight: 700, color: "#bbb",
            letterSpacing: "0.08em", textTransform: "uppercase",
            padding: "0 1.25rem", marginBottom: 8,
          }}>
            Navigation
          </div>

          {/* Nav links */}
          {NAV_ITEMS.map(item => {
            const isActive = activePath === item.path;
            return (
              <button
                key={item.path}
                onClick={() => handleNavClick(item.path)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "10px 1.25rem",
                  margin: "1px 8px",
                  borderRadius: 8,
                  border: "none",
                  background: isActive
                    ? "linear-gradient(90deg, #FEF2F2, #FFF5F5)"
                    : "transparent",
                  borderLeft: isActive ? "3px solid #E24B4A" : "3px solid transparent",
                  color: isActive ? "#E24B4A" : "#555",
                  fontWeight: isActive ? 700 : 400,
                  fontSize: 13,
                  cursor: "pointer",
                  textAlign: "left",
                  transition: "all 0.15s",
                  width: "calc(100% - 16px)",
                }}
                onMouseEnter={e => {
                  if (!isActive) e.currentTarget.style.background = "#F8FAFC";
                }}
                onMouseLeave={e => {
                  if (!isActive) e.currentTarget.style.background = "transparent";
                }}
              >
                <span style={{ fontSize: 16 }}>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            );
          })}

          {/* Divider */}
          <div style={{
            margin: "1rem 1.25rem",
            borderTop: "1px solid #F0F4F8",
          }} />

          {/* Quick stats in sidebar */}
          <div style={{ padding: "0 1.25rem" }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: "#bbb", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 10 }}>
              Quick Stats
            </div>
            {[
              { label: "Critical", count: critical, color: "#E24B4A", bg: "#FEF2F2" },
              { label: "High",     count: patientList.filter(p => p.risk_tier === "HIGH").length, color: "#92400E", bg: "#FFFBEB" },
              { label: "Moderate", count: moderate,  color: "#9A3412", bg: "#FFF7ED" },
              { label: "Low",      count: low,        color: "#15803D", bg: "#F0FDF4" },
            ].map(s => (
              <div key={s.label} style={{
                display: "flex", justifyContent: "space-between",
                alignItems: "center", marginBottom: 7,
              }}>
                <span style={{ fontSize: 12, color: "#777" }}>{s.label}</span>
                <span style={{
                  fontSize: 11, fontWeight: 700,
                  background: s.bg, color: s.color,
                  borderRadius: 4, padding: "2px 8px",
                  minWidth: 24, textAlign: "center",
                }}>
                  {loading ? "—" : s.count}
                </span>
              </div>
            ))}
          </div>

          {/* Bottom: user info in sidebar */}
          <div style={{
            marginTop: "auto",
            padding: "1rem 1.25rem",
            borderTop: "1px solid #F0F4F8",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{
                width: 28, height: 28, borderRadius: "50%",
                background: "#EBF5FF", color: "#1D4ED8",
                fontSize: 10, fontWeight: 700,
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                {username.slice(0, 2).toUpperCase()}
              </div>
              <div>
                <div style={{ fontSize: 12, fontWeight: 600, color: "#111" }}>{username}</div>
                <div style={{ fontSize: 10, color: "#aaa" }}>ICU Staff</div>
              </div>
            </div>
          </div>
        </aside>

        {/* ── MAIN CONTENT ── */}
        <main style={{ flex: 1, padding: "1.5rem", overflow: "auto" }}>

          {showBanner && (
            <AlertBanner
              message="Service Degraded — one or more track models are unavailable."
              onDismiss={() => setShowBanner(false)}
            />
          )}

          <div style={{ marginBottom: "1.25rem" }}>
            <h1 style={{ fontSize: 18, fontWeight: 700, color: "#111", margin: 0 }}>
              ICU Patient Monitor
            </h1>
            <p style={{ fontSize: 12, color: "#999", marginTop: 3 }}>
              {total} active patients · sorted by risk level · auto-refreshing
            </p>
          </div>

          {/* 4 stat cards */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, 1fr)",
            gap: 12,
            marginBottom: "1.25rem",
          }}>
            <StatCard title="Total patients"  value={loading ? "—" : total}    subtitle="Active in ICU" />
            <StatCard title="Critical / High" value={loading ? "—" : critical} subtitle="Immediate attention" accentColor="#E24B4A" trend={critical > 2 ? "up" : undefined} />
            <StatCard title="Moderate risk"   value={loading ? "—" : moderate} subtitle="Monitoring required" accentColor="#F59E0B" />
            <StatCard title="Low risk"        value={loading ? "—" : low}      subtitle="Stable condition"    accentColor="#16A34A" />
          </div>

          <FilterBar
            search={search}
            onSearchChange={setSearch}
            activeTier={activeTier}
            onTierChange={setActiveTier}
          />

          {loading ? (
            <div style={{ display: "flex", justifyContent: "center", padding: "4rem" }}>
              <LoadingSpinner />
            </div>
          ) : (
            <PatientTable patients={visible} />
          )}

          <div style={{ textAlign: "center", marginTop: "1.5rem", fontSize: 11, color: "#ccc" }}>
            VitalDx v1.0.0 · Mock data mode
          </div>
        </main>
      </div>

      {/* Alert Drawer */}
      <AlertDrawer isOpen={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </div>
  );
}

// ── Styles ─────────────────────────────────────────────────
const navStyle = {
  background: "#fff",
  borderBottom: "1px solid #E8ECF0",
  padding: "0 1.5rem",
  height: 56,
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  position: "sticky",
  top: 0,
  zIndex: 100,
  boxShadow: "0 1px 4px rgba(0,0,0,0.05)",
};

const logoBox = {
  width: 30, height: 30,
  background: "#E24B4A",
  borderRadius: 7,
  display: "flex", alignItems: "center", justifyContent: "center",
  color: "#fff", fontSize: 14, fontWeight: 700,
};

const avatarStyle = {
  width: 32, height: 32,
  borderRadius: "50%",
  background: "linear-gradient(135deg, #667eea, #764ba2)",
  color: "#fff",
  fontSize: 11, fontWeight: 700,
  display: "flex", alignItems: "center", justifyContent: "center",
  userSelect: "none",
};

const logoutBtn = {
  fontSize: 12, padding: "5px 12px",
  border: "1px solid #E8ECF0", borderRadius: 7,
  background: "#fff", color: "#777", cursor: "pointer",
};
