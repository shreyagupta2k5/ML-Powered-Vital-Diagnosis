# backend_shared/db/models.py
"""SQLAlchemy ORM models for the shared database layer."""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone
import json

Base = declarative_base()

class PredictionLog(Base):
    """Logs every inference request across all tracks."""
    __tablename__ = "prediction_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(64), index=True, nullable=False)
    patient_id = Column(String(64), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    track_id = Column(String(32), index=True, nullable=False)
    probability = Column(Float, nullable=False)
    risk_tier = Column(String(16), nullable=False)
    features_json = Column(JSON, nullable=True)
    latency_ms = Column(Float, nullable=True)
    model_version = Column(String(32), nullable=True)
    prediction_json = Column(JSON, nullable=True)

class DriftMetric(Base):
    """Stores PSI/KS drift metrics per feature per track."""
    __tablename__ = "drift_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    track_id = Column(String(32), index=True, nullable=False)
    feature_name = Column(String(64), index=True, nullable=False)
    psi_score = Column(Float, nullable=False)
    ks_statistic = Column(Float, nullable=True)
    p_value = Column(Float, nullable=True)
    alert_flag = Column(Boolean, default=False)
    sample_size = Column(Integer, nullable=True)

class ModelVersion(Base):
    """Tracks deployed model versions and performance metrics."""
    __tablename__ = "model_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(String(32), index=True, nullable=False)
    version = Column(String(32), nullable=False)
    deployed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    performance_metrics = Column(JSON, nullable=True)
    status = Column(String(16), default="active")  # active, staging, archived
    notes = Column(Text, nullable=True)