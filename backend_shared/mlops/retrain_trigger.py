# backend_shared/mlops/retrain_trigger.py
"""
Retrain Trigger & Scheduler — Task 3.2
Evaluates drift reports and fires retrain alerts / webhooks.
Also contains the thread-based scheduler that runs drift_monitor every N minutes.
"""
import sys
import pathlib as _pl
sys.path.insert(0, str(_pl.Path(__file__).resolve().parent.parent.parent))

import json
import logging
import os
import pathlib
import threading
import time
from datetime import datetime, timezone
from typing import Dict, Optional

logger = logging.getLogger(__name__)

_ROOT        = pathlib.Path(__file__).resolve().parent.parent   # backend_shared/
_CONFIG_PATH = _ROOT / "config" / "drift_thresholds.json"


# ── Retrain decision logic ────────────────────────────────────────────────────

def should_retrain(drift_report: Dict) -> bool:
    """Return True when the drift report meets the retrain criteria."""
    return bool(drift_report.get("retrain_trigger", False))


def evaluate_all_tracks(reports: Dict[str, Dict]) -> Dict[str, bool]:
    """Given {track_id: drift_report}, return {track_id: needs_retrain}."""
    return {track: should_retrain(report) for track, report in reports.items()}


# ── Notification / webhook ────────────────────────────────────────────────────

def send_retrain_alert(track_id: str, drift_report: Dict) -> None:
    """
    Send retrain alert via webhook (set RETRAIN_WEBHOOK_URL env var)
    or fall back to a structured log line.
    """
    payload = {
        "event":            "retrain_required",
        "track_id":         track_id,
        "timestamp":        datetime.now(timezone.utc).isoformat(),
        "max_psi":          drift_report.get("max_psi"),
        "features_drifted": drift_report.get("features_drifted"),
        "features_checked": drift_report.get("features_checked"),
        "top_drifted_features": [
            m["feature_name"]
            for m in sorted(
                drift_report.get("metrics", []),
                key=lambda x: x.get("psi_score", 0),
                reverse=True,
            )[:5]
        ],
    }

    webhook_url = os.getenv("RETRAIN_WEBHOOK_URL", "").strip()
    if webhook_url:
        try:
            import urllib.request
            data = json.dumps(payload).encode("utf-8")
            req  = urllib.request.Request(
                webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                logger.info(f"[{track_id}] Retrain webhook sent — HTTP {resp.status}")
        except Exception as e:
            logger.error(f"[{track_id}] Retrain webhook failed: {e}")
    else:
        logger.warning(
            f"[RETRAIN ALERT] {track_id} | "
            f"max_psi={payload['max_psi']} | "
            f"drifted={payload['features_drifted']}/{payload['features_checked']} | "
            f"top_features={payload['top_drifted_features']}"
        )


def send_drift_warning(track_id: str, drift_report: Dict) -> None:
    """Soft warning — drift detected but retrain threshold not yet hit."""
    logger.warning(
        f"[DRIFT WARNING] {track_id} | "
        f"max_psi={drift_report.get('max_psi')} | "
        f"drifted={drift_report.get('features_drifted')}/{drift_report.get('features_checked')}"
    )


# ── Orchestration ─────────────────────────────────────────────────────────────

def run_drift_cycle(window_minutes: int = 60) -> Dict[str, Dict]:
    """
    Full drift-check cycle:
      1. Run drift monitor for all tracks
      2. Evaluate retrain criteria
      3. Fire alerts where needed
    Returns the full reports dict.
    """
    from backend_shared.mlops.drift_monitor import run_all_tracks

    logger.info("=== Drift detection cycle starting ===")
    reports = run_all_tracks(window_minutes=window_minutes)

    for track_id, report in reports.items():
        status = report.get("status", "unknown")

        if status in (
            "skipped_no_reference",
            "skipped_no_current_data",
            "skipped_no_features",
        ):
            logger.info(f"[{track_id}] Skipped — {status}")
            continue

        if status == "error":
            logger.error(f"[{track_id}] Drift check error: {report.get('error')}")
            continue

        if should_retrain(report):
            send_retrain_alert(track_id, report)
        elif report.get("alert"):
            send_drift_warning(track_id, report)
        else:
            logger.info(
                f"[{track_id}] No significant drift — "
                f"features_drifted={report.get('features_drifted')}/"
                f"{report.get('features_checked')}, "
                f"max_psi={report.get('max_psi')}"
            )

    logger.info("=== Drift detection cycle complete ===")
    return reports


# ── Scheduler ─────────────────────────────────────────────────────────────────

class DriftScheduler:
    """
    Lightweight background scheduler.
    Runs `run_drift_cycle` every `interval_minutes` (default from config, else 10).
    """

    def __init__(self, interval_minutes: Optional[int] = None):
        cfg = {}
        if _CONFIG_PATH.exists():
            with open(_CONFIG_PATH) as f:
                cfg = json.load(f).get("global", {})
        self.interval      = (interval_minutes or cfg.get("run_interval_minutes", 10)) * 60
        self._stop_event   = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def _loop(self):
        logger.info(f"DriftScheduler started — interval {self.interval}s ({self.interval // 60} min)")
        while not self._stop_event.is_set():
            try:
                run_drift_cycle()
            except Exception as e:
                logger.error(f"DriftScheduler cycle error: {e}")
            self._stop_event.wait(self.interval)
        logger.info("DriftScheduler loop exited.")

    def start(self):
        if self._thread and self._thread.is_alive():
            logger.warning("DriftScheduler already running — ignoring duplicate start().")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="DriftScheduler"
        )
        self._thread.start()
        logger.info("DriftScheduler thread launched.")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("DriftScheduler stopped.")

    @property
    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())


# ── Module-level singleton ────────────────────────────────────────────────────

_scheduler: Optional[DriftScheduler] = None


def start_scheduler(interval_minutes: Optional[int] = None) -> None:
    """Start the global drift scheduler (call once at app startup)."""
    global _scheduler
    if _scheduler and _scheduler.is_running:
        logger.warning("start_scheduler() called but scheduler is already running.")
        return
    _scheduler = DriftScheduler(interval_minutes)
    _scheduler.start()


def stop_scheduler() -> None:
    """Stop the global drift scheduler (call at app shutdown)."""
    if _scheduler:
        _scheduler.stop()


def scheduler_status() -> str:
    if _scheduler is None:
        return "not_started"
    return "running" if _scheduler.is_running else "stopped"


# ── CLI entry point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )

    if len(sys.argv) > 1 and sys.argv[1] == "once":
        results = run_drift_cycle()
        print("\n" + "=" * 60)
        print("DRIFT CYCLE SUMMARY")
        print("=" * 60)
        for track, r in results.items():
            print(f"\n  {track}")
            print(f"    status          : {r.get('status')}")
            print(f"    alert           : {r.get('alert')}")
            print(f"    retrain_trigger : {r.get('retrain_trigger')}")
            print(f"    features_drifted: {r.get('features_drifted')}/{r.get('features_checked')}")
            print(f"    max_psi         : {r.get('max_psi')}")
    else:
        print("Starting DriftScheduler (Ctrl+C to stop)...")
        start_scheduler()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            stop_scheduler()