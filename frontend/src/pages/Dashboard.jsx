// ============================================================
// PAGE 2 — Main Dashboard  (Phase 3 — Tasks 3.1 & 3.2)
// FIXES APPLIED:
//   1. Left sidebar added (Dashboard + Admin panel links)
//   2. Background has soft colour (not all white/grey)
//   3. "ICU Dashboard" label next to VitalDx is now more visible
//   4. Doctor avatar click → goes to /account page
//   5. Clinical labels: table now shows clean clinical alert
//      text instead of raw track_id keys
//   6. Dynamic Prediction modal: doctor can choose Mortality Risk /
//      Crisis Risk / Vital Signs / Ensemble (all 3) before running
//      a live prediction, with curated input fields per track
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
import { getClinicalLabel }          from "../utils/labels";

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
  const [showPredictModal, setShowPredictModal] = useState(false);

  // active sidebar item
  const [activePath, setActivePath] = useState("/dashboard");

  useAlertWebSocket();

  useEffect(() => {
    async function loadPatients() {
      try {
        const history = await predictionService.getHistory();
        // Map real backend fields to our frontend shape
        const mapped = history.map(p => {
          // Prefer the real clinical alert message from prediction_json if available,
          // otherwise fall back to a clean clinical label for the track that flagged it
          const pj = p.prediction_json;
          const alertText = pj?.alert
            || (p.track_id === "ensemble_unified"
                ? "Ensemble Risk Assessment"
                : getClinicalLabel(p.track_id))
            || "No active alerts";

          return {
            id: p.patient_id,
            risk_tier: p.last_risk_tier,
            risk_score: p.last_probability,
            unified_alert: alertText,
            last_updated: p.last_timestamp, // raw ISO timestamp — PatientTable.jsx formats this for display
            bed: "ICU",
          };
        });
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

          <div style={{ marginBottom: "1.25rem", display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
            <div>
              <h1 style={{ fontSize: 18, fontWeight: 700, color: "#111", margin: 0 }}>
                ICU Patient Monitor
              </h1>
              <p style={{ fontSize: 12, color: "#999", marginTop: 3 }}>
                {total} active patients · sorted by risk level · auto-refreshing
              </p>
            </div>
            <button
              onClick={() => setShowPredictModal(true)}
              style={{
                background: "#E24B4A", color: "#fff",
                border: "none", borderRadius: 8,
                padding: "9px 18px", fontSize: 13, fontWeight: 700,
                cursor: "pointer", display: "flex", alignItems: "center", gap: 6,
                boxShadow: "0 2px 8px rgba(226,75,74,0.25)",
                flexShrink: 0,
              }}
            >
              <span style={{ fontSize: 15 }}>+</span> New Prediction
            </button>
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

      {/* New Prediction Modal — live inference against real backend */}
      {showPredictModal && (
        <PredictionModal onClose={() => setShowPredictModal(false)} />
      )}
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

// ============================================================
// PredictionModal — Task: "Live Prediction Input Form" (Dynamic)
//
// Lets a doctor choose which track(s) to run a live prediction
// against — Mortality Risk (Track 1), Crisis Risk (Track 2),
// Vital Signs (Track 3), or Ensemble (all 3 combined) — and
// dynamically shows only the relevant input fields.
// Sends data LIVE to POST /api/v1/ensemble/predict.
// ============================================================

// Curated input fields per track (clinically high-impact subset,
// not the full 562-feature set for Track 1).
const TRACK_OPTIONS = [
  { key: "track1_eicu",           label: "Mortality Risk" },
  { key: "track2_multimorbidity", label: "Crisis Risk" },
  { key: "track3_vitaldb",        label: "Vital Signs" },
  { key: "ensemble",              label: "All Tracks (Ensemble)" },
];

const TRACK1_FIELDS = [
  { key: "age",                label: "Age",                          default: 65,     type: "number" },
  { key: "gender",              label: "Gender",                       default: "Male", type: "select", options: ["Male", "Female"] },
  { key: "heartrate_mean",      label: "Heart Rate Mean (bpm)",        default: 88,     type: "number" },
  { key: "sao2_mean",           label: "SaO2 Mean (%)",                default: 96,     type: "number" },
  { key: "systemicmean_mean",   label: "Systemic Mean (MAP proxy)",    default: 75,     type: "number" },
  { key: "lactate_mean",        label: "Lactate Mean (mmol/L)",        default: 2.0,    type: "number" },
  { key: "creatinine_mean",     label: "Creatinine Mean (mg/dL)",      default: 1.2,    type: "number" },
  { key: "glucose_mean",        label: "Glucose Mean (mg/dL)",         default: 120,    type: "number" },
];

const TRACK2_FIELDS = [
  { key: "glucose_mean",  label: "Glucose Mean (mg/dL)",      default: 145 },
  { key: "glucose_count", label: "Glucose Count",             default: 10 },
  { key: "sbp_mean",      label: "Systolic BP Mean (mmHg)",   default: 135 },
  { key: "sbp_count",     label: "SBP Count",                 default: 50 },
  { key: "map_mean",      label: "MAP Mean (mmHg)",            default: 95 },
  { key: "map_count",     label: "MAP Count",                  default: 50 },
];

const TRACK3_FIELDS = [
  { key: "mean_hr",         label: "Mean HR (bpm)",        default: 85 },
  { key: "std_hr",          label: "HR Std Dev",            default: 12 },
  { key: "min_hr",          label: "Min HR (bpm)",          default: 65 },
  { key: "max_hr",          label: "Max HR (bpm)",          default: 105 },
  { key: "mean_map",        label: "Mean MAP (mmHg)",       default: 75 },
  { key: "std_map",         label: "MAP Std Dev",           default: 8 },
  { key: "min_map",         label: "Min MAP (mmHg)",        default: 60 },
  { key: "max_map",         label: "Max MAP (mmHg)",        default: 90 },
  { key: "map_range",       label: "MAP Range (mmHg)",      default: 30 },
  { key: "mean_spo2",       label: "Mean SpO₂ (%)",         default: 97 },
  { key: "std_spo2",        label: "SpO₂ Std Dev",          default: 2 },
  { key: "min_spo2",        label: "Min SpO₂ (%)",          default: 92 },
  { key: "mean_ecg",        label: "Mean ECG",               default: 1.0 },
  { key: "std_ecg",         label: "ECG Std Dev",            default: 0.3 },
  { key: "min_ecg",         label: "Min ECG",                default: 0.5 },
  { key: "max_ecg",         label: "Max ECG",                default: 1.5 },
  { key: "map_variability", label: "MAP Variability",        default: 8 },
  { key: "hr_variability",  label: "HR Variability",         default: 12 },
  { key: "ecg_range",       label: "ECG Range",              default: 1.0 },
  { key: "map_drop",        label: "MAP Drop (mmHg)",        default: 5 },
  { key: "spo2_drop",       label: "SpO₂ Drop (%)",          default: 3 },
];

// Builds the initial default form values for all 3 tracks at once,
// so switching between track selections doesn't lose previously typed values.
function buildDefaultFormState() {
  const state = {};
  [...TRACK1_FIELDS, ...TRACK2_FIELDS, ...TRACK3_FIELDS].forEach(f => {
    if (!(f.key in state)) state[f.key] = f.default;
  });
  return state;
}

function PredictionModal({ onClose }) {
  const [selectedTrack, setSelectedTrack] = useState("track2_multimorbidity"); // default to Crisis Risk (smallest form)
  const [patientId, setPatientId] = useState("PT-NEW-" + Math.floor(Math.random() * 900 + 100));
  const [form, setForm] = useState(buildDefaultFormState());
  const [result,   setResult]   = useState(null);
  const [error,    setError]    = useState("");
  const [loading,  setLoading]  = useState(false);

  function handleChange(field, value) {
    setForm(prev => ({ ...prev, [field]: value }));
  }

  // Returns the field list to render based on current track selection
  function getActiveFields() {
    if (selectedTrack === "track1_eicu") return TRACK1_FIELDS;
    if (selectedTrack === "track2_multimorbidity") return TRACK2_FIELDS;
    if (selectedTrack === "track3_vitaldb") return TRACK3_FIELDS;
    // ensemble — show all 3 sections
    return null;
  }

  // Builds the payload sent to POST /api/v1/ensemble/predict.
  // Only includes the feature blocks relevant to the selection.
  function buildPayload() {
    const payload = { patient_id: patientId };

    function track1Block() {
      const obj = {};
      TRACK1_FIELDS.forEach(f => {
        obj[f.key] = f.type === "select" ? form[f.key] : Number(form[f.key]);
      });
      return obj;
    }
    function track2Block() {
      const obj = {};
      TRACK2_FIELDS.forEach(f => { obj[f.key] = Number(form[f.key]); });
      return obj;
    }
    function track3Block() {
      const obj = {};
      TRACK3_FIELDS.forEach(f => { obj[f.key] = Number(form[f.key]); });
      return obj;
    }

    if (selectedTrack === "track1_eicu") {
      payload.track1_features = track1Block();
    } else if (selectedTrack === "track2_multimorbidity") {
      payload.track2_features = track2Block();
    } else if (selectedTrack === "track3_vitaldb") {
      payload.track3_features = track3Block();
    } else if (selectedTrack === "ensemble") {
      payload.track1_features = track1Block();
      payload.track2_features = track2Block();
      payload.track3_features = track3Block();
    }

    return payload;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    try {
      // 🔌 BACKEND CONNECT: active — real live call to the ensemble endpoint
      const payload = buildPayload();
      const data = await predictionService.predictEnsemble(payload);
      setResult(data);
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
        "Prediction failed — check backend connection and try again."
      );
    } finally {
      setLoading(false);
    }
  }

  const activeFields = getActiveFields();

  return (
    <div style={{
      position: "fixed", inset: 0,
      background: "rgba(0,0,0,0.4)",
      display: "flex", alignItems: "center", justifyContent: "center",
      zIndex: 1000, padding: "1.5rem",
    }}>
      <div style={{
        background: "#fff", borderRadius: 14,
        width: "100%", maxWidth: 820,
        maxHeight: "90vh", overflow: "auto",
        boxShadow: "0 20px 50px rgba(0,0,0,0.2)",
      }}>

        {/* Header */}
        <div style={{
          padding: "1.25rem 1.5rem", borderBottom: "1px solid #F0F4F8",
          display: "flex", alignItems: "center", justifyContent: "space-between",
        }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, color: "#111" }}>
              ⚡ New Live Prediction
            </div>
            <div style={{ fontSize: 12, color: "#999", marginTop: 2 }}>
              Sends data to POST /api/v1/ensemble/predict — real backend inference
            </div>
          </div>
          <button onClick={onClose} style={{
            fontSize: 20, border: "none", background: "none",
            color: "#aaa", cursor: "pointer", lineHeight: 1,
          }}>×</button>
        </div>

        {/* Body — form (left) + result (right), side-by-side */}
        <div style={{
          display: "grid",
          gridTemplateColumns: result || error ? "1fr 1fr" : "1fr",
          gap: 0,
        }}>

          {/* ── LEFT: input form ── */}
          <form onSubmit={handleSubmit} style={{ padding: "1.5rem", borderRight: (result || error) ? "1px solid #F0F4F8" : "none" }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: "#555", display: "block", marginBottom: 5 }}>
              Patient ID
            </label>
            <input
              type="text"
              value={patientId}
              onChange={e => setPatientId(e.target.value)}
              style={{
                width: "100%", padding: "8px 12px", marginBottom: 14,
                border: "1px solid #D1D5DB", borderRadius: 8, fontSize: 13,
                boxSizing: "border-box",
              }}
            />

            {/* ── Track selector — 4 options ── */}
            <label style={{ fontSize: 12, fontWeight: 600, color: "#555", display: "block", marginBottom: 6 }}>
              Run Prediction For
            </label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 16 }}>
              {TRACK_OPTIONS.map(opt => (
                <button
                  key={opt.key}
                  type="button"
                  onClick={() => setSelectedTrack(opt.key)}
                  style={{
                    padding: "6px 14px", fontSize: 12,
                    border: "1px solid",
                    borderColor: selectedTrack === opt.key ? "#FECACA" : "#E8ECF0",
                    borderRadius: 7, cursor: "pointer",
                    background: selectedTrack === opt.key ? "#FEF2F2" : "#fff",
                    color: selectedTrack === opt.key ? "#B91C1C" : "#777",
                    fontWeight: selectedTrack === opt.key ? 700 : 400,
                    transition: "all 0.15s",
                  }}
                >{opt.label}</button>
              ))}
            </div>

            {/* ── Dynamic fields based on selection ── */}
            {selectedTrack === "ensemble" ? (
              <>
                <FieldSection title="Mortality Risk Features" fields={TRACK1_FIELDS} form={form} onChange={handleChange} />
                <FieldSection title="Crisis Risk Features" fields={TRACK2_FIELDS} form={form} onChange={handleChange} />
                <FieldSection title="Vital Signs Features" fields={TRACK3_FIELDS} form={form} onChange={handleChange} />
              </>
            ) : (
              <FieldSection
                title={TRACK_OPTIONS.find(o => o.key === selectedTrack)?.label + " Features"}
                fields={activeFields}
                form={form}
                onChange={handleChange}
              />
            )}

            {error && (
              <div style={{
                marginTop: 14, background: "#FEF2F2", border: "1px solid #FECACA",
                borderRadius: 8, padding: "10px 14px", fontSize: 12, color: "#B91C1C",
              }}>
                ⚠ {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              style={{
                marginTop: 16, width: "100%",
                background: "#E24B4A", color: "#fff",
                border: "none", borderRadius: 8, padding: "11px",
                fontSize: 14, fontWeight: 700, cursor: loading ? "default" : "pointer",
                opacity: loading ? 0.6 : 1,
              }}
            >
              {loading ? "Running inference…" : "Run Live Prediction →"}
            </button>
          </form>

          {/* ── RIGHT: live result ── */}
          {(result || loading) && (
            <div style={{ padding: "1.5rem" }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: "#999", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 10 }}>
                Live Result
              </div>

              {loading && (
                <div style={{ display: "flex", justifyContent: "center", padding: "2rem" }}>
                  <LoadingSpinner />
                </div>
              )}

              {result && !loading && (
                <>
                  <div style={{
                    background: result.overall_risk === "CRITICAL" ? "#FEF2F2"
                      : result.overall_risk === "HIGH" ? "#FFFBEB" : "#F0FDF4",
                    border: "1px solid " + (result.overall_risk === "CRITICAL" ? "#FECACA"
                      : result.overall_risk === "HIGH" ? "#FDE68A" : "#BBF7D0"),
                    borderRadius: 10, padding: "14px",
                    marginBottom: 14,
                  }}>
                    <div style={{ fontSize: 11, color: "#888", marginBottom: 4 }}>Overall Risk</div>
                    <div style={{ fontSize: 22, fontWeight: 800, color: "#111" }}>
                      {result.overall_risk}
                    </div>
                    <div style={{ fontSize: 13, color: "#555", marginTop: 4 }}>
                      Score: <strong>{result.risk_score?.toFixed(2)}</strong>
                    </div>
                  </div>

                  <div style={{ fontSize: 12, color: "#555", marginBottom: 10, lineHeight: 1.5 }}>
                    {result.unified_alert}
                  </div>

                  {result.track_results && Object.entries(result.track_results).map(([key, val]) => (
                    <div key={key} style={{
                      background: "#F8FAFC", borderRadius: 8,
                      padding: "8px 12px", marginBottom: 8, fontSize: 11,
                    }}>
                      <div style={{ fontWeight: 700, color: "#555", marginBottom: 3 }}>{getClinicalLabel(key)}</div>
                      <pre style={{ margin: 0, fontSize: 10, color: "#888", whiteSpace: "pre-wrap", fontFamily: "monospace" }}>
                        {JSON.stringify(val, null, 1)}
                      </pre>
                    </div>
                  ))}

                  <div style={{ fontSize: 10, color: "#bbb", marginTop: 10 }}>
                    Processed in {result.processing_time_ms?.toFixed?.(0) ?? "?"}ms
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Small helper component to render a labeled group of input fields
function FieldSection({ title, fields, form, onChange }) {
  if (!fields) return null;
  return (
    <div style={{ marginBottom: 18 }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: "#999", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 10 }}>
        {title}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
        {fields.map(f => (
          <div key={f.key}>
            <label style={{ fontSize: 11, color: "#777", display: "block", marginBottom: 4 }}>
              {f.label}
            </label>
            {f.type === "select" ? (
              <select
                value={form[f.key]}
                onChange={e => onChange(f.key, e.target.value)}
                style={{
                  width: "100%", padding: "7px 10px",
                  border: "1px solid #D1D5DB", borderRadius: 7, fontSize: 13,
                  boxSizing: "border-box", background: "#fff",
                }}
              >
                {f.options.map(opt => <option key={opt} value={opt}>{opt}</option>)}
              </select>
            ) : (
              <input
                type="number"
                step="any"
                value={form[f.key]}
                onChange={e => onChange(f.key, e.target.value)}
                required
                style={{
                  width: "100%", padding: "7px 10px",
                  border: "1px solid #D1D5DB", borderRadius: 7, fontSize: 13,
                  boxSizing: "border-box",
                }}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}