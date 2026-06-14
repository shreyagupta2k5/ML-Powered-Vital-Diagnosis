export default function StatCard({ title, value, subtitle, trend, accentColor }) {
  return (
    <div style={{
      background: "#fff",
      border: "1px solid #E8ECF0",
      borderLeft: accentColor ? `3px solid ${accentColor}` : "1px solid #E8ECF0",
      borderRadius: "10px",
      padding: "1rem",
    }}>
      <div style={{ fontSize: 11, color: "#888", marginBottom: 5 }}>{title}</div>
      <div style={{ fontSize: 24, fontWeight: 600, color: accentColor || "#111" }}>
        {value}
        {trend && (
          <span style={{ fontSize: 13, marginLeft: 6, color: trend === "up" ? "#16A34A" : "#DC2626" }}>
            {trend === "up" ? "▲" : "▼"}
          </span>
        )}
      </div>
      {subtitle && <div style={{ fontSize: 11, color: "#aaa", marginTop: 4 }}>{subtitle}</div>}
    </div>
  );
}