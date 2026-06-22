// ============================================================
// PAGE 3 — Patient Detail View
// Route: /patient/:id
// File: src/pages/Patient.jsx
// ============================================================

import { useState, useEffect }      from "react";
import { useParams, useNavigate }   from "react-router-dom";
import { predictionService }        from "../api/predictionService";
import LoadingSpinner               from "../components/common/LoadingSpinner";
import RiskBadge                    from "../components/common/RiskBadge";
import { getClinicalLabel }         from "../utils/labels";
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, ReferenceLine 
} from "recharts";

function bannerColor(risk) {
  if (risk === "CRITICAL") return { bg: "#FEF2F2", border: "#FECACA", text: "#B91C1C" };
  if (risk === "HIGH")     return { bg: "#FFFBEB", border: "#FDE68A", text: "#92400E" };
  if (risk === "MODERATE") return { bg: "#FFF7ED", border: "#FED7AA", text: "#9A3412" };
  return { bg: "#F0FDF4", border: "#BBF7D0", text: "#15803D" };
}

export default function PatientDetailPage() {
  const { id }    = useParams();
  const navigate  = useNavigate();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [vitalsData, setVitalsData] = useState([]);
  const [vitalsRange, setVitalsRange] = useState("1h");
  const [vitalsLoading, setVitalsLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    predictionService.getPatientById(id).then(patient => {
      if (!patient) {
        setData(null);
        setLoading(false);
        return;
      }
      const pj = patient.prediction_json;
      function trackScore(trackKey) {
        if (pj?.track_scores && typeof pj.track_scores[trackKey] === "number") {
          return pj.track_scores[trackKey];
        }
        return patient.last_probability; 
      }
      setData({
        patient_id: patient.patient_id,
        overall_risk: pj?.risk_tier || patient.last_risk_tier,
        risk_score: pj?.risk_score ?? patient.last_probability,
        unified_alert: pj?.alert || `${patient.last_risk_tier} — ${patient.track_id}`,
        timestamp: patient.last_timestamp,
        dominant_track: pj?.dominant_track || null,
        top_features: pj?.top_features || [], 
        has_prediction_json: !!pj,
        track_results: {
          track1_eicu: { mortality_probability: trackScore("track1_eicu"), risk_tier: patient.last_risk_tier },
          track2_multimorbidity: { crisis_probability: trackScore("track2_multimorbidity"), severity_level: patient.last_risk_tier, confidence_interval: [0, 0] },
          track3_vitaldb: { hypotension_probability: trackScore("track3_vitaldb"), tachycardia_probability: 0, spo2_drop_probability: trackScore("track3_vitaldb"), risk_level: patient.last_risk_tier },
        },
      });
      setLoading(false);
    }).catch(() => {
      setData(null);
      setLoading(false);
    });
  }, [id]);

  useEffect(() => {
    async function fetchVitals() {
      setVitalsLoading(true);
      try {
        const response = await fetch(`http://localhost:8000/api/v1/patient/${id}/vitals?range=${vitalsRange}`);
        if (!response.ok) throw new Error("Vitals fetch failed");
        const json = await response.json();
        setVitalsData(json || []);
      } catch (err) {
        console.warn("Failed to load vitals:", err);
        setVitalsData([]);
      } finally {
        setVitalsLoading(false);
      }
    }
    fetchVitals();
  }, [id, vitalsRange]);

  if (loading) return <LoadingSpinner fullPage />;

  if (!data) return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#F0F2F5", fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" }}>
      <div style={{ background: "#fff", border: "1px solid #E8ECF0", borderRadius: 12, padding: "2rem", maxWidth: 380, textAlign: "center" }}>
        <div style={{ fontSize: 36, marginBottom: 12 }}>🔍</div>
        <h2 style={{ fontSize: 16, fontWeight: 700, color: "#111", marginBottom: 8 }}>Patient not found</h2>
        <p style={{ fontSize: 13, color: "#888", marginBottom: 20 }}>No data found for patient <strong>{id}</strong>.</p>
        <button onClick={() => navigate("/dashboard")} style={{ background: "#E24B4A", color: "#fff", border: "none", borderRadius: 8, padding: "9px 20px", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>← Back to Dashboard</button>
      </div>
    </div>
  );

  const bc = bannerColor(data.overall_risk);
  const t1 = data.track_results.track1_eicu;
  const t2 = data.track_results.track2_multimorbidity;
  const t3 = data.track_results.track3_vitaldb;

  return (
    <div style={{ background: "#F0F2F5", minHeight: "100vh", fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" }}>
      <nav style={{ background: "#fff", borderBottom: "1px solid #E8ECF0", padding: "0 1.5rem", height: 52, display: "flex", alignItems: "center", justifyContent: "space-between", position: "sticky", top: 0, zIndex: 50 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <button onClick={() => navigate("/dashboard")} style={{ background: "none", border: "1px solid #E8ECF0", borderRadius: 7, padding: "5px 12px", fontSize: 13, color: "#555", cursor: "pointer" }}>← Dashboard</button>
          <span style={{ color: "#ddd" }}>|</span>
          <span style={{ fontWeight: 600, color: "#111", fontSize: 14 }}>Patient {data.patient_id}</span>
        </div>
        <button style={{ fontSize: 12, padding: "5px 12px", border: "1px solid #E8ECF0", borderRadius: 7, background: "#fff", color: "#777", cursor: "pointer" }}>↻ Re-run prediction</button>
      </nav>

      <div style={{ padding: "1.25rem" }}>
        <div style={{ background: bc.bg, border: `1px solid ${bc.border}`, borderRadius: 12, padding: "14px 20px", display: "flex", alignItems: "center", gap: 14, marginBottom: "1.25rem", boxShadow: "0 2px 8px rgba(0,0,0,0.04)" }}>
          <span style={{ fontSize: 24, flexShrink: 0 }}>{data.overall_risk === "CRITICAL" ? "🚨" : data.overall_risk === "HIGH" ? "⚠️" : "ℹ️"}</span>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700, fontSize: 14, color: bc.text }}>{data.unified_alert}</div>
            <div style={{ fontSize: 12, color: bc.text, opacity: 0.8, marginTop: 3 }}>Immediate ICU escalation recommended · Last updated {new Date(data.timestamp).toLocaleTimeString()}</div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 30, fontWeight: 800, color: bc.text, lineHeight: 1 }}>{data.risk_score.toFixed(2)}</div>
            <div style={{ fontSize: 10, color: bc.text, opacity: 0.7, marginTop: 2 }}>ensemble score</div>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: "1.25rem" }}>
          <div style={{ ...cardStyle, borderTop: "3px solid #E24B4A" }}>
            <div style={cardLabel}>{getClinicalLabel("track1_eicu")}</div>
            <div style={{ fontSize: 28, fontWeight: 800, color: "#E24B4A", margin: "6px 0" }}>{Math.round(t1.mortality_probability * 100)}%</div>
            <RiskBadge level={t1.risk_tier} />
            <div style={{ marginTop: 10 }}><MiniBar label="Mortality probability" value={t1.mortality_probability} color="#E24B4A" /></div>
          </div>
          <div style={{ ...cardStyle, borderTop: "3px solid #F59E0B" }}>
            <div style={cardLabel}>{getClinicalLabel("track2_multimorbidity")}</div>
            <div style={{ fontSize: 28, fontWeight: 800, color: "#F59E0B", margin: "6px 0" }}>{Math.round(t2.crisis_probability * 100)}%</div>
            <RiskBadge level={t2.severity_level} />
            <div style={{ marginTop: 10 }}>
              <MiniBar label="Crisis probability" value={t2.crisis_probability} color="#F59E0B" />
              <div style={{ fontSize: 11, color: "#aaa", marginTop: 6 }}>CI: [{t2.confidence_interval[0].toFixed(2)}, {t2.confidence_interval[1].toFixed(2)}] (90%)</div>
            </div>
          </div>
          <div style={{ ...cardStyle, borderTop: "3px solid #60A5FA" }}>
            <div style={cardLabel}>{getClinicalLabel("track3_vitaldb")}</div>
            <RiskBadge level={t3.risk_level} />
            <div style={{ marginTop: 10 }}>
              <MiniBar label="SpO₂ Drop" value={t3.spo2_drop_probability} color="#E24B4A" />
              <MiniBar label="Tachycardia" value={t3.tachycardia_probability} color="#F59E0B" />
              <MiniBar label="Hypotension" value={t3.hypotension_probability} color="#22C55E" />
            </div>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div style={cardStyle}>
            <div style={{ fontWeight: 700, fontSize: 14, color: "#111", marginBottom: 4 }}>Top SHAP Feature Drivers</div>
            <div style={{ fontSize: 11, color: "#aaa", marginBottom: 14 }}>Red increases risk — Blue decreases risk</div>
            {data.top_features.length === 0 && <div style={{ textAlign: "center", padding: "2rem 1rem", color: "#aaa", fontSize: 13 }}>📊 Feature importance data not available.</div>}
            {data.top_features.length > 0 && (() => {
              const normalized = data.top_features.map((f, i) => typeof f === "string" ? { feature: f, shap_value: null, rank: i } : { feature: f.feature, shap_value: f.shap_value, rank: i });
              const hasRealValues = normalized.every(f => typeof f.shap_value === "number");
              const maxAbsVal = hasRealValues ? Math.max(...normalized.map(f => Math.abs(f.shap_value))) : 1;
              return normalized.map((f, i) => {
                const isPositive = !hasRealValues || f.shap_value >= 0;
                const barWidth = hasRealValues ? (Math.abs(f.shap_value) / maxAbsVal) * 100 : (100 - i * 20);
                return (
                  <div key={f.feature} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
                    <span style={{ width: 110, fontSize: 12, color: "#475569", textAlign: "right", flexShrink: 0, fontFamily: "monospace", fontWeight: 600 }}>{f.feature}</span>
                    <div style={{ flex: 1, display: "flex", alignItems: "center", height: 16, background: "transparent", position: "relative" }}>
                      {hasRealValues && <div style={{ position: "absolute", left: "50%", top: -4, bottom: -4, width: 2, background: "#E2E8F0", zIndex: 10, borderRadius: 2 }} />}
                      <div style={{ flex: 1, display: "flex", justifyContent: "flex-end", paddingRight: 2, height: "100%", alignItems: "center" }}>
                        {hasRealValues && !isPositive && <div style={{ width: `${barWidth}%`, height: "100%", background: "linear-gradient(90deg, #60A5FA, #3B82F6)", borderRadius: "4px 0 0 4px", transition: "width 0.5s ease" }} />}
                      </div>
                      <div style={{ flex: 1, display: "flex", justifyContent: "flex-start", paddingLeft: 2, height: "100%", alignItems: "center" }}>
                        {(!hasRealValues || isPositive) && <div style={{ width: `${barWidth}%`, height: "100%", background: "linear-gradient(90deg, #F87171, #EF4444)", borderRadius: "0 4px 4px 0", transition: "width 0.5s ease" }} />}
                      </div>
                    </div>
                    <span style={{ fontSize: 12, color: hasRealValues ? (isPositive ? "#EF4444" : "#3B82F6") : "#94A3B8", width: 45, textAlign: "left", fontWeight: 700 }}>
                      {hasRealValues ? `${isPositive ? "+" : ""}${f.shap_value.toFixed(2)}` : `#${i + 1}`}
                    </span>
                  </div>
                );
              });
            })()}
          </div>

          <div style={{ ...cardStyle, display: "flex", flexDirection: "column" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 14 }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: 14, color: "#111", marginBottom: 4 }}>Vital Signs</div>
                <div style={{ fontSize: 11, color: "#aaa" }}>Live telemetry history</div>
              </div>
              <div style={{ display: "flex", background: "#F0F2F5", borderRadius: 6, padding: 2 }}>
                {['1h', '6h', '24h'].map(range => (
                  <button key={range} onClick={() => setVitalsRange(range)} style={{ padding: "4px 10px", fontSize: 11, fontWeight: vitalsRange === range ? 700 : 500, color: vitalsRange === range ? "#111" : "#888", background: vitalsRange === range ? "#fff" : "transparent", border: "none", borderRadius: 4, cursor: "pointer", boxShadow: vitalsRange === range ? "0 1px 2px rgba(0,0,0,0.05)" : "none" }}>{range}</button>
                ))}
              </div>
            </div>
            {vitalsLoading ? <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}><LoadingSpinner /></div> 
            : vitalsData.length === 0 ? (
              <div style={{ textAlign: "center", padding: "2.5rem 1rem", color: "#aaa", fontSize: 13, background: "#FAFBFC", borderRadius: 8, marginTop: "auto", marginBottom: "auto" }}>
                <div style={{ fontSize: 28, marginBottom: 10 }}>📉</div>
                <div style={{ fontWeight: 600, color: "#888", marginBottom: 4 }}>Vital sign trends not available</div>
                <div style={{ fontSize: 12, color: "#bbb", maxWidth: 280, margin: "0 auto" }}>Time-series telemetry is not actively recorded for this patient.</div>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <VitalChart title="Heart Rate (bpm)" data={vitalsData} dataKey="hr" color="#E24B4A" threshold={100} domain={[40, 130]} />
                <VitalChart title="MAP (mmHg)" data={vitalsData} dataKey="map_val" color="#F59E0B" threshold={65} domain={[40, 120]} isLowThreshold />
                <VitalChart title="SpO₂ (%)" data={vitalsData} dataKey="spo2" color="#3B82F6" threshold={92} domain={[85, 100]} isLowThreshold />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function MiniBar({ label, value, color }) {
  return (
    <div style={{ marginBottom: 7 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#888", marginBottom: 3 }}>
        <span>{label}</span><span style={{ color, fontWeight: 700 }}>{Math.round(value * 100)}%</span>
      </div>
      <div style={{ height: 5, background: "#EEF0F2", borderRadius: 3 }}>
        <div style={{ width: `${value * 100}%`, height: "100%", background: color, borderRadius: 3, transition: "width 0.4s" }} />
      </div>
    </div>
  );
}

function VitalChart({ title, data, dataKey, color, threshold, domain }) {
  const latestValue = data.length > 0 ? data[data.length - 1][dataKey] : "--";
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "#888", marginBottom: 4 }}>
        <span>{title}</span><span style={{ fontWeight: 700, color: "#111" }}>{latestValue}</span>
      </div>
      <div style={{ height: 60, width: "100%" }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
            <XAxis dataKey="timestamp" hide />
            <YAxis domain={domain} axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#aaa" }} />
            <Tooltip labelFormatter={(label) => new Date(label).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #E8ECF0", boxShadow: "0 2px 8px rgba(0,0,0,0.05)" }} itemStyle={{ color: color, fontWeight: 600 }} />
            <ReferenceLine y={threshold} stroke="#FCA5A5" strokeDasharray="4 4" label={{ position: 'insideTopLeft', value: 'Alert', fill: '#FCA5A5', fontSize: 10 }} />
            <Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

const cardStyle = { background: "#fff", border: "1px solid #E8ECF0", borderRadius: 12, padding: "1.25rem", boxShadow: "0 1px 4px rgba(0,0,0,0.04)" };
const cardLabel = { fontSize: 11, fontWeight: 700, color: "#999", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 4 };