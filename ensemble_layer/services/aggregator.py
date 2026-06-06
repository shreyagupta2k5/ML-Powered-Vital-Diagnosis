# ensemble_layer/services/aggregator.py
"""
Core ensemble fusion logic: weighted aggregation of track predictions.
Updated for 4-tier system and dominant-track feature selection.
"""
import json
import pathlib
from typing import Dict, List, Optional, Union
from .risk_scorer import RiskScorer, RiskTier
from .schema_harmonizer import SchemaHarmonizer

class EnsembleAggregator:
    """Aggregates predictions from all three tracks into unified risk assessment."""
    
    def __init__(self, config_path: Optional[pathlib.Path] = None):
        self.config_path = config_path
        self._load_config()
        self.risk_scorer = RiskScorer(config_path)
        self.harmonizer = SchemaHarmonizer(config_path)
    
    def _load_config(self):
        if self.config_path and self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            self.weights = config['track_weights']
        else:
            self.weights = {
                "track1_eicu": 0.45,
                "track2_multimorbidity": 0.30,
                "track3_vitaldb": 0.25
            }
    
    def _get_track_probability(self, track_name: str, track_output: Dict) -> float:
        """Extract probability score from track output."""
        if track_name == "track1_eicu":
            # eICU router returns mortality_probability
            return track_output.get("mortality_probability", 0.0)
        elif track_name == "track2_multimorbidity":
            # MIMIC router returns crisis_probability
            return track_output.get("crisis_probability", 0.0)
        elif track_name == "track3_vitaldb":
            # VitalDB router returns flat keys for 3 events
            return max(
                track_output.get("hypotension_probability", 0.0),
                track_output.get("tachycardia_probability", 0.0),
                track_output.get("low_spo2_probability", 0.0)
            )
        return 0.0

    def _get_track_risk_type(self, track_name: str, track_output: Dict) -> str:
        """Extract human-readable risk description."""
        if track_name == "track1_eicu":
            tier = track_output.get("risk_tier", "UNKNOWN")
            return f"{tier} Mortality Risk"
        elif track_name == "track2_multimorbidity":
            return track_output.get("severity_level", "Multimorbidity Crisis")
        elif track_name == "track3_vitaldb":
            if track_output.get("low_spo2_probability", 0) > 0.7: return "SpO2 Desaturation"
            if track_output.get("hypotension_probability", 0) > 0.7: return "Hypotension"
            if track_output.get("tachycardia_probability", 0) > 0.7: return "Tachycardia"
            return "Waveform Instability"
        return "Unknown Risk"

    def aggregate(
        self,
        track1_output: Dict,
        track2_output: Dict,
        track3_output: Dict
    ) -> Dict[str, Union[float, str, Dict]]:
        """Aggregate all three track outputs into unified risk assessment."""
        tracks = {
            "track1_eicu": track1_output,
            "track2_multimorbidity": track2_output,
            "track3_vitaldb": track3_output
        }
        
        # Step 1: Calculate scores
        track_scores = {}
        for name, output in tracks.items():
            track_scores[name] = self._get_track_probability(name, output)
        
        # Step 2: Weighted Fusion
        risk_score = sum(
            track_scores[name] * self.weights.get(name, 0.0)
            for name in self.weights
        )
        risk_score = min(1.0, max(0.0, risk_score))
        
        # Step 3: Assign Risk Tier
        risk_tier = self.risk_scorer.score_to_tier(risk_score).value
        
        # Step 4: Conflict Resolution (Highest risk wins)
        individual_tiers = [self.risk_scorer.score_to_tier(s) for s in track_scores.values()]
        resolved_tier = self.risk_scorer.resolve_conflict(individual_tiers).value
        
        tier_order = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}
        if tier_order.get(resolved_tier, 0) > tier_order.get(risk_tier, 0):
            risk_tier = resolved_tier
        
        # Step 5: Select Top 3 Features from Highest-Scoring Track
        dominant_track = max(track_scores, key=track_scores.get)
        dominant_output = tracks[dominant_track]
        
        raw_features = []
        if dominant_track == "track1_eicu":
            # eICU returns list of dicts: [{"feature": "name", "shap_value": 0.1}, ...]
            raw_features = dominant_output.get("top_shap_drivers", [])
            raw_features = [f.get("feature", f) if isinstance(f, dict) else f for f in raw_features]
        elif dominant_track == "track2_multimorbidity":
            # MIMIC returns list of strings: ["glucose_mean", "sbp_mean"]
            raw_features = dominant_output.get("shap_top_drivers", [])
        elif dominant_track == "track3_vitaldb":
            # VitalDB currently doesn't return SHAP drivers
            raw_features = []
        
        harmonized_features = self.harmonizer.harmonize_feature_list(raw_features)
        top_features = harmonized_features[:3]
        
        # Step 6: Generate Alert
        dominant_type = self._get_track_risk_type(dominant_track, dominant_output)
        alert = self.risk_scorer.generate_alert(RiskTier(risk_tier), dominant_type, top_features)
        
        return {
            "risk_score": round(risk_score, 4),
            "risk_tier": risk_tier,
            "track_scores": {k: round(v, 4) for k, v in track_scores.items()},
            "alert": alert,
            "top_features": top_features,
            "dominant_track": dominant_track
        }