# ==========================================
# TRACK 2 | INGESTION MODULE TEST SUITE
# Author: Swayam (Track 2: Complex Multi-Morbidity Core)
# Objective: Standalone pytest-compatible test suite.
#            Robust path resolution for both local and Colab environments.
# ==========================================

import pytest
import sys
import pathlib

# ---------------------------------------------------------
# DYNAMIC PATH RESOLUTION
# Automatically locates the project root to enable imports.
# Structure: .../track2_multimorbidity/data_ingestion/tests/test_ingestion.py
# ---------------------------------------------------------
try:
    this_file = pathlib.Path(__file__).resolve()
    # Go up 3 levels: tests -> data_ingestion -> track2_multimorbidity
    project_root = this_file.parent.parent.parent 
except NameError:
    # Fallback for interactive environments
    project_root = pathlib.Path.cwd() / "track2_multimorbidity"

sys.path.insert(0, str(project_root))

# Import the module under test
from data_ingestion.data_ingestion import DataIngestionPipeline, SchemaValidator, DataPreprocessor

import json
import numpy as np
import pandas as pd

@pytest.fixture
def schema_dir():
    """Returns path to schema directory."""
    colab_path = pathlib.Path('/content/track2_processed/schema')
    local_path = project_root / 'schema'
    return colab_path if colab_path.exists() else local_path

@pytest.fixture
def pipeline(schema_dir):
    """Initializes DataIngestionPipeline for testing."""
    return DataIngestionPipeline(schema_dir)

# ---------------------------------------------------------
# TEST SUITE: Schema Validation
# ---------------------------------------------------------
class TestSchemaValidation:
    """Tests for schema contract enforcement and invalid input rejection."""
    
    def test_unknown_feature_rejected(self, pipeline):
        """Verify that features not defined in schema are rejected."""
        invalid_record = {'nonexistent_feature': 100.0}
        result = pipeline.ingest_json(invalid_record)
        assert result['success'] is False
        assert 'errors' in result

    def test_missing_value_policy_enforced(self, pipeline):
        """Verify that missing values are handled via imputation."""
        missing_record = {
            'glucose_mean': None, 'glucose_min': 90.0, 'glucose_max': 170.0,
            'glucose_std': 25.0, 'glucose_cv': 0.2, 'glucose_count': 8, 'los': 4.0
        }
        result = pipeline.ingest_json(missing_record)
        assert result['success'] is True
        assert result['features']['glucose_mean'] > 0

# ---------------------------------------------------------
# TEST SUITE: Preprocessing Logic
# ---------------------------------------------------------
class TestPreprocessing:
    """Tests for physiological clipping and data transformation."""
    
    def test_physiological_clipping(self, pipeline):
        """Verify out-of-range high values are clipped to schema maximum."""
        outlier_record = {
            'glucose_mean': 650.0, 'glucose_min': 100.0, 'glucose_max': 200.0,
            'glucose_std': 30.0, 'glucose_cv': 0.18, 'glucose_count': 12, 'los': 5.0
        }
        result = pipeline.ingest_json(outlier_record)
        assert result['success'] is True
        assert result['features']['glucose_mean'] == 500.0

    def test_negative_clipping(self, pipeline):
        """Verify out-of-range low values are clipped to schema minimum."""
        low_record = {
            'glucose_mean': 20.0, 'glucose_min': 15.0, 'glucose_max': 40.0,
            'glucose_std': 5.0, 'glucose_cv': 0.1, 'glucose_count': 5, 'los': 2.0
        }
        result = pipeline.ingest_json(low_record)
        assert result['success'] is True
        assert result['features']['glucose_mean'] == 40.0

# ---------------------------------------------------------
# TEST SUITE: Batch Ingestion
# ---------------------------------------------------------
class TestBatchIngestion:
    """Tests for CSV batch processing pipeline."""
    
    def test_csv_ingestion_returns_dataframe(self, pipeline, tmp_path):
        """Verify batch CSV ingestion returns a valid DataFrame."""
        test_data = pd.DataFrame({
            'glucose_mean': [120, 150, 300],
            'glucose_min': [80, 90, 100],
            'glucose_max': [140, 180, 450],
            'glucose_std': [10, 20, 50],
            'glucose_cv': [0.1, 0.2, 0.3],
            'glucose_count': [5, 10, 15],
            'los': [2.0, 4.0, 6.0]
        })
        csv_path = tmp_path / "test_batch.csv"
        test_data.to_csv(csv_path, index=False)
        
        result_df = pipeline.ingest_batch_csv(csv_path)
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 3
        assert 'ingestion_timestamp' in result_df.columns

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])