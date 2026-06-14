export default function RiskBadge({ level }) {
  const styles = {
    CRITICAL: { background: "#FEF2F2", color: "#B91C1C" },
    HIGH:     { background: "#FFFBEB", color: "#92400E" },
    MODERATE: { background: "#FFF7ED", color: "#9A3412" },
    LOW:      { background: "#F0FDF4", color: "#15803D" },
  };

  const style = styles[level] || styles.LOW;

  return (
    <span style={{
      ...style,
      borderRadius: "5px",
      padding: "3px 9px",
      fontSize: "11px",
      fontWeight: 600,
    }}>
      {level}
    </span>
  );
}