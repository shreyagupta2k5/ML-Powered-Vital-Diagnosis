// ============================================================
// PAGE 1 — Login Page  (Phase 2 — Task 2.1)
// Route: /login
// File: src/pages/Login.jsx
//
// WHAT THIS DOES:
//   - Shows username + password form
//   - Calls authService.login() (mock — no real backend)
//   - On success → dispatches setCredentials to Redux
//                → saves token to localStorage
//                → redirects to /dashboard
//   - If user is already logged in → redirects away from /login
//   - Shows inline error if credentials wrong
// ============================================================

import { useState } from "react";
import { useNavigate }   from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { setCredentials } from "../store/authSlice";
import { authService }    from "../api/authService";

export default function LoginPage() {
  const dispatch  = useDispatch();
  const navigate  = useNavigate();

  // If already logged in, skip login page entirely
  const isAuthenticated = useSelector((s) => s.auth.isAuthenticated);
  if (isAuthenticated) {
    navigate("/dashboard", { replace: true });
    return null;
  }

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error,    setError]    = useState("");
  const [loading,  setLoading]  = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      // authService.login() uses MOCK data — backend call is commented inside
      const data = await authService.login(username, password);

      // ── Save token to localStorage (for page refreshes) ──
      localStorage.setItem("access_token", data.access_token);

      // ── Save to Redux (for in-app usage) ──
      dispatch(setCredentials({ token: data.access_token, username: data.username }));

      // ── Go to dashboard ──
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError("Invalid credentials. Try again.");
      setLoading(false);
    }
  }

  return (
    <div style={pageStyle}>
      {/* Left decorative panel */}
      <div style={leftPanel}>
        <div style={brandMark}>
          <span style={heartIcon}>♥</span>
        </div>
        <h1 style={tagline}>ML-Powered<br />ICU Monitoring</h1>
        <p style={subTagline}>
          Real-time patient risk prediction<br />
          powered by AI — eICU · MIMIC · VitalDB
        </p>
        <div style={pillRow}>
          {["Track 1 — Mortality", "Track 2 — Crisis", "Track 3 — Waveforms"].map(t => (
            <span key={t} style={pill}>{t}</span>
          ))}
        </div>
      </div>

      {/* Right — login card */}
      <div style={rightPanel}>
        <div style={card}>
          {/* Logo */}
          <div style={logoRow}>
            <div style={logoBox}>♥</div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: "#111" }}>VitalDiagnosis</div>
              <div style={{ fontSize: 11, color: "#888" }}>ICU Monitoring System</div>
            </div>
          </div>

          <h2 style={{ fontSize: 22, fontWeight: 700, color: "#111", marginBottom: 4 }}>
            Sign in
          </h2>
          <p style={{ fontSize: 13, color: "#888", marginBottom: 24 }}>
            Enter your hospital credentials to continue
          </p>

          {/* Error box */}
          {error && (
            <div style={errorBox}>
              ⚠ {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <label style={label}>Username</label>
            <input
              type="text"
              placeholder="e.g. admin"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
              style={inputStyle}
            />

            <label style={label}>Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              style={inputStyle}
            />

            <button type="submit" disabled={loading} style={submitBtn}>
              {loading ? "Signing in…" : "Sign in →"}
            </button>
          </form>

          <div style={footerNote}>
            🔒 JWT protected · Rate limited · Audit logged
          </div>

          {/* Dev hint */}
          <div style={devHint}>
            💡 Dev mode: any username + password works
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Styles ────────────────────────────────────────────────────
const pageStyle = {
  minHeight: "100vh",
  display: "flex",
  background: "#F0F2F5",
  fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
};

const leftPanel = {
  flex: 1,
  background: "linear-gradient(145deg, #1a1a2e 0%, #16213e 60%, #E24B4A 150%)",
  display: "flex",
  flexDirection: "column",
  justifyContent: "center",
  padding: "3rem",
  color: "#fff",
};

const brandMark = {
  width: 56, height: 56,
  background: "rgba(226,75,74,0.25)",
  border: "1px solid rgba(226,75,74,0.5)",
  borderRadius: 14,
  display: "flex", alignItems: "center", justifyContent: "center",
  marginBottom: 32,
};

const heartIcon  = { fontSize: 26, color: "#E24B4A" };
const tagline    = { fontSize: 32, fontWeight: 700, lineHeight: 1.25, marginBottom: 14, color: "#fff" };
const subTagline = { fontSize: 14, color: "rgba(255,255,255,0.6)", lineHeight: 1.7, marginBottom: 28 };
const pillRow    = { display: "flex", flexDirection: "column", gap: 8 };
const pill       = {
  display: "inline-block",
  background: "rgba(255,255,255,0.08)",
  border: "1px solid rgba(255,255,255,0.15)",
  borderRadius: 6, padding: "5px 12px",
  fontSize: 12, color: "rgba(255,255,255,0.8)", width: "fit-content",
};

const rightPanel = {
  width: 440,
  display: "flex", alignItems: "center", justifyContent: "center",
  padding: "2rem",
  background: "#F0F2F5",
};

const card = {
  background: "#fff",
  border: "1px solid #E8ECF0",
  borderRadius: 16,
  padding: "2.25rem 2rem",
  width: "100%",
  boxShadow: "0 4px 24px rgba(0,0,0,0.06)",
};

const logoRow  = { display: "flex", alignItems: "center", gap: 10, marginBottom: 24 };
const logoBox  = {
  width: 38, height: 38, background: "#E24B4A", borderRadius: 9,
  display: "flex", alignItems: "center", justifyContent: "center",
  color: "#fff", fontSize: 17,
};

const label    = { display: "block", fontSize: 12, fontWeight: 600, color: "#555", marginBottom: 5 };
const inputStyle = {
  width: "100%", padding: "10px 12px", marginBottom: 14,
  border: "1px solid #D1D5DB", borderRadius: 9, fontSize: 14,
  color: "#111", background: "#fff", outline: "none",
  display: "block", boxSizing: "border-box",
};

const submitBtn = {
  width: "100%", background: "#E24B4A", color: "#fff",
  border: "none", borderRadius: 9, padding: "11px",
  fontSize: 14, fontWeight: 700, cursor: "pointer",
  marginTop: 4, transition: "background 0.2s",
};

const errorBox = {
  background: "#FEF2F2", border: "1px solid #FECACA",
  borderRadius: 8, padding: "10px 14px",
  fontSize: 13, color: "#B91C1C", marginBottom: 14,
};

const footerNote = {
  marginTop: 20, textAlign: "center",
  fontSize: 11, color: "#bbb",
  borderTop: "1px solid #F0F0F0", paddingTop: 14,
};

const devHint = {
  marginTop: 10, textAlign: "center",
  fontSize: 11, color: "#A3B0C0",
  background: "#F8FAFC", borderRadius: 6, padding: "6px 10px",
};
