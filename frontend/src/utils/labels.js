// ============================================================
// Shared Clinical Labels Mapping
// File: src/utils/labels.js
//
// WHAT THIS DOES:
//   Maps internal track keys/model names to short, clinician-
//   friendly labels for use on Dashboard and Patient pages.
//   Full technical names (with model versions) are reserved
//   for the Admin/MLOps panel only.
// ============================================================

// Short clinical labels — used on Dashboard & Patient pages
export const CLINICAL_LABELS = {
  track1_eicu:           "Mortality Risk",
  track2_multimorbidity: "Crisis Risk",
  track3_vitaldb:        "Vital Signs",
};

// Full technical labels — used ONLY on Admin/MLOps panel
export const TECHNICAL_LABELS = {
  track1_eicu:           "Track 1 — eICU Mortality",
  track2_multimorbidity: "Track 2 — MIMIC Crisis",
  track3_vitaldb:        "Track 3 — VitalDB Waveforms",
};

// Helper to get the clinical (short) label for a track key
export function getClinicalLabel(trackKey) {
  return CLINICAL_LABELS[trackKey] || trackKey;
}

// Helper to get the technical (full) label for a track key
export function getTechnicalLabel(trackKey) {
  return TECHNICAL_LABELS[trackKey] || trackKey;
}