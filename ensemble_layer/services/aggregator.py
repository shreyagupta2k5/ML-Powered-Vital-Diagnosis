# ensemble_layer/services/aggregator.py
"""
Core ensemble fusion logic: weighted aggregation of track predictions.
Updated for 4-tier system, dominant-track feature selection, and multi-track SHAP merging.
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
            return track_output.get("mortality_probability", 0.0)
        elif track_name == "track2_multimorbidity":
            return track_output.get("crisis_probability", 0.0)
        elif track_name == "track3_vitaldb":
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

    def _merge_shap_drivers(self, tracks: Dict) -> List[Dict]:
        """Merge SHAP drivers from all active tracks into a unified list."""
        merged = []
        
        # Track 1 has full SHAP objects with values
        if "track1_eicu" in tracks and tracks["track1_eicu"]:
            t1 = tracks["track1_eicu"]
            if "top_shap_drivers" in t1:
                for driver in t1["top_shap_drivers"]:
                    if isinstance(driver, dict):
                        merged.append({
                            "feature": driver.get("feature", "unknown"),
                            "shap_value": abs(driver.get("shap_value", 0)),
                            "direction": driver.get("direction", "increases_risk")
                        })
        
        # Track 2 has string list - convert to objects with descending weights
        if "track2_multimorbidity" in tracks and tracks["track2_multimorbidity"]:
            t2 = tracks["track2_multimorbidity"]
            if "shap_top_drivers" in t2 and isinstance(t2["shap_top_drivers"], list):
                weight = 0.95  # Start slightly below 1.0 to rank below Track 1's real values
                for feat in t2["shap_top_drivers"]:
                    merged.append({
                        "feature": feat,
                        "shap_value": round(weight, 4),
                        "direction": "increases_risk"
                    })
                    weight -= 0.1
        
        # Track 3 currently doesn't return SHAP drivers - skip
        
        # Sort by shap_value descending and return top 5
        merged.sort(key=lambda x: x.get("shap_value", 0), reverse=True)
        return merged[:5]

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
        
        # Step 5: Merge Top Features from ALL Active Tracks (NEW)
        top_features = self._merge_shap_drivers(tracks)
        
        # Step 6: Generate Alert
        dominant_track = max(track_scores, key=track_scores.get)
        dominant_output = tracks[dominant_track]
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