// ============================================================
// PAGE 4 — MLOps & Admin Panel
// Route: /admin/mlops
// File: src/pages/Admin.jsx
//
// WHAT THIS DOES:
//   - System health status (3 track dots)
//   - Drift monitor with PSI bars per feature
//   - Model registry with hot-swap button
// ============================================================

import { useState, useEffect } from "react";
import { useNavigate }         from "react-router-dom";
import { mlopsService }         from "../api/mlopsService";
import ConfirmModal             from "../components/common/ConfirmModal";
import LoadingSpinner           from "../components/common/LoadingSpinner";
import { getClinicalLabel }     from "../utils/labels";

// Unified track list — used for BOTH drift monitor and model registry
// Always in sequence: Track 1, Track 2, Track 3
const TRACKS = [
  { key: "track1_eicu",           label: "Track 1" },
  { key: "track2_multimorbidity", label: "Track 2" },
  { key: "track3_vitaldb",        label: "Track 3" },
];

export default function AdminPage() {
  const navigate = useNavigate();

  const [health,        setHealth]        = useState(null);
  const [driftData,     setDriftData]     = useState(null);
  const [regData,       setRegData]       = useState(null);
  const [selectedTrack, setSelectedTrack] = useState("track1_eicu"); // ONE selector drives both sections
  const [showModal,     setShowModal]     = useState(false);
  const [loading,       setLoading]       = useState(true);

  // Load health on mount, poll every 30s
  useEffect(() => {
    async function loadHealth() {
      try {
        const h = await mlopsService.getHealth();
        setHealth(h);
      } catch (e) {
        console.warn("Health load failed", e);
      } finally {
        setLoading(false);
      }
    }
    loadHealth();
    const interval = setInterval(loadHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  // Load drift when the unified track selector changes
  useEffect(() => {
    async function loadDrift() {
      try {
        const d = await mlopsService.getDriftStatus(selectedTrack);
        // Real backend returns data directly, mock returns nested under track ID
        setDriftData(d.metrics ? d : d[selectedTrack] || null);
      } catch (e) {
        console.warn("Drift load failed", e);
      }
    }
    loadDrift();
  }, [selectedTrack]);

  // Load model registry when the SAME unified track selector changes
  useEffect(() => {
    async function loadModel() {
      try {
        const m = await mlopsService.getActiveModel(selectedTrack);
        setRegData(m);
      } catch (e) {
        console.warn("Registry load failed", e);
      }
    }
    loadModel();
  }, [selectedTrack]);

  function handleHotSwap() {
    setShowModal(false);
    // 🔌 BACKEND CONNECT: POST /api/v1/registry/{regTrack}/hot-swap
    alert(`✅ Hot-swap triggered for ${getClinicalLabel(selectedTrack)}.\nIn production this will swap the live model.`);
  }

  return (
    <div style={{ minHeight: "100vh", background: "linear-gradient(135deg, #ffffff  0%,   #909ab0 50%, #936270 100%)",
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      display: "flex",
      flexDirection: "column",
    }}>

      {/* Navbar */}
      <nav style={{
        background: "#fff", borderBottom: "1px solid #E8ECF0",
        padding: "0 1.5rem", height: 52,
        display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={logoBox}>♥</div>
          <span style={{ fontWeight: 700, fontSize: 14 }}>VitalDx</span>
          <span style={{ color: "#ddd" }}>|</span>
          <span style={{ fontSize: 13, color: "#999" }}>MLOps & Admin</span>
        </div>
        <button onClick={() => navigate("/dashboard")} style={navBtn}>← Dashboard</button>
      </nav>

      <div style={{ padding: "1.5rem" }}>
        <h1 style={{ fontSize: 18, fontWeight: 700, color: "#111", margin: "0 0 4px" }}>
          MLOps & Admin Panel
        </h1>
        <p style={{ fontSize: 12, color: "#999", marginBottom: "1.25rem" }}>
          Monitor model health, data drift, and manage model versions
        </p>

        {/* ── UNIFIED TRACK SELECTOR — drives BOTH Drift Monitor and Model Registry below ── */}
        <div style={{
          background: "#fff", border: "1px solid #E8ECF0",
          borderRadius: 12, padding: "1rem 1.25rem",
          marginBottom: "1.25rem",
          display: "flex", alignItems: "center", gap: 14,
          boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
        }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: "#555" }}>
            🎯 Track Selector
          </span>
          <div style={{ display: "flex", gap: 6 }}>
            {TRACKS.map(t => (
              <button key={t.key}
                onClick={() => setSelectedTrack(t.key)}
                style={{
                  padding: "6px 16px", fontSize: 12,
                  border: "1px solid",
                  borderColor: selectedTrack === t.key ? "#BFDBFE" : "#E8ECF0",
                  borderRadius: 7, cursor: "pointer",
                  background: selectedTrack === t.key ? "#EFF6FF" : "#fff",
                  color: selectedTrack === t.key ? "#1D4ED8" : "#777",
                  fontWeight: selectedTrack === t.key ? 700 : 400,
                  transition: "all 0.15s",
                }}
              >{t.label}</button>
            ))}
          </div>
          <span style={{ fontSize: 11, color: "#aaa", marginLeft: "auto" }}>
            Currently viewing: <strong style={{ color: "#555" }}>{getClinicalLabel(selectedTrack)}</strong>
          </span>
        </div>

        {loading ? (
          <div style={{ display: "flex", justifyContent: "center", padding: "4rem" }}>
            <LoadingSpinner />
          </div>
        ) : (
          <>

          {/* ── SECTION 1: SYSTEM HEALTH ── */}
          <Section title="💓 System Health" subtitle="Auto-refreshing every 30 seconds">
            {health && (
              <>
                <div style={{
                  background: health.status === "healthy" ? "#F0FDF4" : "#FFFBEB",
                  border: `1px solid ${health.status === "healthy" ? "#BBF7D0" : "#FDE68A"}`,
                  borderRadius: 8, padding: "8px 14px",
                  fontSize: 12, fontWeight: 600,
                  color: health.status === "healthy" ? "#15803D" : "#92400E",
                  marginBottom: 14,
                  display: "flex", alignItems: "center", gap: 8,
                }}>
                  <span>{health.status === "healthy" ? "🟢" : "🟡"}</span>
                  Overall: {health.status.toUpperCase()}
                  <span style={{ fontWeight: 400, marginLeft: 8, opacity: 0.7 }}>
                    {health.timestamp ? `As of ${new Date(health.timestamp).toLocaleTimeString()}` : ""}
                  </span>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 10 }}>
                  {Object.entries(health.tracks).map(([key, t]) => {
                    // Real backend returns t as a string e.g. "healthy"
                    // Mock returns t as an object e.g. { status: "healthy", latency_ms: 142 }
                    const status = typeof t === "string" ? t : t.status;
                    const isHealthy = status === "healthy";
                    return (
                      <div key={key} style={{
                        background: "#F8FAFC", borderRadius: 10,
                        padding: "0.875rem 1rem",
                        display: "flex", alignItems: "flex-start", gap: 12,
                      }}>
                        <div style={{
                          width: 10, height: 10, borderRadius: "50%", marginTop: 3, flexShrink: 0,
                          background: isHealthy ? "#16A34A" : "#D97706",
                          boxShadow: `0 0 0 3px ${isHealthy ? "rgba(22,163,74,0.15)" : "rgba(217,119,6,0.15)"}`,
                        }} />
                        <div>
                          <div style={{ fontWeight: 600, fontSize: 13, color: "#111" }}>
                            {getClinicalLabel(key)}
                          </div>
                          <div style={{
                            fontSize: 11, marginTop: 2,
                            color: isHealthy ? "#16A34A" : "#D97706",
                          }}>
                            {status.charAt(0).toUpperCase() + status.slice(1)}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </Section>

          {/* ── SECTION 2: DRIFT MONITOR ── */}
          <Section title="📊 Drift Monitor"
            subtitle="PSI > 0.25 means the model is seeing data different from training">

            {driftData && (
              <>
                {/* No data checked at all yet for this track */}
                {(!driftData.metrics || driftData.metrics.length === 0) && (!driftData.features_checked || driftData.features_checked === 0) && (
                  <div style={{
                    textAlign: "center", padding: "2rem",
                    color: "#aaa", fontSize: 13,
                  }}>
                    📊 No drift metrics available for this track yet.
                  </div>
                )}

                {/* Backend checked features but didn't return per-feature breakdown — show a clean summary instead of a blank section */}
                {driftData.features_checked > 0 && (!driftData.metrics || driftData.metrics.length === 0) && (
                  <div style={{
                    background: "#F0FDF4", border: "1px solid #BBF7D0",
                    borderRadius: 8, padding: "10px 14px",
                    fontSize: 12, color: "#15803D",
                    display: "flex", alignItems: "center", gap: 8,
                  }}>
                    ✅ {driftData.features_checked} features checked — no drift detected (max PSI: {driftData.max_psi?.toFixed(2) ?? "0.00"}).
                  </div>
                )}

                {driftData.features_drifted > 0 && (
                  <div style={{
                    background: "#FFFBEB", border: "1px solid #FDE68A",
                    borderRadius: 8, padding: "8px 14px",
                    fontSize: 12, color: "#92400E", marginBottom: 14,
                    display: "flex", alignItems: "center", gap: 8,
                  }}>
                    ⚠️ <strong>{driftData.features_drifted} feature drifted</strong> —
                    PSI above 0.25 threshold. Consider retraining.
                  </div>
                )}

                {driftData.metrics && driftData.metrics.map(f => (
                  <div key={f.feature_name} style={{ marginBottom: 14 }}>
                    <div style={{
                      display: "flex", justifyContent: "space-between",
                      fontSize: 12, marginBottom: 4,
                    }}>
                      <span style={{ color: "#555" }}>{f.feature_name}</span>
                      <span style={{
                        fontWeight: 700,
                        color: f.alert_flag ? "#B91C1C" : "#555",
                      }}>
                        PSI {f.psi_score.toFixed(2)} {f.alert_flag ? "⚠" : ""}
                      </span>
                    </div>
                    <div style={{
                      height: 8, background: "#EEF0F2",
                      borderRadius: 4, overflow: "hidden", position: "relative",
                    }}>
                      {/* Threshold marker at 50% = PSI 0.25 */}
                      <div style={{
                        position: "absolute", left: "50%", top: 0, bottom: 0,
                        width: 2, background: "#F59E0B", zIndex: 1,
                      }} />
                      <div style={{
                        width: `${Math.min((f.psi_score / 0.5) * 100, 100)}%`,
                        height: "100%",
                        background: f.alert_flag ? "#E24B4A" : "#60A5FA",
                        borderRadius: 4,
                        transition: "width 0.5s ease",
                      }} />
                    </div>
                    <div style={{
                      display: "flex", justifyContent: "flex-end",
                      fontSize: 10, color: "#bbb", marginTop: 2, gap: 4,
                    }}>
                      <span style={{ display: "inline-block", width: 12, height: 2, background: "#F59E0B", verticalAlign: "middle" }} />
                      threshold: 0.25
                    </div>
                  </div>
                ))}
              </>
            )}
          </Section>

          {/* ── SECTION 3: MODEL REGISTRY ── */}
          <Section title="🗄️ Model Registry" subtitle="View active model versions and trigger hot-swap">
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 14 }}>
              <span style={{
                padding: "7px 14px", borderRadius: 8, fontSize: 13,
                background: "#F8FAFC", border: "1px solid #E8ECF0",
                color: "#111", fontWeight: 600,
              }}>
                {getClinicalLabel(selectedTrack)}
              </span>
              {regData && (
                <span style={{ fontSize: 12, color: "#aaa" }}>
                  {(regData.status || regData.deployment_status || "ACTIVE").toUpperCase()}
                </span>
              )}
            </div>

            {regData && (
              <>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10, marginBottom: 14 }}>
                  {[
                    { label: "AUC",      value: (regData.performance_metrics?.auc || regData.auc || 0).toFixed(2), good: true },
                    { label: "F1 Score", value: (regData.performance_metrics?.f1  || regData.f1  || 0).toFixed(2) },
                    { label: "Recall",   value: (regData.performance_metrics?.recall || regData.recall || 0).toFixed(2) },
                  ].map(m => (
                    <div key={m.label} style={{ background: "#F8FAFC", borderRadius: 8, padding: "0.75rem" }}>
                      <div style={{ fontSize: 11, color: "#888", marginBottom: 4 }}>{m.label}</div>
                      <div style={{ fontSize: 18, fontWeight: 700, color: m.good ? "#15803D" : "#111" }}>
                        {m.value}
                      </div>
                    </div>
                  ))}
                </div>

                <div style={{ display: "flex", alignItems: "center" }}>
                  <span style={{ fontSize: 12, color: "#888" }}>
                    Training date: {regData.training_date?.split("T")[0]} ·{" "}
                    <span style={{
                      background: "#F0FDF4", color: "#15803D",
                      borderRadius: 4, padding: "2px 8px", fontSize: 11,
                    }}>
                      {(regData.status || regData.deployment_status || "ACTIVE").toUpperCase()}
                    </span>
                  </span>
                  <button
                    onClick={() => setShowModal(true)}
                    style={{
                      marginLeft: "auto",
                      padding: "7px 16px", fontSize: 13,
                      border: "1px solid #FDE68A", borderRadius: 8,
                      background: "#FFFBEB", color: "#92400E", cursor: "pointer",
                      fontWeight: 600,
                    }}
                  >
                    ⚡ Hot-swap model
                  </button>
                </div>
              </>
            )}
          </Section>

          </>
        )}
      </div>

      {/* Hot-swap confirm modal */}
      {showModal && (
        <ConfirmModal
          title="Confirm Hot-Swap?"
          message={`This will replace the active ${getClinicalLabel(selectedTrack)} model with the staged version. The old model will be archived.`}
          onConfirm={handleHotSwap}
          onCancel={() => setShowModal(false)}
        />
      )}
    </div>
  );
}

// ── Helper components ──────────────────────────────────────────
function Section({ title, subtitle, children }) {
  return (
    <div style={{
      background: "#fff",
      border: "1px solid #E8ECF0",
      borderRadius: 12,
      padding: "1.25rem 1.5rem",
      marginBottom: "1.25rem",
      boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
    }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginBottom: 14 }}>
        <span style={{ fontSize: 14, fontWeight: 700, color: "#111" }}>{title}</span>
        {subtitle && <span style={{ fontSize: 11, color: "#aaa" }}>{subtitle}</span>}
      </div>
      {children}
    </div>
  );
}

const logoBox = {
  width: 28, height: 28, background: "#E24B4A", borderRadius: 6,
  display: "flex", alignItems: "center", justifyContent: "center",
  color: "#fff", fontSize: 13, fontWeight: 700,
};
const navBtn = {
  fontSize: 12, padding: "5px 12px",
  border: "1px solid #E8ECF0", borderRadius: 7,
  background: "#fff", color: "#777", cursor: "pointer",
};