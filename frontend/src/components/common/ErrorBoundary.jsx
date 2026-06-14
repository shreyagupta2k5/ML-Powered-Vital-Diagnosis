// ============================================================
// ErrorBoundary — catches unexpected React errors
// Prevents the whole app from crashing on runtime errors
// ============================================================

import { Component } from "react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error("ErrorBoundary caught:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: "100vh",
          display: "flex", alignItems: "center", justifyContent: "center",
          background: "#F0F2F5",
          fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        }}>
          <div style={{
            background: "#fff", border: "1px solid #FECACA",
            borderRadius: 12, padding: "2rem",
            maxWidth: 420, textAlign: "center",
            boxShadow: "0 4px 24px rgba(0,0,0,0.06)",
          }}>
            <div style={{ fontSize: 36, marginBottom: 12 }}>⚠️</div>
            <h2 style={{ fontSize: 16, fontWeight: 700, color: "#B91C1C", marginBottom: 8 }}>
              Something went wrong
            </h2>
            <p style={{ fontSize: 13, color: "#888", marginBottom: 20 }}>
              An unexpected error occurred. Please refresh the page.
            </p>
            <button
              onClick={() => window.location.reload()}
              style={{
                background: "#E24B4A", color: "#fff",
                border: "none", borderRadius: 8,
                padding: "9px 20px", fontSize: 13,
                fontWeight: 600, cursor: "pointer",
              }}
            >
              Refresh page
            </button>
            {import.meta.env.DEV && (
              <pre style={{
                marginTop: 16, fontSize: 10,
                color: "#aaa", textAlign: "left",
                background: "#F8FAFC", borderRadius: 6,
                padding: 10, overflow: "auto",
              }}>
                {this.state.error?.toString()}
              </pre>
            )}
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}