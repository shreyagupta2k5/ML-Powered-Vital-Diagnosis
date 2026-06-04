# ensemble_layer/services/risk_scorer.py
"""Unified risk tier assignment and conflict resolution."""
import json
import pathlib
from typing import Dict, List, Literal, Optional
from enum import Enum

class RiskTier(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"

class RiskScorer:
    """Assigns unified risk tiers and resolves conflicts between tracks."""
    
    def __init__(self, config_path: Optional[pathlib.Path] = None):
        """Initialize with config or defaults."""
        # Defaults
        self.thresholds = {"CRITICAL": 0.85, "HIGH": 0.60, "MODERATE": 0.30, "LOW": 0.0}
        self.conflict_rule = "highest_risk_wins"
        
        # Load from JSON if available
        if config_path and config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            if 'ensemble_logic' in config:
                logic = config['ensemble_logic']
                self.thresholds = {
                    "CRITICAL": logic.get('CRITICAL_threshold', 0.85),
                    "HIGH": logic.get('HIGH_threshold', 0.60),
                    "MODERATE": logic.get('MODERATE_threshold', 0.30),
                    "LOW": 0.0
                }
                self.conflict_rule = logic.get('conflict_resolution', 'highest_risk_wins')
    
    def score_to_tier(self, score: float) -> RiskTier:
        """Convert numeric score to risk tier."""
        if score >= self.thresholds["CRITICAL"]:
            return RiskTier.CRITICAL
        elif score >= self.thresholds["HIGH"]:
            return RiskTier.HIGH
        elif score >= self.thresholds["MODERATE"]:
            return RiskTier.MODERATE
        else:
            return RiskTier.LOW
    
    def resolve_conflict(self, tiers: List[RiskTier]) -> RiskTier:
        """Resolve conflicts using configured rule."""
        tier_values = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}
        
        if self.conflict_rule == "weighted_average":
            # Average the tiers
            avg = sum(tier_values.get(t.value, 0) for t in tiers) / len(tiers)
            if avg >= 2.5: return RiskTier.CRITICAL
            if avg >= 1.5: return RiskTier.HIGH
            if avg >= 0.5: return RiskTier.MODERATE
            return RiskTier.LOW
        else:
            # Default: highest_risk_wins (Safety First)
            if RiskTier.CRITICAL in tiers: return RiskTier.CRITICAL
            if RiskTier.HIGH in tiers: return RiskTier.HIGH
            if RiskTier.MODERATE in tiers: return RiskTier.MODERATE
            return RiskTier.LOW
    
    def generate_alert(self, tier: RiskTier, dominant_track_type: str, features: List[str]) -> str:
        """Generate human-readable alert based on tier and dominant track."""
        if tier == RiskTier.CRITICAL:
            return f"CRITICAL — {dominant_track_type} detected. Immediate escalation required."
        elif tier == RiskTier.HIGH:
            return f"HIGH RISK — {dominant_track_type}. Close monitoring recommended."
        elif tier == RiskTier.MODERATE:
            return f"MODERATE — {dominant_track_type}. Continue standard monitoring."
        else:
            return "LOW RISK — Stable condition. Routine care."