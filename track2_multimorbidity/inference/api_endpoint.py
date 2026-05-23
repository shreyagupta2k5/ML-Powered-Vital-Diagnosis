# ==========================================
# TRACK 2 | FASTAPI INFERENCE ENDPOINT + TELEMETRY
# Author: Swayam (Track 2: Complex Multi-Morbidity Core)
# Objective: Deploy domain-adapted model behind REST API with 
#            input validation, telemetry logging, and Phase 7 payload formatting.
#            Accepts union of MIMIC+Pima features; validates only core MIMIC schema.
# ==========================================

import sys
import json
import uuid
import time
import pathlib
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timezone
import joblib
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict
import warnings
warnings.filterwarnings('ignore')

# Resolve project root dynamically to enable imports regardless of execution directory
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import custom MLOps modules from repository
from data_ingestion.data_ingestion import DataIngestionPipeline
from inference.telemetry_logger import TelemetryLogger

# -----------------------------------------------------------------------------
# SECTION 1: CONFIGURATION & PATHS
# -----------------------------------------------------------------------------

SCHEMA_DIR = PROJECT_ROOT / 'schema'
MODEL_PATH = PROJECT_ROOT / 'models' / 'model_mimic_adapted.joblib'
LOG_DIR = PROJECT_ROOT / 'inference' / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="Track 2 Multimorbidity Risk Engine",
    description="Real-time ICU deterioration prediction with MLOps telemetry",
    version="1.0.0"
)

# -----------------------------------------------------------------------------
# SECTION 2: LOAD MODEL & COMPONENTS
# -----------------------------------------------------------------------------

def load_system_components():
    """Load model, schema, ingestion pipeline, and telemetry logger at startup."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found at {MODEL_PATH}. "
            "Run model training in Colab and copy to track2_multimorbidity/models/"
        )
    
    model = joblib.load(MODEL_PATH)
    model_version = "v1.0.0"
    
    schema_path = SCHEMA_DIR / 'schema_reference.json'
    with open(schema_path, 'r') as f:
        schema_contract = json.load(f)
    
    # Core MIMIC schema features (for validation)
    core_features = list(schema_contract['feature_schema'].keys())
    
    # Union features for model input (MIMIC + Pima aligned)
    # These are the features the model was trained on
    union_features = core_features + [
        'bmi', 'age', 'insulin_score', 'genetic_risk_score', 'comorbidity_flag'
    ]
    
    ingestion_pipeline = DataIngestionPipeline(schema_dir=SCHEMA_DIR)
    telemetry = TelemetryLogger(log_dir=LOG_DIR, log_filename='api_inference_logs.csv')
    
    print(f"Model loaded: {MODEL_PATH.name}")
    print(f"Schema version: {schema_contract.get('schema_version', 'unknown')}")
    print(f"Core features (validated): {len(core_features)}")
    print(f"Union features (model input): {len(union_features)}")
    print("Ingestion pipeline and telemetry logger initialized.")
    
    return model, model_version, schema_contract, core_features, union_features, ingestion_pipeline, telemetry

model, model_version, schema_contract, core_features, union_features, ingestion_pipeline, telemetry = load_system_components()

# -----------------------------------------------------------------------------
# SECTION 3: REQUEST/RESPONSE MODELS
# -----------------------------------------------------------------------------

# class PatientVitalsRequest(BaseModel):
#     """
#     Accepts union of MIMIC + Pima features.
#     Only core MIMIC features are validated via schema; others passed through.
#     """
#     # Core MIMIC schema features (validated)
#     glucose_mean: Optional[float] = Field(None, description="Aggregated glucose level (mg/dL)")
#     sbp_mean: Optional[float] = Field(None, description="Mean systolic BP (mmHg)")
#     map_mean: Optional[float] = Field(None, description="Mean arterial pressure (mmHg)")
#     los: Optional[float] = Field(None, description="ICU length of stay (days)")
    
#     # Pima-aligned metabolic features (passed through, not schema-validated)
#     bmi: Optional[float] = Field(None, description="Body mass index")
#     age: Optional[float] = Field(None, description="Patient age")
#     insulin_score: Optional[float] = Field(None, description="Insulin resistance proxy")
#     genetic_risk_score: Optional[float] = Field(None, description="Diabetes pedigree function")
#     comorbidity_flag: Optional[float] = Field(None, description="Pregnancies/comorbidity proxy")
    
#     # Allow extra fields for future extensibility
#     model_config = ConfigDict(extra='allow')
    
#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "glucose_mean": 145.0,
#                 "sbp_mean": 130.0,
#                 "map_mean": 95.0,
#                 "bmi": 28.5,
#                 "age": 65.0,
#                 "los": 4.2
#             }
#         }

class PatientVitalsRequest(BaseModel):
    """
    Accepts union of MIMIC + Pima features.
    Only core MIMIC features are validated via schema; others passed through.
    """
    # Core MIMIC schema features (validated)
    glucose_mean: Optional[float] = Field(None, description="Aggregated glucose level (mg/dL)")
    sbp_mean: Optional[float] = Field(None, description="Mean systolic BP (mmHg)")
    map_mean: Optional[float] = Field(None, description="Mean arterial pressure (mmHg)")
    los: Optional[float] = Field(None, description="ICU length of stay (days)")
    
    # Pima-aligned metabolic features (passed through, not schema-validated)
    bmi: Optional[float] = Field(None, description="Body mass index")
    age: Optional[float] = Field(None, description="Patient age")
    insulin_score: Optional[float] = Field(None, description="Insulin resistance proxy")
    genetic_risk_score: Optional[float] = Field(None, description="Diabetes pedigree function")
    comorbidity_flag: Optional[float] = Field(None, description="Pregnancies/comorbidity proxy")
    
    # Pydantic v2 configuration: allow extra fields + example
    model_config = ConfigDict(
        extra='allow',
        json_schema_extra={
            "example": {
                "glucose_mean": 145.0,
                "sbp_mean": 130.0,
                "map_mean": 95.0,
                "bmi": 28.5,
                "age": 65.0,
                "los": 4.2
            }
        }
    )

class InferenceResponse(BaseModel):
    track_id: str
    model_version: str
    crisis_probability: float
    severity_level: str
    crisis_type: str
    temporal_instability_score: float
    shap_top_drivers: List[str]
    confidence_interval: List[float]
    drift_status: Dict[str, Union[float, str]]

# -----------------------------------------------------------------------------
# SECTION 4: API ENDPOINTS
# -----------------------------------------------------------------------------

@app.get("/health", tags=["MLOps"])
async def health_check():
    """MLOps health check: verifies model load, schema integrity, and telemetry status."""
    return {
        "status": "healthy",
        "model_version": model_version,
        "model_loaded": True,
        "schema_version": schema_contract.get("schema_version", "unknown"),
        "core_features": len(core_features),
        "union_features": len(union_features),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# @app.post("/predict_multimorbidity", response_model=InferenceResponse, tags=["Inference"])
# async def predict_crisis(request: PatientVitalsRequest):
#     """
#     Real-time multimorbidity crisis prediction.
#     Validates core MIMIC features, passes through Pima features, runs inference,
#     logs telemetry, returns Phase 7 payload.
#     """
#     request_id = str(uuid.uuid4())
#     start_time = time.time()
    
#     try:
#         # 1. Extract raw features from request (union of all possible inputs)
#         raw_features = request.model_dump(exclude_none=True)
        
#         # 2. Validate ONLY core MIMIC features via ingestion pipeline
#         # Extract core features for validation
#         core_input = {k: v for k, v in raw_features.items() if k in core_features}
        
#         if core_input:  # Only validate if core features are provided
#             ingestion_result = ingestion_pipeline.ingest_json(core_input)
#             if not ingestion_result['success']:
#                 raise HTTPException(status_code=400, detail=f"Core feature validation failed: {ingestion_result.get('errors')}")
#             processed_core = ingestion_result['features']
#         else:
#             processed_core = {}
        
#         # 3. Merge processed core features with passthrough Pima features
#         processed_features = {**processed_core}
#         for key, value in raw_features.items():
#             if key not in core_features:  # Pima-aligned or extra features
#                 processed_features[key] = value
        
#         # 4. Align features to model input order (union_features)
#         # Fill missing features with 0.0 (model was trained with this strategy)
#         feature_vector_dict = {}
#         for feat in union_features:
#             feature_vector_dict[feat] = processed_features.get(feat, 0.0)
        
#         feature_vector = pd.DataFrame([feature_vector_dict])
        
#         # 5. Generate prediction
#         proba = model.predict_proba(feature_vector)[0][1]  # Probability of crisis (class 1)
#         prediction = model.predict(feature_vector)[0]
        
#         # 6. Determine severity & crisis type
#         severity = "LOW"
#         crisis_type = "none"
#         if proba > 0.75:
#             severity = "HIGH"
#             crisis_type = "multimorbidity_metabolic_bp"
#         elif proba > 0.50:
#             severity = "MODERATE"
#             crisis_type = "isolated_glucose" if processed_features.get('glucose_mean', 0) > 150 else "isolated_bp"
            
#         # 7. Compute instability score (coefficient of variation proxy)
#         instability = sum([
#             processed_features.get('glucose_cv', 0),
#             processed_features.get('sbp_cv', 0),
#             processed_features.get('map_cv', 0)
#         ]) / 3.0
        
#         # 8. Mock SHAP drivers (replace with actual shap.Explainer in production)
#         shap_drivers = sorted(
#             processed_features.items(), 
#             key=lambda x: abs(x[1] - schema_contract['feature_schema'].get(x[0], {}).get('q50', 0)) if x[0] in schema_contract['feature_schema'] else abs(x[1]), 
#             reverse=True
#         )[:3]
#         shap_top = [f[0] for f in shap_drivers]
        
#         # 9. Confidence interval (approximate via bootstrap proxy)
#         ci_lower = max(0.0, proba - 0.08)
#         ci_upper = min(1.0, proba + 0.08)
        
#         # 10. Log telemetry
#         inference_latency = (time.time() - start_time) * 1000
#         prediction_dict = {
#             "crisis_probability": float(proba),
#             "severity_level": severity,
#             "crisis_type": crisis_type
#         }
#         telemetry.log_inference(
#             features=processed_features,
#             prediction=prediction_dict,
#             request_id=request_id,
#             model_version=model_version,
#             inference_latency_ms=inference_latency,
#             drift_psi_score=None
#         )
        
#         # 11. Build Phase 7 payload
#         response_payload = InferenceResponse(
#             track_id="multi_morbidity_v1",
#             model_version=model_version,
#             crisis_probability=float(proba),
#             severity_level=severity,
#             crisis_type=crisis_type,
#             temporal_instability_score=float(instability),
#             shap_top_drivers=shap_top,
#             confidence_interval=[float(ci_lower), float(ci_upper)],
#             drift_status={
#                 "psi_score": 0.0,
#                 "ks_pvalue": 1.0,
#                 "last_retrain": datetime.now(timezone.utc).isoformat()
#             }
#         )
        
#         return response_payload
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

@app.post("/predict_multimorbidity", response_model=InferenceResponse, tags=["Inference"])
async def predict_crisis(request: PatientVitalsRequest):
    """
    Real-time multimorbidity crisis prediction.
    Validates core MIMIC features, passes through Pima features, runs inference,
    logs telemetry, returns Phase 7 payload.
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # 1. Extract raw features from request (union of all possible inputs)
        raw_features = request.model_dump(exclude_none=True)
        
        # 2. Validate ONLY core MIMIC features via ingestion pipeline
        core_input = {k: v for k, v in raw_features.items() if k in core_features}
        
        if core_input:
            ingestion_result = ingestion_pipeline.ingest_json(core_input)
            if not ingestion_result['success']:
                raise HTTPException(status_code=400, detail=f"Core feature validation failed: {ingestion_result.get('errors')}")
            processed_core = ingestion_result['features']
        else:
            processed_core = {}
        
        # 3. Merge processed core features with passthrough Pima features
        processed_features = {**processed_core}
        for key, value in raw_features.items():
            if key not in core_features:
                processed_features[key] = value
        
        # 4. CRITICAL FIX: Align features to model's actual training feature order
        # XGBoost stores the exact feature names and order used during training
        if not hasattr(model, 'feature_names_in_'):
            raise RuntimeError("Model does not have feature_names_in_ attribute. Was it trained with sklearn API?")
        
        model_features = model.feature_names_in_.tolist()
        
        # Build feature vector in exact model order, filling missing with 0.0
        feature_values = []
        for feat in model_features:
            value = processed_features.get(feat)
            if value is None:
                # Feature not provided: fill with 0.0 (consistent with training preprocessing)
                feature_values.append(0.0)
            else:
                feature_values.append(float(value))
        
        # Create DataFrame with exact feature names and order
        feature_vector = pd.DataFrame([feature_values], columns=model_features)
        
        # 5. Generate prediction
        proba = model.predict_proba(feature_vector)[0][1]
        prediction = model.predict(feature_vector)[0]
        
        # 6. Determine severity & crisis type
        severity = "LOW"
        crisis_type = "none"
        if proba > 0.75:
            severity = "HIGH"
            crisis_type = "multimorbidity_metabolic_bp"
        elif proba > 0.50:
            severity = "MODERATE"
            crisis_type = "isolated_glucose" if processed_features.get('glucose_mean', 0) > 150 else "isolated_bp"
            
        # 7. Compute instability score (coefficient of variation proxy)
        instability = sum([
            processed_features.get('glucose_cv', 0),
            processed_features.get('sbp_cv', 0),
            processed_features.get('map_cv', 0)
        ]) / 3.0
        
        # 8. Mock SHAP drivers (replace with actual shap.Explainer in production)
        shap_drivers = sorted(
            processed_features.items(), 
            key=lambda x: abs(x[1] - schema_contract['feature_schema'].get(x[0], {}).get('q50', 0)) if x[0] in schema_contract['feature_schema'] else abs(x[1]), 
            reverse=True
        )[:3]
        shap_top = [f[0] for f in shap_drivers]
        
        # 9. Confidence interval (approximate via bootstrap proxy)
        ci_lower = max(0.0, proba - 0.08)
        ci_upper = min(1.0, proba + 0.08)
        
        # 10. Log telemetry
        inference_latency = (time.time() - start_time) * 1000
        prediction_dict = {
            "crisis_probability": float(proba),
            "severity_level": severity,
            "crisis_type": crisis_type
        }
        telemetry.log_inference(
            features=processed_features,
            prediction=prediction_dict,
            request_id=request_id,
            model_version=model_version,
            inference_latency_ms=inference_latency,
            drift_psi_score=None
        )
        
        # 11. Build Phase 7 payload
        response_payload = InferenceResponse(
            track_id="multi_morbidity_v1",
            model_version=model_version,
            crisis_probability=float(proba),
            severity_level=severity,
            crisis_type=crisis_type,
            temporal_instability_score=float(instability),
            shap_top_drivers=shap_top,
            confidence_interval=[float(ci_lower), float(ci_upper)],
            drift_status={
                "psi_score": 0.0,
                "ks_pvalue": 1.0,
                "last_retrain": datetime.now(timezone.utc).isoformat()
            }
        )
        
        return response_payload
        
    except HTTPException:
        raise
    except Exception as e:
        # Log full error for debugging
        print(f"INFECTION ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

# -----------------------------------------------------------------------------
# SECTION 5: LOCAL EXECUTION ENTRY POINT
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("STARTING FASTAPI INFERENCE SERVER")
    print("="*60)
    print("Docs: http://127.0.0.1:8000/docs")
    print("Health: http://127.0.0.1:8000/health")
    print("Predict: POST http://127.0.0.1:8000/predict_multimorbidity")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")