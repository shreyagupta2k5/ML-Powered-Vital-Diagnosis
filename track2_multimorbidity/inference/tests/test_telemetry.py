# ==========================================
# TRACK 2 | TELEMETRY LOGGER TEST SUITE
# Author: Swayam (Track 2: Complex Multi-Morbidity Core)
# Objective: Pytest-compatible tests for telemetry_logger.py.
#            Validates logging integrity, file safety, and sanitization.
# ==========================================

import pytest
import pathlib
import sys
import tempfile
import csv
import numpy as np

# ---------------------------------------------------------
# DYNAMIC PATH RESOLUTION
# Automatically locates the project root to enable imports.
# Structure: .../track2_multimorbidity/inference/tests/test_telemetry.py
# ---------------------------------------------------------
try:
    this_file = pathlib.Path(__file__).resolve()
    # Go up 3 levels: tests -> inference -> track2_multimorbidity
    project_root = this_file.parent.parent.parent 
except NameError:
    # Fallback for interactive environments
    project_root = pathlib.Path.cwd() / "track2_multimorbidity"

# Ensure project root is in sys.path for module discovery
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the module under test
from inference.telemetry_logger import TelemetryLogger


@pytest.fixture
def temp_log_dir():
    """Provides temporary directory for log file testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield pathlib.Path(tmpdir)


@pytest.fixture
def logger(temp_log_dir):
    """Initializes TelemetryLogger with temporary directory."""
    return TelemetryLogger(temp_log_dir, 'test_log.csv')


class TestLoggerInitialization:
    """Tests for logger setup and file creation."""
    
    def test_log_file_created_with_header(self, logger):
        """Verify log file is created with correct CSV header."""
        assert logger.log_path.exists()
        with open(logger.log_path, 'r') as f:
            header = f.readline().strip()
            assert 'timestamp_utc' in header
            assert 'crisis_probability' in header
            assert 'request_id' in header


class TestInferenceLogging:
    """Tests for logging inference requests and responses."""
    
    def test_log_single_inference(self, logger):
        """Verify a single inference record is logged successfully."""
        features = {
            'glucose_mean': 145.0, 'glucose_min': 95.0, 'glucose_max': 210.0,
            'glucose_std': 32.0, 'glucose_cv': 0.22, 'glucose_count': 15,
            'sbp_mean': 120.0, 'sbp_min': 100.0, 'sbp_max': 140.0,
            'sbp_std': 10.0, 'sbp_cv': 0.08, 'sbp_count': 50,
            'map_mean': 90.0, 'map_min': 75.0, 'map_max': 105.0,
            'map_std': 8.0, 'map_cv': 0.09, 'map_count': 50,
            'los': 4.2
        }
        prediction = {
            'crisis_probability': 0.35,
            'severity_level': 'MODERATE',
            'crisis_type': 'isolated_glucose'
        }
        result = logger.log_inference(
            features=features,
            prediction=prediction,
            request_id='test_001',
            model_version='v1.0.0',
            inference_latency_ms=45.2
        )
        assert result['success'] is True
    
    def test_log_retrieval(self, logger):
        """Verify logged records can be retrieved."""
        features = {
            'glucose_mean': 130.0, 'glucose_min': 80.0, 'glucose_max': 180.0,
            'glucose_std': 25.0, 'glucose_cv': 0.19, 'glucose_count': 10,
            'sbp_mean': 115.0, 'sbp_min': 95.0, 'sbp_max': 135.0,
            'sbp_std': 9.0, 'sbp_cv': 0.08, 'sbp_count': 40,
            'map_mean': 88.0, 'map_min': 72.0, 'map_max': 102.0,
            'map_std': 7.0, 'map_cv': 0.08, 'map_count': 40,
            'los': 3.5
        }
        prediction = {'crisis_probability': 0.12, 'severity_level': 'LOW', 'crisis_type': 'none'}
        logger.log_inference(features, prediction, 'retrieval_test', 'v1.0.0', 38.7)
        
        recent = logger.get_recent_logs(n=10)
        assert len(recent) == 1
        assert recent[0]['request_id'] == 'retrieval_test'
    
    def test_drift_score_optional(self, logger):
        """Verify drift_psi_score is optional and handled correctly."""
        features = {
            'glucose_mean': 140.0, 'glucose_min': 90.0, 'glucose_max': 190.0,
            'glucose_std': 28.0, 'glucose_cv': 0.20, 'glucose_count': 12,
            'sbp_mean': 118.0, 'sbp_min': 98.0, 'sbp_max': 138.0,
            'sbp_std': 9.5, 'sbp_cv': 0.08, 'sbp_count': 45,
            'map_mean': 89.0, 'map_min': 73.0, 'map_max': 103.0,
            'map_std': 7.5, 'map_cv': 0.08, 'map_count': 45,
            'los': 3.8
        }
        prediction = {'crisis_probability': 0.25, 'severity_level': 'LOW', 'crisis_type': 'none'}
        result = logger.log_inference(
            features=features,
            prediction=prediction,
            request_id='drift_test',
            model_version='v1.0.0',
            inference_latency_ms=42.1,
            drift_psi_score=None
        )
        assert result['success'] is True


class TestSanitization:
    """Tests for PHI removal and schema enforcement."""
    
    def test_unexpected_fields_removed(self, logger):
        """Verify fields not in LOG_COLUMNS are excluded from output."""
        features = {
            'glucose_mean': 140.0, 'glucose_min': 90.0, 'glucose_max': 190.0,
            'glucose_std': 28.0, 'glucose_cv': 0.20, 'glucose_count': 12,
            'sbp_mean': 118.0, 'sbp_min': 98.0, 'sbp_max': 138.0,
            'sbp_std': 9.5, 'sbp_cv': 0.08, 'sbp_count': 45,
            'map_mean': 89.0, 'map_min': 73.0, 'map_max': 103.0,
            'map_std': 7.5, 'map_cv': 0.08, 'map_count': 45,
            'los': 3.8,
            'patient_name': 'REDACTED',
            'medical_record_number': '12345'
        }
        prediction = {'crisis_probability': 0.25, 'severity_level': 'LOW', 'crisis_type': 'none'}
        logger.log_inference(features, prediction, 'sanitize_test', 'v1.0.0', 42.1)
        
        recent = logger.get_recent_logs(n=1)
        assert 'patient_name' not in recent[0]
        assert 'medical_record_number' not in recent[0]


class TestLogStats:
    """Tests for log file statistics reporting."""
    
    def test_stats_on_empty_log(self, logger):
        """Verify stats report correctly for new log file."""
        stats = logger.get_log_stats()
        assert stats['record_count'] == 0
        assert 'file_size_bytes' in stats
        assert 'last_updated' in stats
    
    def test_stats_after_logging(self, logger):
        """Verify stats update after records are logged."""
        features = {
            'glucose_mean': 135.0, 'glucose_min': 85.0, 'glucose_max': 185.0,
            'glucose_std': 26.0, 'glucose_cv': 0.19, 'glucose_count': 11,
            'sbp_mean': 117.0, 'sbp_min': 97.0, 'sbp_max': 137.0,
            'sbp_std': 9.2, 'sbp_cv': 0.08, 'sbp_count': 42,
            'map_mean': 88.5, 'map_min': 72.5, 'map_max': 102.5,
            'map_std': 7.2, 'map_cv': 0.08, 'map_count': 42,
            'los': 3.6
        }
        prediction = {'crisis_probability': 0.18, 'severity_level': 'LOW', 'crisis_type': 'none'}
        logger.log_inference(features, prediction, 'stats_test', 'v1.0.0', 40.5)
        
        stats = logger.get_log_stats()
        assert stats['record_count'] == 1
        assert stats['file_size_bytes'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])