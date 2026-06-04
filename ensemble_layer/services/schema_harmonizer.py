# ensemble_layer/services/schema_harmonizer.py
"""
Schema Harmonization Service.
Maps different feature naming conventions across tracks to a unified standard.
"""
import json
import pathlib
from typing import Dict, List, Optional

class SchemaHarmonizer:
    """Maps feature names and standardizes output schemas."""
    
    def __init__(self, config_path: Optional[pathlib.Path] = None):
        self.feature_map = {}
        
        # Load from JSON if available
        if config_path and config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            if 'unified_features' in config:
                # Invert the map: TrackName -> UnifiedName
                for unified_name, track_variants in config['unified_features'].items():
                    for track_variant in track_variants.values():
                        if isinstance(track_variant, str):
                            self.feature_map[track_variant] = unified_name
        else:
            # Fallback minimal map if JSON missing
            self.feature_map = {
                "mean_hr": "heart_rate_mean",
                "mean_map": "mean_arterial_pressure_mean",
                "mean_spo2": "oxygen_saturation_mean",
            }
    
    def harmonize_feature_name(self, feature_name: str) -> str:
        """Return unified feature name or original if not found."""
        return self.feature_map.get(feature_name, feature_name)
    
    def harmonize_feature_list(self, features: List[str]) -> List[str]:
        """Harmonize a list of feature names."""
        return [self.harmonize_feature_name(f) for f in features]