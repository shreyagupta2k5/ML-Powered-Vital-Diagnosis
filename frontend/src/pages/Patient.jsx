// ============================================================
// PAGE 3 — Patient Detail View
// Route: /patient/:id
// File: src/pages/Patient.jsx
//
// WHAT THIS DOES:
//   - Gets patient ID from URL using useParams()
//   - Loads prediction data from predictionService (mock)
//   - Shows: CRITICAL banner, 3 track cards,
//            SHAP feature bars, vital sign sparklines
// ============================================================

import { useState, useEffect }      from "react";
import { useParams, useNavigate }   from "react-router-dom";
import { predictionService }         from "../api/predictionService";
import LoadingSpinner from "../components/common/LoadingSpinner";
import RiskBadge      from "../components/common/RiskBadge";
import { getClinicalLabel } from "../utils/labels";

// Color for SHAP bars by importance rank
function shapColor(i) {
  if (i < 2) return "#E24B4A";
  if (i < 4) return "#F59E0B";
  return "#60A5FA";
}

// Banner background by risk level
function bannerColor(risk) {
  if (risk === "CRITICAL") return { bg: "#FEF2F2", border: "#FECACA", text: "#B91C1C" };
  if (risk === "HIGH")     return { bg: "#FFFBEB", border: "#FDE68A", text: "#92400E" };
  if (risk === "MODERATE") return { bg: "#FFF7ED", border: "#FED7AA", text: "#9A3412" };
  return { bg: "#F0FDF4", border: "#BBF7D0", text: "#15803D" };
}

export default function PatientDetailPage() {
  const { id }    = useParams();     // grabs the :id from /patient/PT-007
  const navigate  = useNavigate();

  const [data,      setData]      = useState(null);
  const [loading,   setLoading]   = useState(true);

  useEffect(() => {
    setLoading(true);

    // 🔌 BACKEND CONNECT: get patient from history
    predictionService.getPatientById(id).then(patient => {
      if (!patient) {
        setData(null);
        setLoading(false);
        return;
      }

      const pj = patient.prediction_json; // real per-track data, may be null for old patients

      // Helper: pull a real track score, falling back to last_probability if missing
      function trackScore(trackKey) {
        if (pj?.track_scores && typeof pj.track_scores[trackKey] === "number") {
          return pj.track_scores[trackKey];
        }
        return patient.last_probability; // fallback for patients without prediction_json
      }

      const t1Score = trackScore("track1_eicu");
      const t2Score = trackScore("track2_multimorbidity");
      const t3Score = trackScore("track3_vitaldb");

      setData({
        patient_id: patient.patient_id,
        overall_risk: pj?.risk_tier || patient.last_risk_tier,
        risk_score: pj?.risk_score ?? patient.last_probability,
        unified_alert: pj?.alert || `${patient.last_risk_tier} — ${patient.track_id}`,
        timestamp: patient.last_timestamp,
        dominant_track: pj?.dominant_track || null,
        top_features: pj?.top_features || [], // currently always empty from backend
        has_prediction_json: !!pj,
        track_results: {
          track1_eicu: {
            mortality_probability: t1Score,
            risk_tier: patient.last_risk_tier,
          },
          track2_multimorbidity: {
            crisis_probability: t2Score,
            severity_level: patient.last_risk_tier,
            confidence_interval: [0, 0],
          },
          track3_vitaldb: {
            hypotension_probability: t3Score,
            tachycardia_probability: 0,
            spo2_drop_probability: t3Score,
            risk_level: patient.last_risk_tier,
          },
        },
      });
      setLoading(false);
    }).catch(() => {
      setData(null);
      setLoading(false);
    });
  }, [id]);

if (loading) return <LoadingSpinner fullPage />;

if (!data) return (
  <div style={{
    minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center",
    background: "#F0F2F5",
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  }}>
    <div style={{
      background: "#fff", border: "1px solid #E8ECF0",
      borderRadius: 12, padding: "2rem", maxWidth: 380, textAlign: "center",
    }}>
      <div style={{ fontSize: 36, marginBottom: 12 }}>🔍</div>
      <h2 style={{ fontSize: 16, fontWeight: 700, color: "#111", marginBottom: 8 }}>
        Patient not found
      </h2>
      <p style={{ fontSize: 13, color: "#888", marginBottom: 20 }}>
        No data found for patient <strong>{id}</strong>.
      </p>
      <button
        onClick={() => window.location.href = "/dashboard"}
        style={{
          background: "#E24B4A", color: "#fff",
          border: "none", borderRadius: 8,
          padding: "9px 20px", fontSize: 13,
          fontWeight: 600, cursor: "pointer",
        }}
      >
        ← Back to Dashboard
      </button>
    </div>
  </div>
);
  const bc        = bannerColor(data.overall_risk);
  const maxShap   = data.top_features[0]?.shap_value || 1;
  const t1        = data.track_results.track1_eicu;
  const t2        = data.track_results.track2_multimorbidity;
  const t3        = data.track_results.track3_vitaldb;

  return (
    <div style={{ background: "#F0F2F5", minHeight: "100vh",
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" }}>

      {/* ── MINI NAVBAR ── */}
      <nav style={{
        background: "#fff", borderBottom: "1px solid #E8ECF0",
        padding: "0 1.5rem", height: 52,
        display: "flex", alignItems: "center", justifyContent: "space-between",
        position: "sticky", top: 0, zIndex: 50,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <button
            onClick={() => navigate("/dashboard")}
            style={{
              background: "none", border: "1px solid #E8ECF0",
              borderRadius: 7, padding: "5px 12px",
              fontSize: 13, color: "#555", cursor: "pointer",
            }}
          >
            ← Dashboard
          </button>
          <span style={{ color: "#ddd" }}>|</span>
          <span style={{ fontWeight: 600, color: "#111", fontSize: 14 }}>
            Patient {data.patient_id}
          </span>
        </div>
        <button style={{
          fontSize: 12, padding: "5px 12px",
          border: "1px solid #E8ECF0", borderRadius: 7,
          background: "#fff", color: "#777", cursor: "pointer",
        }}>
          ↻ Re-run prediction
        </button>
      </nav>

      <div style={{ padding: "1.25rem" }}>

        {/* ── RISK BANNER ── */}
        <div style={{
          background: bc.bg, border: `1px solid ${bc.border}`,
          borderRadius: 12, padding: "14px 20px",
          display: "flex", alignItems: "center", gap: 14,
          marginBottom: "1.25rem",
          boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
        }}>
          <span style={{ fontSize: 24, flexShrink: 0 }}>
            {data.overall_risk === "CRITICAL" ? "🚨" : data.overall_risk === "HIGH" ? "⚠️" : "ℹ️"}
          </span>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700, fontSize: 14, color: bc.text }}>
              {data.unified_alert}
            </div>
            <div style={{ fontSize: 12, color: bc.text, opacity: 0.8, marginTop: 3 }}>
              Immediate ICU escalation recommended · Last updated {new Date(data.timestamp).toLocaleTimeString()}
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 30, fontWeight: 800, color: bc.text, lineHeight: 1 }}>
              {data.risk_score.toFixed(2)}
            </div>
            <div style={{ fontSize: 10, color: bc.text, opacity: 0.7, marginTop: 2 }}>
              ensemble score
            </div>
          </div>
        </div>

        {/* ── 3 TRACK CARDS ── */}
        <div style={{
          display: "grid", gridTemplateColumns: "repeat(3, 1fr)",
          gap: 12, marginBottom: "1.25rem",
        }}>

          {/* Track 1 — Mortality Risk */}
          <div style={{ ...cardStyle, borderTop: "3px solid #E24B4A" }}>
            <div style={cardLabel}>{getClinicalLabel("track1_eicu")}</div>
            <div style={{ fontSize: 28, fontWeight: 800, color: "#E24B4A", margin: "6px 0" }}>
              {Math.round(t1.mortality_probability * 100)}%
            </div>
            <RiskBadge level={t1.risk_tier} />
            <div style={{ marginTop: 10 }}>
              <MiniBar label="Mortality probability" value={t1.mortality_probability} color="#E24B4A" />
            </div>
          </div>

          {/* Track 2 — Crisis Risk */}
          <div style={{ ...cardStyle, borderTop: "3px solid #F59E0B" }}>
            <div style={cardLabel}>{getClinicalLabel("track2_multimorbidity")}</div>
            <div style={{ fontSize: 28, fontWeight: 800, color: "#F59E0B", margin: "6px 0" }}>
              {Math.round(t2.crisis_probability * 100)}%
            </div>
            <RiskBadge level={t2.severity_level} />
            <div style={{ marginTop: 10 }}>
              <MiniBar label="Crisis probability" value={t2.crisis_probability} color="#F59E0B" />
              <div style={{ fontSize: 11, color: "#aaa", marginTop: 6 }}>
                CI: [{t2.confidence_interval[0].toFixed(2)}, {t2.confidence_interval[1].toFixed(2)}] (90%)
              </div>
            </div>
          </div>

          {/* Track 3 — Vital Signs */}
          <div style={{ ...cardStyle, borderTop: "3px solid #60A5FA" }}>
            <div style={cardLabel}>{getClinicalLabel("track3_vitaldb")}</div>
            <RiskBadge level={t3.risk_level} />
            <div style={{ marginTop: 10 }}>
              <MiniBar label="SpO₂ Drop"   value={t3.spo2_drop_probability}   color="#E24B4A" />
              <MiniBar label="Tachycardia" value={t3.tachycardia_probability} color="#F59E0B" />
              <MiniBar label="Hypotension" value={t3.hypotension_probability} color="#22C55E" />
            </div>
          </div>
        </div>

        {/* ── BOTTOM: SHAP + Vitals ── */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>

          {/* SHAP Chart */}
          <div style={cardStyle}>
            <div style={{ fontWeight: 700, fontSize: 14, color: "#111", marginBottom: 4 }}>
              Top SHAP Feature Drivers
            </div>
            <div style={{ fontSize: 11, color: "#aaa", marginBottom: 14 }}>
              What caused this risk score — higher bar = more impact
            </div>
            {data.top_features.length === 0 && (
              <div style={{
                textAlign: "center", padding: "2rem 1rem",
                color: "#aaa", fontSize: 13,
              }}>
                📊 Feature importance data not available for this prediction.
              </div>
            )}
            {data.top_features.length > 0 && (() => {
              // Backend currently sends top_features as plain strings:
              //   ["glucose_mean", "sbp_mean", "map_mean"]
              // (ranked by importance, but no numeric magnitude yet).
              // Normalize to objects so the chart works either way —
              // if real shap_value numbers are added later, this still works.
              const normalized = data.top_features.map((f, i) =>
                typeof f === "string"
                  ? { feature: f, shap_value: null, rank: i }
                  : { feature: f.feature, shap_value: f.shap_value, rank: i }
              );
              const hasRealValues = normalized.every(f => typeof f.shap_value === "number");
              const maxVal = hasRealValues
                ? Math.max(...normalized.map(f => f.shap_value))
                : null;

              return normalized.map((f, i) => (
                <div key={f.feature} style={{
                  display: "flex", alignItems: "center", gap: 8, marginBottom: 9,
                }}>
                  <span style={{
                    width: 120, fontSize: 12, color: "#777",
                    textAlign: "right", flexShrink: 0, fontFamily: "monospace",
                  }}>
                    {f.feature}
                  </span>
                  <div style={{
                    flex: 1, height: 14,
                    background: "#F0F2F5", borderRadius: 4, overflow: "hidden",
                  }}>
                    <div style={{
                      // No real magnitude from backend yet — show descending
                      // bars by rank so #1 is fullest, #2 slightly less, etc.
                      width: hasRealValues
                        ? `${(f.shap_value / maxVal) * 100}%`
                        : `${100 - i * 20}%`,
                      height: "100%",
                      background: shapColor(i),
                      borderRadius: 4,
                      transition: "width 0.5s ease",
                    }} />
                  </div>
                  <span style={{ fontSize: 11, color: "#aaa", width: 32, textAlign: "right" }}>
                    {hasRealValues ? f.shap_value.toFixed(2) : `#${i + 1}`}
                  </span>
                </div>
              ));
            })()}
          </div>

          {/* Vital Signs */}
          <div style={cardStyle}>
            <div style={{ fontWeight: 700, fontSize: 14, color: "#111", marginBottom: 4 }}>
              Vital Signs
            </div>
            <div style={{ fontSize: 11, color: "#aaa", marginBottom: 14 }}>
              Time-series trend data
            </div>

            {/* 🔌 BACKEND CONNECT: No time-series endpoint exists yet.
                /api/v1/history only returns ONE latest snapshot per patient,
                not historical HR/MAP/SpO2 readings over time.
                When the backend adds a vitals time-series endpoint
                (e.g. GET /api/v1/patient/{id}/vitals?range=6h),
                replace this empty state with real VitalLine charts:

                <VitalLine label="Heart Rate (HR)" value={...} points={...} threshold={...} />
                <VitalLine label="MAP" value={...} points={...} threshold={...} />
                <VitalLine label="SpO2" value={...} points={...} threshold={...} />
            */}
            <div style={{
              textAlign: "center", padding: "2.5rem 1rem",
              color: "#aaa", fontSize: 13,
              background: "#FAFBFC", borderRadius: 8,
            }}>
              <div style={{ fontSize: 28, marginBottom: 10 }}>📉</div>
              <div style={{ fontWeight: 600, color: "#888", marginBottom: 4 }}>
                Vital sign trends not available
              </div>
              <div style={{ fontSize: 12, color: "#bbb", maxWidth: 280, margin: "0 auto" }}>
                Time-series HR / MAP / SpO₂ history isn't provided by the backend yet — only the latest snapshot per patient is stored.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────

function MiniBar({ label, value, color }) {
  return (
    <div style={{ marginBottom: 7 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#888", marginBottom: 3 }}>
        <span>{label}</span>
        <span style={{ color, fontWeight: 700 }}>{Math.round(value * 100)}%</span>
      </div>
      <div style={{ height: 5, background: "#EEF0F2", borderRadius: 3 }}>
        <div style={{
          width: `${value * 100}%`, height: "100%",
          background: color, borderRadius: 3, transition: "width 0.4s",
        }} />
      </div>
    </div>
  );
}

// VitalLine kept for when backend adds a real time-series endpoint —
// see the 🔌 BACKEND CONNECT note above for how to wire it back in.
function VitalLine({ label, value, valueColor, color, points, threshold }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{
        display: "flex", justifyContent: "space-between",
        fontSize: 12, color: "#888", marginBottom: 4,
      }}>
        <span>{label}</span>
        <span style={{ fontWeight: 700, color: valueColor || "#111" }}>{value}</span>
      </div>
      <svg viewBox="0 0 240 38" width="100%" height="38">
        <polyline points={points}
          fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
        <line x1="0" y1={threshold} x2="240" y2={threshold}
          stroke="#FCA5A5" strokeWidth="1" strokeDasharray="4,3" />
      </svg>
    </div>
  );
}

// ── Shared card style ──
const cardStyle = {
  background: "#fff",
  border: "1px solid #E8ECF0",
  borderRadius: 12,
  padding: "1.25rem",
  boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
};

const cardLabel = {
  fontSize: 11, fontWeight: 700, color: "#999",
  textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 4,
};