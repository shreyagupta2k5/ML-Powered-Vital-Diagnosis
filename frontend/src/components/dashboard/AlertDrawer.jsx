// ============================================================
// AlertDrawer  (Phase 3 — Task 3.2)
// FIX: "Mark all read" now works properly —
//      marks each alert as read AND resets the bell badge
// ============================================================

import { useSelector, useDispatch } from "react-redux";
import { useNavigate }              from "react-router-dom";
import { markAllRead, clearAlerts } from "../../store/alertsSlice";

const ALERT_CONFIG = {
  HIGH_RISK:      { label: "High Risk",      color: "#B91C1C", bg: "#FEF2F2", icon: "🚨" },
  CRITICAL:       { label: "Critical",       color: "#7F1D1D", bg: "#FEF2F2", icon: "🔴" },
  DRIFT_DETECTED: { label: "Drift Detected", color: "#92400E", bg: "#FFFBEB", icon: "📊" },
  MODEL_UPDATED:  { label: "Model Updated",  color: "#1D4ED8", bg: "#EFF6FF", icon: "🔄" },
};

function timeAgo(isoString) {
  const diff = Math.floor((Date.now() - new Date(isoString)) / 1000);
  if (diff < 60)    return `${diff}s ago`;
  if (diff < 3600)  return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

export default function AlertDrawer({ isOpen, onClose }) {
  const dispatch    = useDispatch();
  const navigate    = useNavigate();
  const alerts      = useSelector((s) => s.alerts.alerts);
  const unreadCount = useSelector((s) => s.alerts.unreadCount);

  // FIX: "Mark all read" now dispatches markAllRead which sets unreadCount → 0
  // This makes the bell badge disappear AND shows a visual "all read" state
  function handleMarkAllRead() {
    dispatch(markAllRead());
  }

  function handleClear() {
    dispatch(clearAlerts());
  }

  function handleAlertClick(alert) {
    if (alert.patient_id) {
      dispatch(markAllRead()); // also mark read when navigating
      navigate(`/patient/${alert.patient_id}`);
      onClose();
    }
  }

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          onClick={onClose}
          style={{
            position: "fixed", inset: 0,
            background: "rgba(0,0,0,0.25)",
            zIndex: 200,
          }}
        />
      )}

      {/* Drawer */}
      <div style={{
        position: "fixed",
        top: 0, right: 0, bottom: 0,
        width: 360,
        background: "#fff",
        borderLeft: "1px solid #E8ECF0",
        zIndex: 201,
        display: "flex",
        flexDirection: "column",
        transform: isOpen ? "translateX(0)" : "translateX(100%)",
        transition: "transform 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
        boxShadow: isOpen ? "-8px 0 32px rgba(0,0,0,0.12)" : "none",
      }}>

        {/* Header */}
        <div style={{
          padding: "1rem 1.25rem",
          borderBottom: "1px solid #F0F4F8",
          display: "flex", alignItems: "center", justifyContent: "space-between",
        }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: "#111" }}>Live Alerts</div>
            <div style={{ fontSize: 11, color: "#999" }}>
              {alerts.length} total ·{" "}
              {/* FIX: Shows "all read" when unreadCount is 0 */}
              {unreadCount > 0
                ? <span style={{ color: "#E24B4A", fontWeight: 600 }}>{unreadCount} unread</span>
                : <span style={{ color: "#16A34A", fontWeight: 600 }}>all read ✓</span>
              }
            </div>
          </div>

          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            {/* FIX: Mark all read button — only shows when there are unread alerts */}
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                style={{
                  fontSize: 11, padding: "5px 10px",
                  border: "1px solid #E8ECF0",
                  borderRadius: 6, background: "#F8FAFC",
                  color: "#555", cursor: "pointer",
                  fontWeight: 500,
                }}
              >
                ✓ Mark all read
              </button>
            )}
            {/* Close button */}
            <button
              onClick={onClose}
              style={{
                fontSize: 18, padding: "2px 8px",
                color: "#aaa", border: "none", background: "none",
                cursor: "pointer", lineHeight: 1,
              }}
            >
              ×
            </button>
          </div>
        </div>

        {/* Alert list */}
        <div style={{ flex: 1, overflowY: "auto", padding: "0.5rem 0" }}>
          {alerts.length === 0 ? (
            <div style={{
              textAlign: "center", padding: "3rem 1rem",
              color: "#aaa", fontSize: 13,
            }}>
              <div style={{ fontSize: 28, marginBottom: 10 }}>🔔</div>
              No alerts yet.<br />Live alerts will appear here.
            </div>
          ) : (
            alerts.map((alert) => {
              const cfg = ALERT_CONFIG[alert.type] || ALERT_CONFIG.HIGH_RISK;
              return (
                <div
                  key={alert.id}
                  onClick={() => handleAlertClick(alert)}
                  style={{
                    padding: "10px 1.25rem",
                    borderBottom: "1px solid #F8FAFC",
                    cursor: alert.patient_id ? "pointer" : "default",
                    display: "flex", gap: 12, alignItems: "flex-start",
                    transition: "background 0.1s",
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = "#F8FAFC"}
                  onMouseLeave={e => e.currentTarget.style.background = "transparent"}
                >
                  <div style={{
                    width: 32, height: 32,
                    background: cfg.bg, borderRadius: 8,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 15, flexShrink: 0,
                  }}>
                    {cfg.icon}
                  </div>

                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{
                        fontSize: 11, fontWeight: 700,
                        color: cfg.color, background: cfg.bg,
                        borderRadius: 4, padding: "2px 7px",
                      }}>
                        {cfg.label}
                      </span>
                      <span style={{ fontSize: 10, color: "#bbb" }}>
                        {timeAgo(alert.timestamp)}
                      </span>
                    </div>
                    <div style={{ fontSize: 12, color: "#555", marginTop: 4 }}>
                      {alert.patient_id
                        ? <><strong>{alert.patient_id}</strong> — click to view</>
                        : "System-wide event"
                      }
                    </div>
                    {alert.risk_score != null && (
                      <div style={{ fontSize: 11, color: "#999", marginTop: 2 }}>
                        Risk score: {alert.risk_score.toFixed(2)}
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        {alerts.length > 0 && (
          <div style={{
            padding: "0.75rem 1.25rem",
            borderTop: "1px solid #F0F4F8",
            textAlign: "center",
          }}>
            <button
              onClick={handleClear}
              style={{
                fontSize: 12, color: "#aaa",
                border: "none", background: "none", cursor: "pointer",
              }}
            >
              Clear all alerts
            </button>
          </div>
        )}
      </div>
    </>
  );
}
