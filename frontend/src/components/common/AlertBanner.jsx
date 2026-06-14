import { useState } from "react";

export default function AlertBanner({ message, onDismiss }) {
  const [visible, setVisible] = useState(true);

  if (!visible) return null;

  function dismiss() {
    setVisible(false);
    if (onDismiss) onDismiss();
  }

  return (
    <div style={{
      background: "#FEF2F2",
      border: "1px solid #FECACA",
      borderRadius: "9px",
      padding: "10px 16px",
      display: "flex",
      alignItems: "center",
      gap: "10px",
      fontSize: "13px",
      marginBottom: "1rem",
    }}>
      <span style={{ fontSize: 17 }}>⚠️</span>
      <span style={{ color: "#7F1D1D", flex: 1 }}>{message}</span>
      {/* 🔌 BACKEND CONNECT: this banner is triggered by 502 interceptor */}
      <span
        onClick={dismiss}
        style={{ cursor: "pointer", color: "#999", fontSize: 18 }}
      >×</span>
    </div>
  );
}