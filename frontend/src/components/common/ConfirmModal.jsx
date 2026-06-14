export default function ConfirmModal({ title, message, onConfirm, onCancel }) {
  return (
    <div style={{
      position: "fixed", inset: 0,
      background: "rgba(0,0,0,0.4)",
      display: "flex", alignItems: "center", justifyContent: "center",
      zIndex: 1000,
    }}>
      <div style={{
        background: "#fff",
        borderRadius: 12,
        padding: "2rem",
        width: 400,
        boxShadow: "0 20px 40px rgba(0,0,0,0.15)",
      }}>
        <h3 style={{ margin: "0 0 8px", fontSize: 16, color: "#111" }}>{title}</h3>
        <p style={{ margin: "0 0 1.5rem", fontSize: 13, color: "#666" }}>{message}</p>
        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
          <button onClick={onCancel} style={{
            padding: "8px 16px", borderRadius: 8,
            border: "1px solid #D1D5DB", background: "#fff",
            fontSize: 13, cursor: "pointer",
          }}>
            Cancel
          </button>
          <button onClick={onConfirm} style={{
            padding: "8px 16px", borderRadius: 8,
            border: "none", background: "#E24B4A",
            color: "#fff", fontSize: 13,
            fontWeight: 600, cursor: "pointer",
          }}>
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
}