# System Architecture

## Components

backend_main

backend_shared

track1_eicu_pipeline

track2_multimorbidity

track3_vitalDB

ensemble_layer

---

## Data Flow

Client
  ↓

FastAPI Backend
  ↓

Prediction Pipelines
  ↓

MLOps Monitoring
  ↓

WebSocket Alert Layer
  ↓

Frontend Dashboard

---

## WebSocket Flow

Prediction Generated
        ↓
High Risk Detected
        ↓
Alert Published
        ↓
Connection Manager
        ↓
Frontend Receives Alert

---

## MLOps Flow

Incoming Data
        ↓
Drift Detection
        ↓
Alert Trigger
        ↓
Retraining Pipeline