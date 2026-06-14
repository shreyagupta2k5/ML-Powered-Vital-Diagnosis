export default function EmptyState({ icon = "📭", message = "No data available" }) {
  return (
    <div style={{
      textAlign: "center",
      padding: "3rem",
      color: "#aaa",
      fontSize: 13,
    }}>
      <div style={{ fontSize: 32, marginBottom: 12 }}>{icon}</div>
      <div>{message}</div>
    </div>
  );
}