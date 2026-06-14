// ============================================================
// MOCK DATA — Drift Monitor
// File: src/mocks/mockDrift.js
//
// This matches GET /api/v1/drift/{track_id} response shape
// PSI > 0.25 means the model is seeing data it wasn't trained on
// alert_flag: true means that feature has drifted (problem!)
// ============================================================

export const mockDrift = {
  track2_multimorbidity: {
    track_id: "track2_multimorbidity",
    status: "DRIFT_DETECTED",
    features_drifted: 1,
    metrics: [
      { feature_name: "glucose_mean",   psi_score: 0.28, ks_statistic: 0.19, alert_flag: true  },
      { feature_name: "heartrate_mean", psi_score: 0.08, ks_statistic: 0.05, alert_flag: false },
      { feature_name: "insulin_score",  psi_score: 0.05, ks_statistic: 0.03, alert_flag: false },
      { feature_name: "comorbidity",    psi_score: 0.03, ks_statistic: 0.02, alert_flag: false },
      { feature_name: "sysbp_mean",     psi_score: 0.04, ks_statistic: 0.02, alert_flag: false },
      { feature_name: "los_hours",      psi_score: 0.06, ks_statistic: 0.04, alert_flag: false },
    ],
  },
  track1_eicu: {
    track_id: "track1_eicu",
    status: "OK",
    features_drifted: 0,
    metrics: [
      { feature_name: "sao2_mean",      psi_score: 0.12, ks_statistic: 0.08, alert_flag: false },
      { feature_name: "lactate_mean",   psi_score: 0.09, ks_statistic: 0.06, alert_flag: false },
      { feature_name: "heartrate_mean", psi_score: 0.06, ks_statistic: 0.04, alert_flag: false },
      { feature_name: "glucose_mean",   psi_score: 0.11, ks_statistic: 0.07, alert_flag: false },
      { feature_name: "creatinine",     psi_score: 0.07, ks_statistic: 0.05, alert_flag: false },
    ],
  },
  track3_vitaldb: {
    track_id: "track3_vitaldb",
    status: "OK",
    features_drifted: 0,
    metrics: [
      { feature_name: "map_mean",       psi_score: 0.21, ks_statistic: 0.14, alert_flag: false },
      { feature_name: "hr_variability", psi_score: 0.11, ks_statistic: 0.07, alert_flag: false },
      { feature_name: "spo2_drop",      psi_score: 0.04, ks_statistic: 0.03, alert_flag: false },
      { feature_name: "ecg_variance",   psi_score: 0.08, ks_statistic: 0.05, alert_flag: false },
    ],
  },
};
