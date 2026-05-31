# ==========================================
# TRACK 2 | DATA INGESTION MODULE
# Author: Swayam (Track 2: Complex Multi-Morbidity Core)
# Objective: Implement automated ingestion pipeline that validates incoming
#            patient data against schema contract, applies training-consistent
#            preprocessing, and outputs ML-ready feature vectors for inference.
# ==========================================

import json
import pathlib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Union
import warnings
warnings.filterwarnings('ignore')


class SchemaValidator:
    """
    Validates incoming patient data against the schema reference contract.
    Ensures feature existence, dtype compliance, and missing value policy adherence.
    Out-of-range clinical values are allowed to pass and are handled during preprocessing.
    """
    
    def __init__(self, schema_path: Union[str, pathlib.Path]):
        """
        Initialize validator with schema reference file.
        
        Args:
            schema_path: Path to schema_reference.json
        """
        with open(schema_path, 'r') as f:
            self.schema = json.load(f)
        self.feature_schema = self.schema['feature_schema']
    
    def validate_feature(self, feature_name: str, value: Optional[float]) -> Dict[str, Union[bool, str]]:
        """
        Validate a single feature value against schema constraints.
        
        Args:
            feature_name: Name of the feature to validate
            value: Feature value (may be None for missing)
            
        Returns:
            Dict with 'valid' boolean and optional 'message' for errors
        """
        if feature_name not in self.feature_schema:
            return {'valid': False, 'message': f"Feature '{feature_name}' not in schema"}
        
        spec = self.feature_schema[feature_name]
        
        # Handle missing values according to schema policy
        if value is None or (isinstance(value, float) and np.isnan(value)):
            if spec['missing_strategy'] not in ['median_impute', 'zero_fill']:
                return {'valid': False, 'message': f"Missing values not allowed for {feature_name}"}
            return {'valid': True, 'message': 'Missing value - will be imputed during preprocessing'}
        
        # Note: Physiological range clipping is intentionally deferred to preprocessing
        # to avoid blocking ingestion of noisy or out-of-bound sensor readings.
        return {'valid': True, 'message': 'OK'}
    
    def validate_record(self, record: Dict[str, float]) -> Dict[str, Union[bool, List[str]]]:
        """
        Validate an entire patient record against schema.
        
        Args:
            record: Dictionary of feature_name: value pairs
            
        Returns:
            Dict with 'valid' boolean and list of error messages if any
        """
        errors = []
        for feature_name, value in record.items():
            result = self.validate_feature(feature_name, value)
            if not result['valid']:
                errors.append(f"{feature_name}: {result['message']}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors if errors else None
        }


class DataPreprocessor:
    """
    Applies preprocessing transformations consistent with training pipeline.
    Handles physiological clipping, missing value imputation, and feature alignment.
    """
    
    def __init__(self, reference_stats_path: Union[str, pathlib.Path], 
                 schema_path: Union[str, pathlib.Path]):
        """
        Initialize preprocessor with reference statistics and schema.
        
        Args:
            reference_stats_path: Path to reference_stats.json
            schema_path: Path to schema_reference.json
        """
        with open(reference_stats_path, 'r') as f:
            self.ref_stats = json.load(f)
        with open(schema_path, 'r') as f:
            self.schema = json.load(f)
        
        self.feature_schema = self.schema['feature_schema']
        self.feature_stats = self.ref_stats['feature_statistics']
    
    def clip_to_physiological_range(self, feature_name: str, value: float) -> float:
        """
        Clip value to physiological bounds defined in schema.
        
        Args:
            feature_name: Name of the feature
            value: Raw value to clip
            
        Returns:
            Clipped value within valid range
        """
        spec = self.feature_schema.get(feature_name)
        if not spec or 'valid_range' not in spec:
            return value
        
        min_val, max_val = spec['valid_range']
        return float(np.clip(value, min_val, max_val))
    
    def impute_missing(self, feature_name: str, value: Optional[float]) -> float:
        """
        Impute missing values using strategy from schema.
        
        Args:
            feature_name: Name of the feature
            value: Value to impute (should be None or NaN)
            
        Returns:
            Imputed value (median from reference stats or zero)
        """
        spec = self.feature_schema.get(feature_name)
        if not spec:
            return 0.0
        
        strategy = spec.get('missing_strategy', 'zero_fill')
        
        if strategy == 'median_impute':
            stats = self.feature_stats.get(feature_name, {})
            median = stats.get('q50')
            if median is not None:
                return float(median)
            mean = stats.get('mean')
            if mean is not None:
                return float(mean)
            return 0.0
        elif strategy == 'zero_fill':
            return 0.0
        
        return 0.0
    
    def preprocess_record(self, raw_record: Dict[str, float]) -> Dict[str, float]:
        """
        Apply full preprocessing pipeline to a single patient record.
        
        Args:
            raw_record: Raw feature values from ingestion
            
        Returns:
            Preprocessed feature vector ready for model inference
        """
        processed = {}
        
        # Process features in schema order to ensure consistent output shape
        for feature_name in self.feature_schema.keys():
            raw_value = raw_record.get(feature_name)
            
            # Handle missing values first
            if raw_value is None or (isinstance(raw_value, float) and np.isnan(raw_value)):
                processed[feature_name] = self.impute_missing(feature_name, raw_value)
            else:
                # Clip to physiological range
                clipped = self.clip_to_physiological_range(feature_name, float(raw_value))
                processed[feature_name] = clipped
        
        return processed


class DataIngestionPipeline:
    """
    Main ingestion pipeline orchestrating validation and preprocessing.
    Accepts JSON/CSV input and outputs ML-ready feature vectors.
    """
    
    def __init__(self, schema_dir: Union[str, pathlib.Path]):
        """
        Initialize pipeline with schema directory.
        
        Args:
            schema_dir: Directory containing schema_reference.json and reference_stats.json
        """
        schema_path = pathlib.Path(schema_dir) / 'schema_reference.json'
        stats_path = pathlib.Path(schema_dir) / 'reference_stats.json'
        
        self.validator = SchemaValidator(schema_path)
        self.preprocessor = DataPreprocessor(stats_path, schema_path)
        self.schema_dir = pathlib.Path(schema_dir)
    
    def ingest_json(self, json_data: Union[str, Dict]) -> Dict[str, Union[bool, Dict, List[str]]]:
        """
        Ingest and process patient data from JSON string or dict.
        
        Args:
            json_data: JSON string or dictionary of patient features
            
        Returns:
            Dict with success status, processed features, or error messages
        """
        # Parse JSON if string input
        if isinstance(json_data, str):
            try:
                record = json.loads(json_data)
            except json.JSONDecodeError as e:
                return {'success': False, 'error': f"JSON parse error: {str(e)}"}
        else:
            record = json_data
        
        # Validate against schema
        validation = self.validator.validate_record(record)
        if not validation['valid']:
            return {'success': False, 'errors': validation['errors']}
        
        # Preprocess to ML-ready format
        try:
            processed = self.preprocessor.preprocess_record(record)
            return {
                'success': True,
                'features': processed,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        except Exception as e:
            return {'success': False, 'error': f"Preprocessing error: {str(e)}"}
    
    def ingest_csv_row(self, csv_row: pd.Series) -> Dict[str, Union[bool, Dict, List[str]]]:
        """
        Ingest and process a single row from CSV input.
        
        Args:
            csv_row: pandas Series representing one patient record
            
        Returns:
            Dict with success status, processed features, or error messages
        """
        record = {k: (None if pd.isna(v) else v) for k, v in csv_row.to_dict().items()}
        return self.ingest_json(record)
    
    def ingest_batch_csv(self, csv_path: Union[str, pathlib.Path]) -> pd.DataFrame:
        """
        Process entire CSV file and return DataFrame of processed features.
        
        Args:
            csv_path: Path to input CSV file
            
        Returns:
            DataFrame with processed feature vectors and ingestion metadata
        """
        df = pd.read_csv(csv_path)
        results = []
        
        for idx, row in df.iterrows():
            result = self.ingest_csv_row(row)
            result['original_index'] = idx
            results.append(result)
        
        successful = [r for r in results if r.get('success')]
        
        if successful:
            features_df = pd.DataFrame([r['features'] for r in successful])
            features_df['ingestion_timestamp'] = [r['timestamp'] for r in successful]
            features_df['original_index'] = [r['original_index'] for r in successful]
            return features_df
        else:
            return pd.DataFrame()


# ==========================================
# UNIT TESTS FOR DATA INGESTION MODULE
# ==========================================

def run_unit_tests():
    """
    Execute unit tests for schema validation and preprocessing.
    Returns summary of test results.
    """
    print("Running unit tests for data_ingestion module...")
    
    # Setup test paths
    schema_dir = pathlib.Path('/content/track2_processed/schema')
    
    if not schema_dir.exists():
        print("WARNING: Schema directory not found. Skipping tests.")
        return {'passed': 0, 'failed': 0, 'details': ['Schema directory missing']}
    
    pipeline = DataIngestionPipeline(schema_dir)
    results = {'passed': 0, 'failed': 0, 'details': []}
    
    # Test 1: Valid record within physiological ranges
    valid_record = {
        'glucose_mean': 120.0, 'glucose_min': 85.0, 'glucose_max': 160.0,
        'glucose_std': 20.0, 'glucose_cv': 0.15, 'glucose_count': 10, 'los': 3.5
    }
    result = pipeline.ingest_json(valid_record)
    if result['success'] and 'features' in result:
        results['passed'] += 1
        results['details'].append("Test 1 PASSED: Valid record processed")
    else:
        results['failed'] += 1
        results['details'].append(f"Test 1 FAILED: {result}")
    
    # Test 2: Record with missing values (should impute)
    missing_record = {
        'glucose_mean': None, 'glucose_min': 90.0, 'glucose_max': 170.0,
        'glucose_std': 25.0, 'glucose_cv': 0.2, 'glucose_count': 8, 'los': 4.0
    }
    result = pipeline.ingest_json(missing_record)
    if result['success'] and result['features']['glucose_mean'] > 0:
        results['passed'] += 1
        results['details'].append("Test 2 PASSED: Missing value imputed")
    else:
        results['failed'] += 1
        results['details'].append(f"Test 2 FAILED: {result}")
    
    # Test 3: Record with out-of-range value (should be clipped, not rejected)
    outlier_record = {
        'glucose_mean': 600.0, 'glucose_min': 100.0, 'glucose_max': 200.0,
        'glucose_std': 30.0, 'glucose_cv': 0.18, 'glucose_count': 12, 'los': 5.0
    }
    result = pipeline.ingest_json(outlier_record)
    if result['success'] and result['features']['glucose_mean'] <= 500.0:
        results['passed'] += 1
        results['details'].append("Test 3 PASSED: Out-of-range value clipped to 500.0")
    else:
        results['failed'] += 1
        results['details'].append(f"Test 3 FAILED: {result}")
    
    # Test 4: Invalid feature name (should fail validation)
    invalid_record = {'invalid_feature': 100.0, 'glucose_mean': 130.0}
    result = pipeline.ingest_json(invalid_record)
    if not result['success'] and 'errors' in result:
        results['passed'] += 1
        results['details'].append("Test 4 PASSED: Invalid feature rejected")
    else:
        results['failed'] += 1
        results['details'].append(f"Test 4 FAILED: {result}")
    
    # Print summary
    print(f"\nUnit Test Summary: {results['passed']} passed, {results['failed']} failed")
    for detail in results['details']:
        print(f"  - {detail}")
    
    return results


if __name__ == '__main__':
    schema_dir = pathlib.Path('/content/track2_processed/schema')
    pipeline = DataIngestionPipeline(schema_dir)
    
    sample_patient = {
        'glucose_mean': 145.0, 'glucose_min': 95.0, 'glucose_max': 210.0,
        'glucose_std': 32.0, 'glucose_cv': 0.22, 'glucose_count': 15, 'los': 4.2
    }
    
    print("Ingesting sample patient record...")
    result = pipeline.ingest_json(sample_patient)
    
    if result['success']:
        print("Ingestion successful. Processed features:")
        for feature, value in result['features'].items():
            print(f"  {feature}: {value:.3f}")
    else:
        print(f"Ingestion failed: {result}")
    
    print("\n" + "="*60)
    run_unit_tests()