// ============================================================
// MOCK DATA — System Health
// File: src/mocks/mockHealth.js
//
// This matches GET /health response shape
// Shows which AI tracks are working and which have issues
// ============================================================

export const mockHealth = {
  status: "degraded",   // overall: "healthy" | "degraded" | "down"
  uptime_seconds: 86400,
  tracks: {
    track1_eicu: {
      status: "healthy",
      model_loaded: true,
      version: "v1.0.0",
      last_prediction: "2026-06-08T10:04:55Z",
      latency_ms: 142,
    },
    track2_multimorbidity: {
      status: "healthy",
      model_loaded: true,
      version: "v4.0.0",
      last_prediction: "2026-06-08T10:04:58Z",
      latency_ms: 8,
    },
    track3_vitaldb: {
      status: "degraded",
      model_loaded: true,
      version: "v1.0.0",
      last_prediction: "2026-06-08T10:03:12Z",
      latency_ms: 380,
      warning: "High latency detected — drift monitor skipped Tracks 1 & 3",
    },
  },
  drift_monitor: { status: "running", last_run: "2026-06-08T10:00:00Z" },
  database:      { status: "healthy", connection: "SQLite" },
};
