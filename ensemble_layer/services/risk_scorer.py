# ensemble_layer/services/risk_scorer.py
"""
Unified risk tier assignment and conflict resolution.
"""
import json
import pathlib
from typing import Dict, List, Literal, Optional
from enum import Enum

class RiskTier(str, Enum):
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"

class RiskScorer:
    """Assigns unified risk tiers and resolves conflicts between tracks."""
    
    def __init__(self, config_path: Optional[pathlib.Path] = None):
        """Initialize with config or defaults."""
        if config_path and config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            self.tiers = config['risk_tiers']
            self.conflict_rule = config['conflict_resolution']['rule']
        else:
            # Defaults
            self.tiers = {
                "HIGH": {"min": 0.60, "max": 1.0, "action": "IMMEDIATE_ESCALATION"},
                "MODERATE": {"min": 0.30, "max": 0.60, "action": "MONITOR_CLOSELY"},
                "LOW": {"min": 0.0, "max": 0.30, "action": "ROUTINE_CARE"}
            }
            self.conflict_rule = "highest_risk_wins"
    
    def score_to_tier(self, score: float) -> RiskTier:
        """Convert numeric score to risk tier."""
        if score >= self.tiers["HIGH"]["min"]:
            return RiskTier.HIGH
        elif score >= self.tiers["MODERATE"]["min"]:
            return RiskTier.MODERATE
        else:
            return RiskTier.LOW
    
    def resolve_conflict(self, tiers: List[RiskTier]) -> RiskTier:
        """Resolve conflicts using configured rule."""
        if self.conflict_rule == "highest_risk_wins":
            # Order: HIGH > MODERATE > LOW
            if RiskTier.HIGH in tiers:
                return RiskTier.HIGH
            elif RiskTier.MODERATE in tiers:
                return RiskTier.MODERATE
            else:
                return RiskTier.LOW
        else:
            # Default fallback: average then score
            tier_values = {"HIGH": 1.0, "MODERATE": 0.5, "LOW": 0.0}
            avg = sum(tier_values[t.value] for t in tiers) / len(tiers)
            return self.score_to_tier(avg)
    
    def generate_alert(self, tier: RiskTier, track_results: Dict) -> str:
        """Generate human-readable alert based on tier and track outputs."""
        if tier == RiskTier.HIGH:
            alerts = []
            # Check Track 1 events
            if track_results.get("track1_waveform", {}).get("spo2_drop", 0) > 0.70:
                alerts.append("SpO2 Desaturation")
            if track_results.get("track1_waveform", {}).get("hypotension", 0) > 0.70:
                alerts.append("Hypotension")
            if track_results.get("track1_waveform", {}).get("tachycardia", 0) > 0.70:
                alerts.append("Tachycardia")
            # Check Track 2 crisis
            if track_results.get("track2_multimorbidity", {}).get("crisis_probability", 0) > 0.70:
                alerts.append("Multimorbidity Crisis")
            # Check Track 3 mortality
            if track_results.get("track3_mortality", {}).get("mortality_probability", 0) > 0.60:
                alerts.append("High Mortality Risk")
            
            if alerts:
                return f"CRITICAL — {' + '.join(alerts)}"
            else:
                return "CRITICAL — Elevated composite risk score"
        
        elif tier == RiskTier.MODERATE:
            return "MODERATE — Monitor patient closely; reassess in 1-2 hours"
        else:
            return "LOW — Continue routine care"