# ==========================================
# TRACK 2 | TELEMETRY LOGGER MODULE
# Author: Swayam (Track 2: Complex Multi-Morbidity Core)
# Objective: Implement audit-compliant logging for inference requests.
#            Logs de-identified feature vectors, predictions, and metadata
#            to support drift detection and model performance monitoring.
# ==========================================

import csv
import json
import pathlib
import fcntl
import numpy as np  # Added: Required for numpy type checking in sanitization
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union
import warnings
warnings.filterwarnings('ignore')


class TelemetryLogger:
    """
    Thread-safe logger for inference telemetry.
    Appends de-identified records to CSV with file locking for concurrent safety.
    """
    
    # CSV column schema - fixed order for consistency
    LOG_COLUMNS = [
        'timestamp_utc',
        'model_version',
        'request_id',
        'glucose_mean', 'glucose_min', 'glucose_max', 'glucose_std', 'glucose_cv', 'glucose_count',
        'sbp_mean', 'sbp_min', 'sbp_max', 'sbp_std', 'sbp_cv', 'sbp_count',
        'map_mean', 'map_min', 'map_max', 'map_std', 'map_cv', 'map_count',
        'los',
        'crisis_probability',
        'severity_level',
        'crisis_type',
        'inference_latency_ms',
        'drift_psi_score'
    ]
    
    def __init__(self, log_dir: Union[str, pathlib.Path], log_filename: str = 'logged_clinical_traces.csv'):
        """
        Initialize telemetry logger.
        
        Args:
            log_dir: Directory for log file storage
            log_filename: Name of the log file (default: logged_clinical_traces.csv)
        """
        self.log_dir = pathlib.Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.log_dir / log_filename
        self._initialize_log_file()
    
    def _initialize_log_file(self):
        """Create log file with header if it does not exist."""
        if not self.log_path.exists():
            with open(self.log_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.LOG_COLUMNS)
                writer.writeheader()
    
    def _acquire_lock(self, file_handle) -> bool:
        """
        Acquire exclusive file lock for writing.
        
        Args:
            file_handle: Open file object
            
        Returns:
            True if lock acquired, False otherwise
        """
        try:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (IOError, OSError):
            return False
    
    def _release_lock(self, file_handle):
        """Release file lock."""
        try:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
        except (IOError, OSError):
            pass
    
    def _sanitize_record(self, record: Dict) -> Dict:
        """
        Ensure record contains only de-identified, schema-compliant fields.
        Removes any potential PHI or unexpected keys.
        
        Args:
            record: Raw record dictionary
            
        Returns:
            Sanitized record with only allowed columns
        """
        sanitized = {}
        for col in self.LOG_COLUMNS:
            value = record.get(col)
            # Convert numpy types to native Python for CSV compatibility
            if isinstance(value, (np.integer, np.floating)):
                sanitized[col] = '' if np.isnan(value) else float(value)
            elif value is None:
                sanitized[col] = ''
            else:
                sanitized[col] = value
        return sanitized
    
    def log_inference(
        self,
        features: Dict[str, float],
        prediction: Dict[str, Union[float, str]],
        request_id: str,
        model_version: str,
        inference_latency_ms: float,
        drift_psi_score: Optional[float] = None
    ) -> Dict[str, Union[bool, str]]:
        """
        Log a single inference request and response.
        
        Args:
            features: Preprocessed feature vector sent to model
            prediction: Model output dict with crisis_probability, severity_level, crisis_type
            request_id: Unique identifier for this inference request
            model_version: Version string of the model used
            inference_latency_ms: Time taken for inference in milliseconds
            drift_psi_score: Optional PSI score indicating data drift
            
        Returns:
            Dict with success status and message
        """
        # Build log record with timezone-aware UTC timestamp
        record = {
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'model_version': model_version,
            'request_id': request_id,
            'glucose_mean': features.get('glucose_mean'),
            'glucose_min': features.get('glucose_min'),
            'glucose_max': features.get('glucose_max'),
            'glucose_std': features.get('glucose_std'),
            'glucose_cv': features.get('glucose_cv'),
            'glucose_count': features.get('glucose_count'),
            'sbp_mean': features.get('sbp_mean'),
            'sbp_min': features.get('sbp_min'),
            'sbp_max': features.get('sbp_max'),
            'sbp_std': features.get('sbp_std'),
            'sbp_cv': features.get('sbp_cv'),
            'sbp_count': features.get('sbp_count'),
            'map_mean': features.get('map_mean'),
            'map_min': features.get('map_min'),
            'map_max': features.get('map_max'),
            'map_std': features.get('map_std'),
            'map_cv': features.get('map_cv'),
            'map_count': features.get('map_count'),
            'los': features.get('los'),
            'crisis_probability': prediction.get('crisis_probability'),
            'severity_level': prediction.get('severity_level'),
            'crisis_type': prediction.get('crisis_type'),
            'inference_latency_ms': inference_latency_ms,
            'drift_psi_score': drift_psi_score
        }
        
        # Sanitize to ensure only allowed columns are written
        sanitized = self._sanitize_record(record)
        
        # Write with file locking for concurrent safety
        try:
            with open(self.log_path, 'a', newline='', encoding='utf-8') as f:
                if not self._acquire_lock(f):
                    return {'success': False, 'error': 'Could not acquire file lock'}
                
                try:
                    writer = csv.DictWriter(f, fieldnames=self.LOG_COLUMNS)
                    writer.writerow(sanitized)
                    return {'success': True, 'message': 'Record logged successfully'}
                finally:
                    self._release_lock(f)
                    
        except Exception as e:
            return {'success': False, 'error': f'Logging error: {str(e)}'}
    
    def get_recent_logs(self, n: int = 100) -> List[Dict]:
        """
        Retrieve the most recent n log entries for inspection.
        
        Args:
            n: Number of recent entries to return
            
        Returns:
            List of dictionaries representing log records
        """
        if not self.log_path.exists():
            return []
        
        records = []
        with open(self.log_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
        
        return records[-n:] if len(records) > n else records
    
    def get_log_stats(self) -> Dict[str, Union[int, str]]:
        """
        Get basic statistics about the log file.
        
        Returns:
            Dict with file size, record count, and last update time
        """
        if not self.log_path.exists():
            return {'record_count': 0, 'file_size_bytes': 0, 'last_updated': None}
        
        stats = self.log_path.stat()
        with open(self.log_path, 'r', encoding='utf-8') as f:
            # Count data rows (excluding header)
            record_count = sum(1 for _ in f) - 1
        
        return {
            'record_count': max(0, record_count),
            'file_size_bytes': stats.st_size,
            'last_updated': datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc).isoformat()
        }


# ==========================================
# UNIT TESTS FOR TELEMETRY LOGGER
# ==========================================

def run_unit_tests():
    """Execute unit tests for telemetry logging functionality."""
    import tempfile
    import os
    
    print("Running unit tests for telemetry_logger module...")
    
    results = {'passed': 0, 'failed': 0, 'details': []}
    
    # Test 1: Initialize logger and verify header creation
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = TelemetryLogger(tmpdir, 'test_log.csv')
        if logger.log_path.exists():
            with open(logger.log_path, 'r') as f:
                header = f.readline().strip()
                if 'timestamp_utc' in header and 'crisis_probability' in header:
                    results['passed'] += 1
                    results['details'].append("Test 1 PASSED: Log file initialized with correct header")
                else:
                    results['failed'] += 1
                    results['details'].append("Test 1 FAILED: Header missing expected columns")
        else:
            results['failed'] += 1
            results['details'].append("Test 1 FAILED: Log file not created")
    
    # Test 2: Log a single inference record
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = TelemetryLogger(tmpdir, 'test_log.csv')
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
            request_id='test_req_001',
            model_version='v1.0.0',
            inference_latency_ms=45.2,
            drift_psi_score=0.08
        )
        if result['success']:
            results['passed'] += 1
            results['details'].append("Test 2 PASSED: Single inference record logged")
        else:
            results['failed'] += 1
            results['details'].append(f"Test 2 FAILED: {result}")
    
    # Test 3: Verify logged data can be retrieved
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = TelemetryLogger(tmpdir, 'test_log.csv')
        features = {'glucose_mean': 130.0, 'glucose_min': 80.0, 'glucose_max': 180.0,
                   'glucose_std': 25.0, 'glucose_cv': 0.19, 'glucose_count': 10,
                   'sbp_mean': 115.0, 'sbp_min': 95.0, 'sbp_max': 135.0,
                   'sbp_std': 9.0, 'sbp_cv': 0.08, 'sbp_count': 40,
                   'map_mean': 88.0, 'map_min': 72.0, 'map_max': 102.0,
                   'map_std': 7.0, 'map_cv': 0.08, 'map_count': 40,
                   'los': 3.5}
        prediction = {'crisis_probability': 0.12, 'severity_level': 'LOW', 'crisis_type': 'none'}
        logger.log_inference(features, prediction, 'test_req_002', 'v1.0.0', 38.7)
        
        recent = logger.get_recent_logs(n=10)
        if len(recent) == 1 and recent[0]['request_id'] == 'test_req_002':
            results['passed'] += 1
            results['details'].append("Test 3 PASSED: Logged data retrievable")
        else:
            results['failed'] += 1
            results['details'].append("Test 3 FAILED: Could not retrieve logged data")
    
    # Test 4: Sanitization removes unexpected fields
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = TelemetryLogger(tmpdir, 'test_log.csv')
        features = {'glucose_mean': 140.0, 'glucose_min': 90.0, 'glucose_max': 190.0,
                   'glucose_std': 28.0, 'glucose_cv': 0.20, 'glucose_count': 12,
                   'sbp_mean': 118.0, 'sbp_min': 98.0, 'sbp_max': 138.0,
                   'sbp_std': 9.5, 'sbp_cv': 0.08, 'sbp_count': 45,
                   'map_mean': 89.0, 'map_min': 73.0, 'map_max': 103.0,
                   'map_std': 7.5, 'map_cv': 0.08, 'map_count': 45,
                   'los': 3.8, 'patient_name': 'REDACTED'}  # Unexpected field
        prediction = {'crisis_probability': 0.25, 'severity_level': 'LOW', 'crisis_type': 'none'}
        logger.log_inference(features, prediction, 'test_req_003', 'v1.0.0', 42.1)
        
        recent = logger.get_recent_logs(n=1)
        if 'patient_name' not in recent[0]:
            results['passed'] += 1
            results['details'].append("Test 4 PASSED: Unexpected fields sanitized")
        else:
            results['failed'] += 1
            results['details'].append("Test 4 FAILED: Unexpected field present in log")
    
    # Test 5: Log stats reporting
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = TelemetryLogger(tmpdir, 'test_log.csv')
        stats = logger.get_log_stats()
        if stats['record_count'] == 0 and 'file_size_bytes' in stats:
            results['passed'] += 1
            results['details'].append("Test 5 PASSED: Log stats reporting functional")
        else:
            results['failed'] += 1
            results['details'].append("Test 5 FAILED: Log stats incorrect")
    
    # Print summary
    print(f"\nUnit Test Summary: {results['passed']} passed, {results['failed']} failed")
    for detail in results['details']:
        print(f"  - {detail}")
    
    return results


if __name__ == '__main__':
    run_unit_tests()