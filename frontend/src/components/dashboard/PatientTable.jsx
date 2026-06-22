// ============================================================
// PatientTable  (Phase 3 — Task 3.1)
// File: src/components/dashboard/PatientTable.jsx
//
// WHAT THIS DOES:
//   - Renders the patient list as a table
//   - Color-coded risk badges
//   - Progress bar for risk score
//   - Clicking a row navigates to /patient/:id
//   - Critical/High alert rows pulse with a red border
//   - Empty state if no patients match the filter
//   - NEW: Displays a "NEW" badge for live predictions
// ============================================================

import { useNavigate }   from "react-router-dom";
import { useSelector }   from "react-redux";
import RiskBadge         from "../common/RiskBadge";
import EmptyState        from "../common/EmotyState";   // note: your friend spelled it EmotyState

// Risk order for sorting: CRITICAL first
const RISK_ORDER = { CRITICAL: 0, HIGH: 1, MODERATE: 2, LOW: 3 };

// Color for the progress bar fill
function riskBarColor(tier) {
  if (tier === "CRITICAL") return "#E24B4A";
  if (tier === "HIGH")     return "#F59E0B";
  if (tier === "MODERATE") return "#FB923C";
  return "#22C55E";
}

// Formats backend UTC timestamp into relative time ("2m ago") for recent
// updates, or a full local date+time string for anything older than a day.
// new Date(isoString) automatically converts UTC → the browser's local timezone.
function timeAgo(isoString) {
  const date = new Date(isoString);
  const diff = Math.floor((Date.now() - date) / 1000);
  if (diff < 60)    return `${diff}s ago`;
  if (diff < 3600)  return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return date.toLocaleString(); // local date + time, not just date
}

export default function PatientTable({ patients }) {
  const navigate = useNavigate();

  // Get live alerts from Redux — we use this to flash CRITICAL rows
  const liveAlerts = useSelector((s) => s.alerts.alerts);
  const criticalIds = new Set(
    liveAlerts
      .filter(a => a.type === "HIGH_RISK" || a.type === "CRITICAL")
      .map(a => a.patient_id)
  );

  // Sort by risk order (CRITICAL first)
  const sorted = [...patients].sort(
    (a, b) => (RISK_ORDER[a.risk_tier] ?? 9) - (RISK_ORDER[b.risk_tier] ?? 9)
  );

  if (sorted.length === 0) {
    return <EmptyState icon="🔍" message="No patients match your search or filter." />;
  }

  return (
    <div style={{
      background: "#fff",
      border: "1px solid #E8ECF0",
      borderRadius: 12,
      overflow: "hidden",
    }}>
      <table style={{
        width: "100%", borderCollapse: "collapse",
        fontSize: 13, tableLayout: "fixed",
      }}>
        <thead>
          <tr style={{ background: "#F8FAFC" }}>
            <th style={th}>Patient ID</th>
            <th style={th}>Risk Level</th>
            <th style={th}>Risk Score</th>
            <th style={th}>Alert</th>
            <th style={th}>Bed</th>
            <th style={th}>Last Updated</th>
            <th style={{ ...th, width: 30 }}></th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((p, i) => {
            const isLive = criticalIds.has(p.id);   // does this row have a live alert?
            const isLast = i === sorted.length - 1;

            return (
              <tr
                key={p.id}
                onClick={() => navigate(`/patient/${p.id}`)}
                style={{
                  borderTop: "1px solid #F0F4F8",
                  borderLeft: isLive ? "3px solid #E24B4A" : "3px solid transparent",
                  cursor: "pointer",
                  transition: "background 0.1s",
                  background: isLive ? "#FFFAF9" : "transparent",
                  ...(isLast ? { borderBottom: "none" } : {}),
                }}
                onMouseEnter={e => e.currentTarget.style.background = isLive ? "#FFF5F5" : "#F8FAFC"}
                onMouseLeave={e => e.currentTarget.style.background = isLive ? "#FFFAF9" : "transparent"}
              >
                <td style={td}>
                  <div style={{ display: "flex", alignItems: "center" }}>
                    <span style={{ fontWeight: 700, color: "#111" }}>{p.id}</span>
                    {/* NEW BADGE ADDED HERE */}
                    {p.isNew && (
                      <span style={{ 
                        background: "#3B82F6", 
                        color: "#fff", 
                        padding: "2px 6px", 
                        borderRadius: "4px", 
                        fontSize: "10px", 
                        fontWeight: "bold", 
                        marginLeft: "8px",
                        letterSpacing: "0.05em"
                      }}>
                        NEW
                      </span>
                    )}
                  </div>
                </td>
                <td style={td}>
                  <RiskBadge level={p.risk_tier} />
                </td>
                <td style={td}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <div style={{
                      flex: 1, height: 6,
                      background: "#EEF0F2", borderRadius: 3, overflow: "hidden",
                    }}>
                      <div style={{
                        width: `${Math.min(p.risk_score * 100, 100)}%`,
                        height: "100%",
                        background: riskBarColor(p.risk_tier),
                        borderRadius: 3,
                        transition: "width 0.4s ease",
                      }} />
                    </div>
                    <span style={{ fontSize: 12, color: "#777", width: 32, textAlign: "right" }}>
                      {p.risk_score.toFixed(2)}
                    </span>
                  </div>
                </td>
                <td style={{ ...td, color: "#777", fontSize: 12, maxWidth: 200 }}>
                  <span style={{
                    display: "block",
                    overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                  }}>
                    {p.unified_alert}
                  </span>
                </td>
                <td style={{ ...td, color: "#999", fontSize: 12 }}>{p.bed}</td>
                <td style={{ ...td, color: "#bbb", fontSize: 12 }}>
                  {timeAgo(p.last_updated)}
                </td>
                <td style={{ ...td, color: "#ccc", textAlign: "center" }}>›</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

const th = {
  padding: "10px 16px",
  textAlign: "left",
  fontWeight: 600,
  fontSize: 11,
  color: "#888",
  borderBottom: "1px solid #E8ECF0",
  letterSpacing: "0.03em",
  textTransform: "uppercase",
};

const td = {
  padding: "12px 16px",
  verticalAlign: "middle",
  color: "#111",
};