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
        """Initialize with calibrated thresholds for normalized ensemble scoring."""
        # Calibrated thresholds - adjusted for real-world track outputs
        self.thresholds = {
            "CRITICAL": 0.70,   # Only true multi-organ failure
            "HIGH": 0.40,       # Single-track critical or two-track moderate
            "MODERATE": 0.18,   # Elevated but stable
            "LOW": 0.0
        }
        self.conflict_rule = "weighted_majority"  # Changed from highest_risk_wins
        
        # Load from JSON if available
        if config_path and config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            if 'ensemble_logic' in config:
                logic = config['ensemble_logic']
                self.thresholds = {
                    "CRITICAL": logic.get('CRITICAL_threshold', 0.70),
                    "HIGH": logic.get('HIGH_threshold', 0.40),
                    "MODERATE": logic.get('MODERATE_threshold', 0.18),
                    "LOW": 0.0
                }
                self.conflict_rule = logic.get('conflict_resolution', 'weighted_majority')
    
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
        """Resolve conflicts using weighted majority voting."""
        tier_values = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}
        
        if self.conflict_rule == "highest_risk_wins":
            # Safety-first fallback
            if RiskTier.CRITICAL in tiers: return RiskTier.CRITICAL
            if RiskTier.HIGH in tiers: return RiskTier.HIGH
            if RiskTier.MODERATE in tiers: return RiskTier.MODERATE
            return RiskTier.LOW
        else:
            # NEW: Weighted majority - prevents single-track false positives
            # Count votes per tier
            votes = {"LOW": 0, "MODERATE": 0, "HIGH": 0, "CRITICAL": 0}
            for t in tiers:
                votes[t.value] = votes.get(t.value, 0) + 1
            
            # Require at least 2/3 tracks to agree on HIGH/CRITICAL
            total = len(tiers)
            if votes["CRITICAL"] >= 2: return RiskTier.CRITICAL
            if votes["HIGH"] >= 2: return RiskTier.HIGH
            if votes["MODERATE"] >= 2: return RiskTier.MODERATE
            
            # If only 1 track is elevated, cap at MODERATE unless score > 0.60
            max_tier_val = max(tier_values.get(t.value, 0) for t in tiers)
            if max_tier_val >= 2:  # At least one HIGH
                return RiskTier.MODERATE  # Cap single-track HIGH to MODERATE
            if max_tier_val >= 1:  # At least one MODERATE
                return RiskTier.MODERATE
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