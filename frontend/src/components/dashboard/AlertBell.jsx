// ============================================================
// AlertBell  (Phase 3 — Task 3.2)
// File: src/components/dashboard/AlertBell.jsx
//
// WHAT THIS DOES:
//   - Shows a bell icon in the navbar
//   - Red badge shows how many unread alerts there are
//   - Clicking the bell opens/closes the AlertDrawer
// ============================================================

import { useSelector } from "react-redux";

export default function AlertBell({ onClick, isOpen }) {
  // Read unread count from Redux store
  const unreadCount = useSelector((s) => s.alerts.unreadCount);

  return (
    <button
      onClick={onClick}
      title="Alerts"
      style={{
        position: "relative",
        background: isOpen ? "#F8FAFC" : "none",
        border: "1px solid",
        borderColor: isOpen ? "#E8ECF0" : "transparent",
        borderRadius: 8,
        padding: "6px 9px",
        cursor: "pointer",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        transition: "all 0.15s",
      }}
    >
      {/* Bell icon (SVG so we don't need an icon library) */}
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
        stroke={unreadCount > 0 ? "#E24B4A" : "#888"} strokeWidth="2"
        strokeLinecap="round" strokeLinejoin="round">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
        <path d="M13.73 21a2 2 0 0 1-3.46 0" />
      </svg>

      {/* Red badge — only shows if there are unread alerts */}
      {unreadCount > 0 && (
        <span style={{
          position: "absolute",
          top: -5, right: -5,
          background: "#E24B4A",
          color: "#fff",
          borderRadius: "50%",
          width: 17, height: 17,
          fontSize: 10, fontWeight: 700,
          display: "flex", alignItems: "center", justifyContent: "center",
          border: "2px solid #fff",
          lineHeight: 1,
        }}>
          {unreadCount > 9 ? "9+" : unreadCount}
        </span>
      )}
    </button>
  );
}
