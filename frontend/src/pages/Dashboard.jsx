// ============================================================
// PAGE 2 — Main Dashboard
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

import StatCard       from "../components/common/StatCard";
import AlertBanner    from "../components/common/AlertBanner";
import LoadingSpinner from "../components/common/LoadingSpinner";
import FilterBar      from "../components/dashboard/FilterBar";
import PatientTable   from "../components/dashboard/PatientTable";
import AlertBell      from "../components/dashboard/AlertBell";
import AlertDrawer    from "../components/dashboard/AlertDrawer";

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
  const [activePath, setActivePath] = useState("/dashboard");

  useAlertWebSocket();

  useEffect(() => {
    async function loadPatients() {
      try {
        const history = await predictionService.getHistory();
        const mapped = history.map(p => {
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
            last_updated: p.last_timestamp, 
            bed: "ICU",
            isNew: false 
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

  // NEW FEATURE: Handles successful live prediction and adds to top of table
  function handleNewPrediction(resultData, patientId) {
    const newPatient = {
      id: patientId,
      risk_tier: resultData.overall_risk || "MODERATE",
      risk_score: resultData.risk_score || 0.5,
      unified_alert: resultData.unified_alert || "Live Ensemble Assessment",
      last_updated: new Date().toISOString(),
      bed: "ICU (Live)",
      isNew: true // This triggers the NEW badge in the table
    };

    dispatch(setPatients([newPatient, ...patientList]));
    setSearch("");
    setActiveTier("All");
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
    <div style={{ minHeight: "100vh", background: "linear-gradient(135deg, #0a1c3f 0%, #eae9ef 50%, #936270 100%)",
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      display: "flex",
      flexDirection: "column",
    }}>
      <nav style={navStyle}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={logoBox}>♥</div>
          <span style={{ fontWeight: 800, fontSize: 15, color: "#111" }}>VitalDx</span>
          <span style={{ background: "linear-gradient(90deg, #E24B4A, #FF6B6B)", color: "#fff", fontSize: 11, fontWeight: 700, padding: "3px 10px", borderRadius: 20, letterSpacing: "0.04em", marginLeft: 4 }}>ICU DASHBOARD</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12, color: "#16A34A" }}><span style={{ width: 7, height: 7, borderRadius: "50%", background: "#16A34A", boxShadow: "0 0 0 3px rgba(22,163,74,0.2)", display: "inline-block" }} /> Live</div>
          <AlertBell onClick={() => setDrawerOpen(o => !o)} isOpen={drawerOpen} />
          <div onClick={() => alert(`👤 Logged in as: ${username}\n\nAccount settings page coming soon!\n(Route: /account)`)} title={`Signed in as ${username} — click for account`} style={{ ...avatarStyle, cursor: "pointer", transition: "transform 0.15s, box-shadow 0.15s" }} onMouseEnter={e => { e.currentTarget.style.transform = "scale(1.1)"; e.currentTarget.style.boxShadow = "0 0 0 3px rgba(29,78,216,0.2)"; }} onMouseLeave={e => { e.currentTarget.style.transform = "scale(1)"; e.currentTarget.style.boxShadow = "none"; }}>
            {username.slice(0, 2).toUpperCase()}
          </div>
          <button onClick={handleLogout} style={logoutBtn}>Sign out</button>
        </div>
      </nav>

      <div style={{ display: "flex", flex: 1 }}>
        <aside style={{ width: 200, background: "rgba(15, 23, 42, 0.35)", backdropFilter: "blur(10px)", borderRight: "1px solid rgba(255,255,255,0.15)", display: "flex", flexDirection: "column", paddingTop: "1.25rem", flexShrink: 0 }}>
          <div style={{ fontSize: 10, fontWeight: 800, color: "rgba(255,255,255,0.8)", letterSpacing: "0.1em", textTransform: "uppercase", padding: "0 1.25rem", marginBottom: 12 }}>Navigation</div>
          
          {NAV_ITEMS.map(item => {
            const isActive = activePath === item.path;
            return (
              <button 
                key={item.path} 
                onClick={() => handleNavClick(item.path)} 
                style={{ 
                  display: "flex", alignItems: "center", gap: 10, 
                  padding: "10px 1.25rem", margin: "2px 8px", 
                  borderRadius: 8, border: "none", 
                  background: isActive ? "linear-gradient(90deg, #E24B4A, #EF4444)" : "transparent", 
                  color: "#FFF", 
                  fontWeight: isActive ? 700 : 500, 
                  fontSize: 13, cursor: "pointer", textAlign: "left", transition: "all 0.15s", width: "calc(100% - 16px)",
                  boxShadow: isActive ? "0 4px 10px rgba(226, 75, 74, 0.3)" : "none",
                  opacity: isActive ? 1 : 0.85
                }} 
                onMouseEnter={e => { if (!isActive) { e.currentTarget.style.background = "rgba(255,255,255,0.1)"; e.currentTarget.style.opacity = "1"; } }} 
                onMouseLeave={e => { if (!isActive) { e.currentTarget.style.background = "transparent"; e.currentTarget.style.opacity = "0.85"; } }}
              >
                <span style={{ fontSize: 16 }}>{item.icon}</span><span>{item.label}</span>
              </button>
            );
          })}

          <div style={{ margin: "1.25rem 1.25rem", borderTop: "1px solid rgba(255,255,255,0.15)" }} />

          <div style={{ padding: "0 1.25rem" }}>
            <div style={{ fontSize: 10, fontWeight: 800, color: "rgba(255,255,255,0.8)", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 12 }}>Quick Stats</div>
            {[
              { label: "Critical", count: critical, color: "#FECACA", bg: "rgba(226, 75, 74, 0.4)" },
              { label: "High",     count: patientList.filter(p => p.risk_tier === "HIGH").length, color: "#FDE68A", bg: "rgba(245, 158, 11, 0.4)" },
              { label: "Moderate", count: moderate,  color: "#FED7AA", bg: "rgba(249, 115, 22, 0.4)" },
              { label: "Low",      count: low,        color: "#BBF7D0", bg: "rgba(34, 197, 94, 0.4)" },
            ].map(s => (
              <div key={s.label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                <span style={{ fontSize: 12, color: "#FFF", fontWeight: 500 }}>{s.label}</span>
                <span style={{ fontSize: 11, fontWeight: 800, background: s.bg, color: s.color, borderRadius: 6, padding: "3px 8px", minWidth: 26, textAlign: "center" }}>{loading ? "—" : s.count}</span>
              </div>
            ))}
          </div>
        </aside>

        <main style={{ flex: 1, padding: "1.5rem", overflow: "auto" }}>
          {showBanner && <AlertBanner message="Service Degraded" onDismiss={() => setShowBanner(false)} />}
          <div style={{ marginBottom: "1.25rem", display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
            <div>
              <h1 style={{ fontSize: 22, fontWeight: 800, color: "#FFF", margin: 0, letterSpacing: "0.02em" }}>ICU Patient Monitor</h1>
              <p style={{ fontSize: 13, color: "rgba(255,255,255,0.7)", marginTop: 4, fontWeight: 500 }}>{total} active patients · sorted by risk level · auto-refreshing</p>
            </div>
            <button onClick={() => setShowPredictModal(true)} style={{ background: "linear-gradient(90deg, #E24B4A, #EF4444)", color: "#fff", border: "none", borderRadius: 8, padding: "9px 18px", fontSize: 13, fontWeight: 700, cursor: "pointer", display: "flex", alignItems: "center", gap: 6, boxShadow: "0 4px 12px rgba(226,75,74,0.3)", flexShrink: 0 }}>
              <span style={{ fontSize: 15 }}>+</span> New Prediction
            </button>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: "1.25rem" }}>
            <StatCard title="Total patients"  value={loading ? "—" : total} subtitle="Active in ICU" />
            <StatCard title="Critical / High" value={loading ? "—" : critical} subtitle="Immediate attention" accentColor="#E24B4A" trend={critical > 2 ? "up" : undefined} />
            <StatCard title="Moderate risk"   value={loading ? "—" : moderate} subtitle="Monitoring required" accentColor="#F59E0B" />
            <StatCard title="Low risk"        value={loading ? "—" : low} subtitle="Stable condition" accentColor="#16A34A" />
          </div>

          <FilterBar search={search} onSearchChange={setSearch} activeTier={activeTier} onTierChange={setActiveTier} />

          {loading ? <div style={{ display: "flex", justifyContent: "center", padding: "4rem" }}><LoadingSpinner /></div> : <PatientTable patients={visible} />}
        </main>
      </div>

      <AlertDrawer isOpen={drawerOpen} onClose={() => setDrawerOpen(false)} />

      {/* Passing onSuccess up to handleNewPrediction */}
      {showPredictModal && <PredictionModal onClose={() => setShowPredictModal(false)} onSuccess={handleNewPrediction} />}
    </div>
  );
}

const navStyle = { background: "#fff", borderBottom: "1px solid #E8ECF0", padding: "0 1.5rem", height: 56, display: "flex", alignItems: "center", justifyContent: "space-between", position: "sticky", top: 0, zIndex: 100, boxShadow: "0 1px 4px rgba(0,0,0,0.05)" };
const logoBox = { width: 30, height: 30, background: "#E24B4A", borderRadius: 7, display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontSize: 14, fontWeight: 700 };
const avatarStyle = { width: 32, height: 32, borderRadius: "50%", background: "linear-gradient(135deg, #667eea, #764ba2)", color: "#fff", fontSize: 11, fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center", userSelect: "none" };
const logoutBtn = { fontSize: 12, padding: "5px 12px", border: "1px solid #E8ECF0", borderRadius: 7, background: "#fff", color: "#777", cursor: "pointer" };

// ============================================================
// PredictionModal 
// ============================================================
const TRACK_OPTIONS = [ { key: "track1_eicu", label: "Mortality Risk" }, { key: "track2_multimorbidity", label: "Crisis Risk" }, { key: "track3_vitaldb", label: "Vital Signs" }, { key: "ensemble", label: "All Tracks (Ensemble)" } ];
const TRACK1_FIELDS = [ { key: "age", label: "Age", default: 65, type: "number" }, { key: "gender", label: "Gender", default: "Male", type: "select", options: ["Male", "Female"] }, { key: "heartrate_mean", label: "Heart Rate Mean (bpm)", default: 88, type: "number" }, { key: "sao2_mean", label: "SaO2 Mean (%)", default: 96, type: "number" }, { key: "systemicmean_mean", label: "Systemic Mean (MAP proxy)", default: 75, type: "number" }, { key: "lactate_mean", label: "Lactate Mean (mmol/L)", default: 2.0, type: "number" }, { key: "creatinine_mean", label: "Creatinine Mean (mg/dL)", default: 1.2, type: "number" }, { key: "glucose_mean", label: "Glucose Mean (mg/dL)", default: 120, type: "number" } ];
const TRACK2_FIELDS = [ { key: "glucose_mean", label: "Glucose Mean (mg/dL)", default: 145 }, { key: "glucose_count", label: "Glucose Count", default: 10 }, { key: "sbp_mean", label: "Systolic BP Mean (mmHg)", default: 135 }, { key: "sbp_count", label: "SBP Count", default: 50 }, { key: "map_mean", label: "MAP Mean (mmHg)", default: 95 }, { key: "map_count", label: "MAP Count", default: 50 } ];
const TRACK3_FIELDS = [ { key: "mean_hr", label: "Mean HR (bpm)", default: 85 }, { key: "std_hr", label: "HR Std Dev", default: 12 }, { key: "min_hr", label: "Min HR (bpm)", default: 65 }, { key: "max_hr", label: "Max HR (bpm)", default: 105 }, { key: "mean_map", label: "Mean MAP (mmHg)", default: 75 }, { key: "std_map", label: "MAP Std Dev", default: 8 }, { key: "min_map", label: "Min MAP (mmHg)", default: 60 }, { key: "max_map", label: "Max MAP (mmHg)", default: 90 }, { key: "map_range", label: "MAP Range (mmHg)", default: 30 }, { key: "mean_spo2", label: "Mean SpO₂ (%)", default: 97 }, { key: "std_spo2", label: "SpO₂ Std Dev", default: 2 }, { key: "min_spo2", label: "Min SpO₂ (%)", default: 92 }, { key: "mean_ecg", label: "Mean ECG", default: 1.0 }, { key: "std_ecg", label: "ECG Std Dev", default: 0.3 }, { key: "min_ecg", label: "Min ECG", default: 0.5 }, { key: "max_ecg", label: "Max ECG", default: 1.5 }, { key: "map_variability", label: "MAP Variability", default: 8 }, { key: "hr_variability", label: "HR Variability", default: 12 }, { key: "ecg_range", label: "ECG Range", default: 1.0 }, { key: "map_drop", label: "MAP Drop (mmHg)", default: 5 }, { key: "spo2_drop", label: "SpO₂ Drop (%)", default: 3 } ];

function buildDefaultFormState() {
  const state = {};
  [...TRACK1_FIELDS, ...TRACK2_FIELDS, ...TRACK3_FIELDS].forEach(f => { if (!(f.key in state)) state[f.key] = f.default; });
  return state;
}

function PredictionModal({ onClose, onSuccess }) {
  const [selectedTrack, setSelectedTrack] = useState("track2_multimorbidity"); 
  const [patientId, setPatientId] = useState("PT-NEW-" + Math.floor(Math.random() * 900 + 100));
  const [form, setForm] = useState(buildDefaultFormState());
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleChange(field, value) { setForm(prev => ({ ...prev, [field]: value })); }

  function getActiveFields() {
    if (selectedTrack === "track1_eicu") return TRACK1_FIELDS;
    if (selectedTrack === "track2_multimorbidity") return TRACK2_FIELDS;
    if (selectedTrack === "track3_vitaldb") return TRACK3_FIELDS;
    return null;
  }

  function buildPayload() {
    const payload = { patient_id: patientId };
    function track1Block() { const obj = {}; TRACK1_FIELDS.forEach(f => { obj[f.key] = f.type === "select" ? form[f.key] : Number(form[f.key]); }); return obj; }
    function track2Block() { const obj = {}; TRACK2_FIELDS.forEach(f => { obj[f.key] = Number(form[f.key]); }); return obj; }
    function track3Block() { const obj = {}; TRACK3_FIELDS.forEach(f => { obj[f.key] = Number(form[f.key]); }); return obj; }

    if (selectedTrack === "track1_eicu") payload.track1_features = track1Block();
    else if (selectedTrack === "track2_multimorbidity") payload.track2_features = track2Block();
    else if (selectedTrack === "track3_vitaldb") payload.track3_features = track3Block();
    else if (selectedTrack === "ensemble") { payload.track1_features = track1Block(); payload.track2_features = track2Block(); payload.track3_features = track3Block(); }
    return payload;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true); setError(""); setResult(null);
    try {
      const payload = buildPayload();
      const data = await predictionService.predictEnsemble(payload);
      setResult(data);
      if (onSuccess) { onSuccess(data, patientId); }
    } catch (err) {
      setError(err?.response?.data?.detail || "Prediction failed.");
    } finally {
      setLoading(false);
    }
  }

  const activeFields = getActiveFields();

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000, padding: "1.5rem" }}>
      <div style={{ background: "#fff", borderRadius: 14, width: "100%", maxWidth: 680, maxHeight: "90vh", overflow: "auto", boxShadow: "0 20px 50px rgba(0,0,0,0.2)" }}>
        <div style={{ padding: "1.25rem 1.5rem", borderBottom: "1px solid #F0F4F8", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div><div style={{ fontSize: 16, fontWeight: 700, color: "#111" }}>⚡ New Live Prediction</div><div style={{ fontSize: 12, color: "#999", marginTop: 2 }}>Sends data to POST /api/v1/ensemble/predict</div></div>
          <button onClick={onClose} style={{ fontSize: 20, border: "none", background: "none", color: "#aaa", cursor: "pointer", lineHeight: 1 }}>×</button>
        </div>
        <div style={{ padding: "1.5rem" }}>
          <form onSubmit={handleSubmit}>
            <div style={{ display: "flex", gap: "1rem", marginBottom: 16 }}><div style={{ flex: 1 }}><label style={{ fontSize: 12, fontWeight: 600, color: "#555", display: "block", marginBottom: 5 }}>Patient ID</label><input type="text" value={patientId} onChange={e => setPatientId(e.target.value)} style={{ width: "100%", padding: "8px 12px", border: "1px solid #D1D5DB", borderRadius: 8, fontSize: 13, boxSizing: "border-box" }} /></div></div>
            <label style={{ fontSize: 12, fontWeight: 600, color: "#555", display: "block", marginBottom: 6 }}>Run Prediction For</label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 20 }}>
              {TRACK_OPTIONS.map(opt => ( <button key={opt.key} type="button" onClick={() => setSelectedTrack(opt.key)} style={{ padding: "6px 14px", fontSize: 12, border: "1px solid", borderColor: selectedTrack === opt.key ? "#FECACA" : "#E8ECF0", borderRadius: 7, cursor: "pointer", background: selectedTrack === opt.key ? "#FEF2F2" : "#fff", color: selectedTrack === opt.key ? "#B91C1C" : "#777", fontWeight: selectedTrack === opt.key ? 700 : 400, transition: "all 0.15s" }}>{opt.label}</button> ))}
            </div>
            <div style={{ background: "#F8FAFC", padding: "1rem", borderRadius: "8px", border: "1px solid #E2E8F0" }}>
              {selectedTrack === "ensemble" ? ( <> <FieldSection title="Mortality Risk Features" fields={TRACK1_FIELDS} form={form} onChange={handleChange} /> <FieldSection title="Crisis Risk Features" fields={TRACK2_FIELDS} form={form} onChange={handleChange} /> <FieldSection title="Vital Signs Features" fields={TRACK3_FIELDS} form={form} onChange={handleChange} /> </> ) : ( <FieldSection title={TRACK_OPTIONS.find(o => o.key === selectedTrack)?.label + " Features"} fields={activeFields} form={form} onChange={handleChange} /> )}
            </div>
            {error && <div style={{ marginTop: 14, background: "#FEF2F2", border: "1px solid #FECACA", borderRadius: 8, padding: "10px 14px", fontSize: 12, color: "#B91C1C" }}>⚠ {error}</div>}
            <button type="submit" disabled={loading} style={{ marginTop: 20, width: "100%", background: "#E24B4A", color: "#fff", border: "none", borderRadius: 8, padding: "12px", fontSize: 14, fontWeight: 700, cursor: loading ? "default" : "pointer", opacity: loading ? 0.6 : 1 }}>{loading ? "Running inference…" : "Run Live Prediction →"}</button>
          </form>
          {loading && <div style={{ display: "flex", justifyContent: "center", padding: "2rem" }}><LoadingSpinner /></div>}
          {result && !loading && (
            <div style={{ marginTop: "1.5rem", padding: "1.5rem", background: "#F8FAFC", borderRadius: "12px", border: "1px solid #E2E8F0" }}>
              <h3 style={{ fontSize: "16px", fontWeight: "bold", color: "#1E293B", marginBottom: "1rem", textAlign: "center", borderBottom: "1px solid #CBD5E1", paddingBottom: "10px" }}>Diagnostic Results</h3>
              {selectedTrack === 'ensemble' ? (
                <div style={{ background: "#EEF2FF", padding: "1.5rem", borderRadius: "8px", border: "1px solid #C7D2FE", display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center" }}>
                  <h4 style={{ fontSize: "14px", fontWeight: "600", color: "#312E81", marginBottom: "12px" }}>Combined Ensemble Analysis</h4>
                  <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginBottom: "8px" }}><span style={{ fontSize: "40px", fontWeight: "800", color: "#4338CA" }}>{result.risk_score !== undefined ? `${(result.risk_score * 100).toFixed(1)}%` : 'N/A'}</span><span style={{ fontSize: "14px", fontWeight: "500", color: "#6366F1" }}>Overall Risk</span></div>
                  <div style={{ fontSize: "15px", fontWeight: "700", color: result.overall_risk === "CRITICAL" ? "#DC2626" : result.overall_risk === "HIGH" ? "#D97706" : "#059669", marginBottom: "8px", padding: "4px 12px", background: "#fff", borderRadius: "20px", border: "1px solid #E0E7FF" }}>Tier: {result.overall_risk}</div>
                  <p style={{ fontSize: "13px", color: "#4F46E5", maxWidth: "400px", marginTop: "4px" }}>{result.unified_alert}</p>
                </div>
              ) : (
                <div style={{ background: "#FFFFFF", padding: "1.5rem", borderRadius: "8px", border: "1px solid #E2E8F0", display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center" }}>
                  <h4 style={{ fontSize: "14px", fontWeight: "600", color: "#334155", marginBottom: "12px" }}>{TRACK_OPTIONS.find(o => o.key === selectedTrack)?.label || "Model Result"}</h4>
                  <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginBottom: "8px" }}><span style={{ fontSize: "36px", fontWeight: "800", color: "#1E293B" }}>{result.risk_score !== undefined ? `${(result.risk_score * 100).toFixed(1)}%` : 'N/A'}</span><span style={{ fontSize: "14px", fontWeight: "500", color: "#64748B" }}>Predicted Risk</span></div>
                  <div style={{ fontSize: "15px", fontWeight: "700", color: result.overall_risk === "CRITICAL" ? "#DC2626" : result.overall_risk === "HIGH" ? "#D97706" : "#059669", marginBottom: "8px", padding: "4px 12px", background: "#F1F5F9", borderRadius: "20px" }}>Tier: {result.overall_risk}</div>
                  <p style={{ fontSize: "13px", color: "#64748B", maxWidth: "400px", marginTop: "4px" }}>{result.unified_alert}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function FieldSection({ title, fields, form, onChange }) {
  if (!fields) return null;
  return (
    <div style={{ marginBottom: 18 }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: "#64748B", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 10 }}>{title}</div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
        {fields.map(f => (
          <div key={f.key}>
            <label style={{ fontSize: 11, color: "#475569", display: "block", marginBottom: 4 }}>{f.label}</label>
            {f.type === "select" ? ( <select value={form[f.key]} onChange={e => onChange(f.key, e.target.value)} style={{ width: "100%", padding: "7px 10px", border: "1px solid #D1D5DB", borderRadius: 7, fontSize: 13, boxSizing: "border-box", background: "#fff" }}>{f.options.map(opt => <option key={opt} value={opt}>{opt}</option>)}</select> ) : ( <input type="number" step="any" value={form[f.key]} onChange={e => onChange(f.key, e.target.value)} required style={{ width: "100%", padding: "7px 10px", border: "1px solid #D1D5DB", borderRadius: 7, fontSize: 13, boxSizing: "border-box" }} /> )}
          </div>
        ))}
      </div>
    </div>
  );
}