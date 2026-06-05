# backend_shared/registry/model_registry.py
"""
Centralized Model Registry — Task 3.3
Tracks model versions, metadata, and deployment status for all tracks.
Backed by SQLite (registry.db) via SQLAlchemy.
"""
import hashlib
import json
import logging
import pathlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# ── DB setup (dedicated registry.db) ─────────────────────────────────────────
_REGISTRY_DIR = pathlib.Path(__file__).resolve().parent
_DB_PATH = _REGISTRY_DIR / "registry.db"
_DB_URL = f"sqlite:///{_DB_PATH}"

engine = create_engine(_DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── ORM Model ─────────────────────────────────────────────────────────────────

class ModelVersionRecord(Base):
    """One row per registered model version."""
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(String(32), index=True, nullable=False)
    version = Column(String(32), nullable=False)
    model_type = Column(String(64), nullable=True)        # e.g. "RandomForest", "XGBoost"
    artifact_path = Column(Text, nullable=True)           # path to .pkl / .joblib
    feature_schema_hash = Column(String(64), nullable=True)
    performance_metrics = Column(JSON, nullable=True)     # {"auc": 0.87, "f1": 0.74, ...}
    training_date = Column(DateTime, nullable=True)
    registered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    deployed_at = Column(DateTime, nullable=True)
    status = Column(String(16), default="staging")       # active | staging | archived
    is_current = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)


def init_registry():
    """Create tables and seed initial known versions."""
    Base.metadata.create_all(bind=engine)
    _seed_initial_versions()


@contextmanager
def _session() -> Session:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── Seed data (known versions at launch) ─────────────────────────────────────

_INITIAL_VERSIONS = [
    {
        "track_id": "track1_eicu",
        "version": "v1.0.0",
        "model_type": "RandomForest",
        "artifact_path": "track1_eicu_pipeline/models/track1_best_model.pkl",
        "performance_metrics": {"auc": 0.85, "f1": 0.72, "recall": 0.78},
        "status": "active",
        "notes": "Initial eICU mortality model — 562 features",
    },
    {
        "track_id": "track2_multimorbidity",
        "version": "v4.0.0",
        "model_type": "XGBoost",
        # "artifact_path": "track2_multimorbidity/models/xgboost_leak_free.pkl",
        "artifact_path": "track2_multimorbidity/models/model_mimic_calibrated.joblib",
        "performance_metrics": {"auc": 0.91, "f1": 0.80, "recall": 0.83},
        "status": "active",
        "notes": "Leak-free XGBoost — 6 features (MIMIC+Pima)",
    },
    {
        "track_id": "track3_vitaldb",
        "version": "v1.0.0",
        "model_type": "RF/XGBoost Ensemble",
        # "artifact_path": "vitalDB project/backend/models/",
        "artifact_path": "track3_vitalDB/backend/models/",
        "performance_metrics": {"auc": 0.88, "f1": 0.76, "recall": 0.80},
        "status": "active",
        "notes": "Waveform ensemble — hypotension/tachycardia/SpO2 drop",
    },
]


def _seed_initial_versions():
    """Insert initial versions only if the table is empty."""
    with _session() as db:
        existing = db.query(ModelVersionRecord).count()
        if existing > 0:
            return
        for v in _INITIAL_VERSIONS:
            record = ModelVersionRecord(
                track_id=v["track_id"],
                version=v["version"],
                model_type=v["model_type"],
                artifact_path=v["artifact_path"],
                performance_metrics=v["performance_metrics"],
                status=v["status"],
                is_current=True,
                notes=v["notes"],
                training_date=datetime.now(timezone.utc),
                deployed_at=datetime.now(timezone.utc),
            )
            db.add(record)
        logger.info("Registry seeded with initial model versions.")


# ── Public API ────────────────────────────────────────────────────────────────

def register_model(
    track_id: str,
    version: str,
    model_type: str,
    artifact_path: str,
    performance_metrics: Optional[Dict[str, float]] = None,
    feature_schema: Optional[List[str]] = None,
    training_date: Optional[datetime] = None,
    notes: Optional[str] = None,
    status: str = "staging",
) -> int:
    """
    Register a new model version.
    Returns the new record ID.
    """
    schema_hash = None
    if feature_schema:
        schema_hash = hashlib.md5(json.dumps(sorted(feature_schema)).encode()).hexdigest()

    with _session() as db:
        record = ModelVersionRecord(
            track_id=track_id,
            version=version,
            model_type=model_type,
            artifact_path=artifact_path,
            feature_schema_hash=schema_hash,
            performance_metrics=performance_metrics,
            training_date=training_date or datetime.now(timezone.utc),
            status=status,
            is_current=False,
            notes=notes,
        )
        db.add(record)
        db.flush()
        record_id = record.id
    logger.info(f"Registered {track_id} {version} (id={record_id}, status={status})")
    return record_id


def promote_to_active(track_id: str, version: str) -> bool:
    """
    Set `version` as the active (current) model for `track_id`.
    Archives the previous active version.
    Returns True on success.
    """
    with _session() as db:
        # Archive old active
        db.query(ModelVersionRecord).filter(
            ModelVersionRecord.track_id == track_id,
            ModelVersionRecord.is_current == True
        ).update({"is_current": False, "status": "archived"})

        # Promote new
        updated = db.query(ModelVersionRecord).filter(
            ModelVersionRecord.track_id == track_id,
            ModelVersionRecord.version == version
        ).update({
            "is_current": True,
            "status": "active",
            "deployed_at": datetime.now(timezone.utc)
        })

        if not updated:
            logger.warning(f"promote_to_active: version {version} not found for {track_id}")
            return False

    logger.info(f"Promoted {track_id} {version} → active")
    return True


def get_active_version(track_id: str) -> Optional[Dict[str, Any]]:
    """Return metadata for the currently active model of a track."""
    with _session() as db:
        record = db.query(ModelVersionRecord).filter(
            ModelVersionRecord.track_id == track_id,
            ModelVersionRecord.is_current == True
        ).first()
        return _record_to_dict(record) if record else None


def get_version(track_id: str, version: str) -> Optional[Dict[str, Any]]:
    """Return metadata for a specific version."""
    with _session() as db:
        record = db.query(ModelVersionRecord).filter(
            ModelVersionRecord.track_id == track_id,
            ModelVersionRecord.version == version
        ).first()
        return _record_to_dict(record) if record else None


def list_versions(track_id: str) -> List[Dict[str, Any]]:
    """List all registered versions for a track, newest first."""
    with _session() as db:
        records = db.query(ModelVersionRecord).filter(
            ModelVersionRecord.track_id == track_id
        ).order_by(ModelVersionRecord.registered_at.desc()).all()
        return [_record_to_dict(r) for r in records]


def archive_version(track_id: str, version: str) -> bool:
    """Mark a version as archived."""
    with _session() as db:
        updated = db.query(ModelVersionRecord).filter(
            ModelVersionRecord.track_id == track_id,
            ModelVersionRecord.version == version
        ).update({"status": "archived", "is_current": False})
    return bool(updated)


def update_metrics(track_id: str, version: str, metrics: Dict[str, float]) -> bool:
    """Update performance metrics for a registered version."""
    with _session() as db:
        updated = db.query(ModelVersionRecord).filter(
            ModelVersionRecord.track_id == track_id,
            ModelVersionRecord.version == version
        ).update({"performance_metrics": metrics})
    return bool(updated)


def _record_to_dict(r: ModelVersionRecord) -> Dict[str, Any]:
    return {
        "id": r.id,
        "track_id": r.track_id,
        "version": r.version,
        "model_type": r.model_type,
        "artifact_path": r.artifact_path,
        "feature_schema_hash": r.feature_schema_hash,
        "performance_metrics": r.performance_metrics,
        "training_date": r.training_date.isoformat() if r.training_date else None,
        "registered_at": r.registered_at.isoformat() if r.registered_at else None,
        "deployed_at": r.deployed_at.isoformat() if r.deployed_at else None,
        "status": r.status,
        "is_current": r.is_current,
        "notes": r.notes,
    }


# ── Initialize on import ──────────────────────────────────────────────────────
init_registry()