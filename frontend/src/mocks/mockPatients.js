// ============================================================
// MOCK DATA — Patient List
// File: src/mocks/mockPatients.js
//
// 10 patients with different risk levels — used by dashboard
// Matches the shape that GET /api/v1/history will return
// ============================================================

export const mockPatients = [
  {
    id: "PT-007",
    risk_tier: "CRITICAL",
    risk_score: 0.85,
    unified_alert: "SpO2 Desaturation + High Mortality Risk",
    last_updated: "2026-06-08T10:05:00Z",
    age: 72, gender: "Male", bed: "ICU Bed 4",
  },
  {
    id: "PT-003",
    risk_tier: "HIGH",
    risk_score: 0.67,
    unified_alert: "High Mortality Risk — Elevated Lactate",
    last_updated: "2026-06-08T10:02:00Z",
    age: 58, gender: "Female", bed: "ICU Bed 7",
  },
  {
    id: "PT-011",
    risk_tier: "HIGH",
    risk_score: 0.63,
    unified_alert: "Tachycardia + Elevated Creatinine",
    last_updated: "2026-06-08T09:58:00Z",
    age: 65, gender: "Male", bed: "ICU Bed 2",
  },
  {
    id: "PT-015",
    risk_tier: "HIGH",
    risk_score: 0.61,
    unified_alert: "Hypotension Risk Detected",
    last_updated: "2026-06-08T09:55:00Z",
    age: 44, gender: "Female", bed: "ICU Bed 11",
  },
  {
    id: "PT-002",
    risk_tier: "MODERATE",
    risk_score: 0.45,
    unified_alert: "Moderate Multimorbidity Crisis Risk",
    last_updated: "2026-06-08T09:50:00Z",
    age: 60, gender: "Male", bed: "ICU Bed 9",
  },
  {
    id: "PT-005",
    risk_tier: "MODERATE",
    risk_score: 0.38,
    unified_alert: "Elevated Glucose + Insulin Resistance",
    last_updated: "2026-06-08T09:48:00Z",
    age: 53, gender: "Female", bed: "ICU Bed 3",
  },
  {
    id: "PT-008",
    risk_tier: "MODERATE",
    risk_score: 0.31,
    unified_alert: "Moderate Crisis Risk — Monitoring",
    last_updated: "2026-06-08T09:45:00Z",
    age: 49, gender: "Male", bed: "ICU Bed 6",
  },
  {
    id: "PT-009",
    risk_tier: "LOW",
    risk_score: 0.18,
    unified_alert: "No Active Alerts",
    last_updated: "2026-06-08T09:40:00Z",
    age: 35, gender: "Female", bed: "ICU Bed 1",
  },
  {
    id: "PT-001",
    risk_tier: "LOW",
    risk_score: 0.12,
    unified_alert: "No Active Alerts",
    last_updated: "2026-06-08T09:35:00Z",
    age: 40, gender: "Male", bed: "ICU Bed 8",
  },
  {
    id: "PT-013",
    risk_tier: "LOW",
    risk_score: 0.07,
    unified_alert: "No Active Alerts",
    last_updated: "2026-06-08T09:30:00Z",
    age: 29, gender: "Female", bed: "ICU Bed 10",
  },
];
