# backend_shared/registry/model_loader.py
"""
Model Loader with Lazy Loading & Hot-Swap — Task 3.3
"""
import logging
import pathlib
import pickle
import threading
from typing import Any, Dict, Optional

import joblib

logger = logging.getLogger(__name__)

# ── Project root ──────────────────────────────────────────────────────────────
_THIS_FILE = pathlib.Path(__file__).resolve()

def _find_project_root() -> pathlib.Path:
    markers = {
        "track1_eicu_pipeline",
        "track2_multimorbidity",
        "track3_vitaldb_pipeline",
        "vitalDB project",
        "backend_shared",
    }
    candidate = _THIS_FILE.parent
    for _ in range(6):
        candidate = candidate.parent
        if any((candidate / m).exists() for m in markers):
            return candidate
    return _THIS_FILE.resolve().parent.parent.parent

_PROJECT_ROOT = _find_project_root()
logger.debug(f"[model_loader] PROJECT_ROOT resolved to: {_PROJECT_ROOT}")


# ── Internal cache ────────────────────────────────────────────────────────────

class _ModelCache:
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._meta:  Dict[str, Dict] = {}
        self._lock   = threading.RLock()

    def get(self, track_id: str) -> Optional[Any]:
        with self._lock:
            return self._cache.get(track_id)

    def set(self, track_id: str, model: Any, meta: Optional[Dict] = None):
        with self._lock:
            self._cache[track_id] = model
            if meta:
                self._meta[track_id] = meta
        logger.info(f"[ModelCache] {track_id} loaded into cache.")

    def evict(self, track_id: str):
        with self._lock:
            self._cache.pop(track_id, None)
            self._meta.pop(track_id, None)
        logger.info(f"[ModelCache] {track_id} evicted from cache.")

    def get_meta(self, track_id: str) -> Optional[Dict]:
        with self._lock:
            return self._meta.get(track_id)

    def loaded_tracks(self):
        with self._lock:
            return list(self._cache.keys())


_cache = _ModelCache()


# ── Artifact loading ──────────────────────────────────────────────────────────

def _resolve_path(artifact_path: str) -> pathlib.Path:
    path = pathlib.Path(artifact_path)
    if path.is_absolute():
        return path
    return _PROJECT_ROOT / artifact_path


def _load_file(path: pathlib.Path) -> Any:
    """Load a single model file — tries joblib first, falls back to pickle."""
    try:
        return joblib.load(path)
    except Exception:
        with open(path, "rb") as f:
            return pickle.load(f)


def _load_artifact(artifact_path: str) -> Any:
    """Load .pkl / .joblib / .json artifact from absolute or project-relative path."""
    path = _resolve_path(artifact_path)

    if not path.exists():
        raise FileNotFoundError(f"Model artifact not found: {path}")

    suffix = path.suffix.lower()

    if suffix in (".pkl", ".pickle", ".joblib"):
        return _load_file(path)

    if suffix == ".json":
        try:
            import xgboost as xgb
            model = xgb.Booster()
            model.load_model(str(path))
            return model
        except ImportError:
            import json
            with open(path) as f:
                return json.load(f)

    raise ValueError(f"Unsupported artifact format: {suffix}")


def _load_track3_ensemble(artifact_dir: str) -> Dict[str, Any]:
    """
    Track 3 structure (vitalDB project/backend/models/):
      hypotension/   -> best_model.pkl + scaler.pkl
      low_spo2/      -> best_model.pkl + scaler.pkl
      tachycardia/   -> best_model.pkl + scaler.pkl

    Returns: {event_name: {"model": <model>, "scaler": <scaler_or_None>}}
    Uses joblib first, falls back to pickle for each file.
    """
    dir_path = _resolve_path(artifact_dir)

    if not dir_path.exists():
        raise FileNotFoundError(f"Track 3 model directory not found: {dir_path}")

    models: Dict[str, Any] = {}
    subdirs = sorted([d for d in dir_path.iterdir() if d.is_dir()])

    if subdirs:
        for subdir in subdirs:
            model_file  = subdir / "best_model.pkl"
            scaler_file = subdir / "scaler.pkl"

            if not model_file.exists():
                pkls = list(subdir.glob("*.pkl"))
                if not pkls:
                    logger.warning(f"[track3] No .pkl in {subdir.name}, skipping.")
                    continue
                model_file = pkls[0]

            model = _load_file(model_file)

            scaler = None
            if scaler_file.exists():
                scaler = _load_file(scaler_file)

            models[subdir.name] = {"model": model, "scaler": scaler}
            logger.info(
                f"[track3] Loaded '{subdir.name}': "
                f"model={type(model).__name__}, scaler={'yes' if scaler else 'no'}"
            )
    else:
        for pkl in sorted(dir_path.glob("*.pkl")):
            models[pkl.stem] = {"model": _load_file(pkl), "scaler": None}

    if not models:
        raise FileNotFoundError(f"No models found in {dir_path}")

    return models


# ── Public API ────────────────────────────────────────────────────────────────

def load_model(
    track_id: str,
    force_reload: bool = False,
    version: Optional[str] = None,
) -> Any:
    """Lazy-load model for track_id; cache after first load."""
    if not force_reload and _cache.get(track_id) is not None:
        return _cache.get(track_id)

    from backend_shared.registry.model_registry import get_active_version, get_version

    meta = get_version(track_id, version) if version else get_active_version(track_id)
    if meta is None:
        raise RuntimeError(f"No active version found for '{track_id}' in registry.")

    artifact_path = meta["artifact_path"]
    resolved = _resolve_path(artifact_path)

    if track_id == "track3_vitaldb" and (resolved.is_dir() or not resolved.suffix):
        model = _load_track3_ensemble(artifact_path)
    else:
        model = _load_artifact(artifact_path)

    if force_reload:
        _cache.evict(track_id)

    _cache.set(track_id, model, meta)
    logger.info(
        f"[{track_id}] Loaded version={meta['version']} "
        f"type={meta.get('model_type')} from {artifact_path}"
    )
    return model


def hot_swap(track_id: str, new_version: str) -> bool:
    """Hot-swap to a different registered version without restarting the API."""
    logger.info(f"[{track_id}] Hot-swap -> version {new_version}")
    try:
        from backend_shared.registry.model_registry import get_version, promote_to_active

        meta = get_version(track_id, new_version)
        if meta is None:
            raise ValueError(f"Version {new_version} not registered for {track_id}")

        artifact_path = meta["artifact_path"]
        resolved = _resolve_path(artifact_path)
        if track_id == "track3_vitaldb" and (resolved.is_dir() or not resolved.suffix):
            new_model = _load_track3_ensemble(artifact_path)
        else:
            new_model = _load_artifact(artifact_path)

        _cache.evict(track_id)
        _cache.set(track_id, new_model, meta)
        promote_to_active(track_id, new_version)

        logger.info(f"[{track_id}] Hot-swap complete -> version {new_version}")
        return True
    except Exception as e:
        logger.error(f"[{track_id}] Hot-swap failed: {e}")
        return False


def get_loaded_model_meta(track_id: str) -> Optional[Dict]:
    return _cache.get_meta(track_id)


def preload_all_models() -> Dict[str, bool]:
    """Eagerly load all 3 track models at startup."""
    results = {}
    for track in ["track1_eicu", "track2_multimorbidity", "track3_vitaldb"]:
        try:
            load_model(track)
            results[track] = True
        except Exception as e:
            logger.warning(f"[{track}] Could not preload model: {e}")
            results[track] = False
    return results


def unload_model(track_id: str) -> None:
    _cache.evict(track_id)


def list_loaded() -> list:
    return _cache.loaded_tracks()