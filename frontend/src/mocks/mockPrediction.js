// ============================================================
// MOCK DATA — Single Patient Ensemble Prediction
// File: src/mocks/mockPrediction.js
//
// This matches the exact JSON shape from POST /api/v1/ensemble/predict
// Used by the Patient Detail page
// ============================================================

export const mockPrediction = {
  patient_id: "PT-007",
  timestamp: "2026-06-08T10:05:00Z",
  overall_risk: "CRITICAL",
  risk_score: 0.85,
  unified_alert: "CRITICAL — SpO2 Desaturation + High Mortality Risk",
  top_features: [
    { feature: "sao2_mean",       shap_value: 0.21, direction: "up" },
    { feature: "lactate_mean",    shap_value: 0.18, direction: "up" },
    { feature: "heartrate_mean",  shap_value: 0.14, direction: "up" },
    { feature: "insulin_score",   shap_value: 0.12, direction: "up" },
    { feature: "glucose_std",     shap_value: 0.09, direction: "up" },
    { feature: "creatinine_mean", shap_value: 0.07, direction: "up" },
  ],
  track_results: {
    track1_eicu: {
      mortality_probability: 0.67,
      risk_tier: "HIGH",
      model_version: "v1.0.0",
      top_shap_drivers: [
        { feature: "sao2_mean", shap_value: 0.21 },
        { feature: "lactate_mean", shap_value: 0.18 },
      ],
    },
    track2_multimorbidity: {
      crisis_probability: 0.31,
      severity_level: "MODERATE",
      confidence_interval: [0.23, 0.39],
      model_version: "v4.0.0",
    },
    track3_vitaldb: {
      hypotension_probability: 0.04,
      tachycardia_probability: 0.12,
      spo2_drop_probability: 0.87,
      risk_level: "CRITICAL",
      model_version: "v1.0.0",
      alerts: ["OXYGEN_DESATURATION_DETECTED"],
    },
  },
  model_versions: {
    track1_eicu: "v1.0.0",
    track2_multimorbidity: "v4.0.0",
    track3_vitaldb: "v1.0.0",
  },
};
