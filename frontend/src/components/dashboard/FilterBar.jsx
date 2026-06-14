// ============================================================
// FilterBar  (Phase 3 — Task 3.1)
// File: src/components/dashboard/FilterBar.jsx
//
// WHAT THIS DOES:
//   - Text search box (filters by Patient ID as you type)
//   - Risk tier filter buttons (CRITICAL / HIGH / MODERATE / LOW / All)
//   - Passes the selected values UP to DashboardPage via props
// ============================================================

const TIERS = ["All", "CRITICAL", "HIGH", "MODERATE", "LOW"];

// Color for each tier button when active
const TIER_COLORS = {
  CRITICAL: { bg: "#FEF2F2", color: "#B91C1C", border: "#FECACA" },
  HIGH:     { bg: "#FFFBEB", color: "#92400E", border: "#FDE68A" },
  MODERATE: { bg: "#FFF7ED", color: "#9A3412", border: "#FED7AA" },
  LOW:      { bg: "#F0FDF4", color: "#15803D", border: "#BBF7D0" },
  All:      { bg: "#E24B4A", color: "#fff",    border: "#E24B4A" },
};

export default function FilterBar({ search, onSearchChange, activeTier, onTierChange }) {
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: 10,
      marginBottom: 14,
      flexWrap: "wrap",
    }}>
      {/* Search input */}
      <div style={{ position: "relative" }}>
        {/* Search icon */}
        <span style={{
          position: "absolute", left: 10, top: "50%",
          transform: "translateY(-50%)",
          color: "#bbb", fontSize: 14, pointerEvents: "none",
        }}>
          🔍
        </span>
        <input
          type="text"
          placeholder="Search Patient ID…"
          value={search}
          onChange={e => onSearchChange(e.target.value)}
          style={{
            paddingLeft: 32, paddingRight: 12,
            paddingTop: 8, paddingBottom: 8,
            border: "1px solid #E8ECF0",
            borderRadius: 8, fontSize: 13,
            width: 210, background: "#fff",
            color: "#111",
          }}
        />
      </div>

      {/* Divider */}
      <div style={{ width: 1, height: 24, background: "#E8ECF0" }} />

      {/* Risk tier filter pills */}
      <div style={{ display: "flex", gap: 6 }}>
        {TIERS.map(tier => {
          const isActive = activeTier === tier;
          const colors   = TIER_COLORS[tier] || TIER_COLORS.All;
          return (
            <button
              key={tier}
              onClick={() => onTierChange(tier)}
              style={{
                padding: "5px 12px",
                fontSize: 11, fontWeight: isActive ? 700 : 500,
                border: `1px solid ${isActive ? colors.border : "#E8ECF0"}`,
                borderRadius: 6,
                background: isActive ? colors.bg : "#fff",
                color: isActive ? colors.color : "#777",
                cursor: "pointer",
                transition: "all 0.15s",
              }}
            >
              {tier}
            </button>
          );
        })}
      </div>
    </div>
  );
}
