# ensemble_layer/services/aggregator.py
"""
Core ensemble fusion logic: weighted aggregation of track predictions.
"""
import json
import pathlib
from typing import Dict, List, Optional, Union
from .risk_scorer import RiskScorer, RiskTier

class EnsembleAggregator:
    """Aggregates predictions from multiple tracks into unified risk assessment."""
    
    def __init__(self, config_path: Optional[pathlib.Path] = None):
        """Initialize with config path or defaults."""
        self.config_path = config_path
        self._load_config()
        self.risk_scorer = RiskScorer(config_path)
    
    def _load_config(self):
        """Load weights and aggregation rules from config."""
        if self.config_path and self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            self.weights = config['track_weights']
            self.track1_method = config['track1_aggregation']['method']
        else:
            # Defaults
            self.weights = {
                "track1_waveform": 0.25,
                "track2_multimorbidity": 0.30,
                "track3_mortality": 0.45
            }
            self.track1_method = "max"  # or "weighted_average"
    
    def aggregate_track1(self, track1_output: Dict) -> float:
        """
        Aggregate Track 1's 3 binary outputs into single probability.
        
        Track 1 output format:
        {
          "hypotension": {"label": 0, "probability": 0.04},
          "tachycardia": {"label": 0, "probability": 0.12},
          "oxygen_desaturation": {"label": 1, "probability": 0.87}
        }
        """
        probs = [
            track1_output.get("hypotension", {}).get("probability", 0.0),
            track1_output.get("tachycardia", {}).get("probability", 0.0),
            track1_output.get("oxygen_desaturation", {}).get("probability", 0.0)
        ]
        
        if self.track1_method == "max":
            return max(probs)
        elif self.track1_method == "weighted_average":
            # Weight SpO2 higher as it's most critical for early warning
            weights = [0.2, 0.2, 0.6]  # hypotension, tachycardia, spo2
            return sum(p * w for p, w in zip(probs, weights))
        else:
            return max(probs)  # fallback
    
    def aggregate(
        self,
        track1_output: Dict,
        track2_output: Dict,
        track3_output: Dict
    ) -> Dict[str, Union[float, str, Dict]]:
        """
        Aggregate all three track outputs into unified risk assessment.
        
        Args:
            track1_output: VitalDB waveform predictions
            track2_output: MIMIC+Pima multimorbidity predictions  
            track3_output: eICU mortality predictions
        
        Returns:
            Dict with:
            - risk_score: float (0.0-1.0)
            - risk_tier: "HIGH" | "MODERATE" | "LOW"
            - track_scores: Dict of individual track contributions
            - alert: Human-readable alert message
            - top_features: List of top contributing features across tracks
        """
        # Step 1: Extract individual track probabilities
        track1_score = self.aggregate_track1(track1_output)
        track2_score = track2_output.get("crisis_probability", 0.0)
        track3_score = track3_output.get("mortality_probability", 0.0)
        
        # Step 2: Apply weighted fusion
        risk_score = (
            self.weights["track1_waveform"] * track1_score +
            self.weights["track2_multimorbidity"] * track2_score +
            self.weights["track3_mortality"] * track3_score
        )
        risk_score = min(1.0, max(0.0, risk_score))  # Clamp to [0,1]
        
        # Step 3: Assign risk tier
        risk_tier = self.risk_scorer.score_to_tier(risk_score).value
        
        # Step 4: Conflict resolution (if individual tiers disagree)
        individual_tiers = [
            self.risk_scorer.score_to_tier(track1_score),
            self.risk_scorer.score_to_tier(track2_score),
            self.risk_scorer.score_to_tier(track3_score)
        ]
        resolved_tier = self.risk_scorer.resolve_conflict(individual_tiers).value
        
        # Use resolved tier if it's higher than weighted tier (safety first)
        tier_order = {"LOW": 0, "MODERATE": 1, "HIGH": 2}
        if tier_order[resolved_tier] > tier_order[risk_tier]:
            risk_tier = resolved_tier
        
        # Step 5: Generate alert message
        track_results = {
            "track1_waveform": {
                "hypotension": track1_output.get("hypotension", {}).get("probability", 0.0),
                "tachycardia": track1_output.get("tachycardia", {}).get("probability", 0.0),
                "spo2_drop": track1_output.get("oxygen_desaturation", {}).get("probability", 0.0)
            },
            "track2_multimorbidity": {
                "crisis_probability": track2_score,
                "severity": track2_output.get("severity_label", "UNKNOWN")
            },
            "track3_mortality": {
                "mortality_probability": track3_score,
                "risk_tier": track3_output.get("risk_tier", "UNKNOWN")
            }
        }
        alert = self.risk_scorer.generate_alert(RiskTier(risk_tier), track_results)
        
        # Step 6: Extract top contributing features (mock for now)
        # In production: aggregate SHAP values across tracks
        top_features = []
        if track1_score > 0.5:
            top_features.extend(["spo2_mean", "map_mean", "hr_variability"])
        if track2_score > 0.5:
            top_features.extend(["glucose_mean", "insulin_score", "comorbidity_flag"])
        if track3_score > 0.5:
            top_features.extend(["lactate_mean", "creatinine_mean", "sao2_mean"])
        # Deduplicate and limit to top 5
        seen = set()
        top_features = [f for f in top_features if not (f in seen or seen.add(f))][:5]
        
        return {
            "risk_score": round(risk_score, 4),
            "risk_tier": risk_tier,
            "track_scores": {
                "track1_waveform": round(track1_score, 4),
                "track2_multimorbidity": round(track2_score, 4),
                "track3_mortality": round(track3_score, 4)
            },
            "alert": alert,
            "top_features": top_features,
            "weights_used": self.weights
        }