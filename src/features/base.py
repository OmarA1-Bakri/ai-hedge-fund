from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass(frozen=True)
class FeatureConfig:
    """
    Canonical feature config pulled from YAML. Provide safe defaults so we
    don't crash if a key is missing in config/config.yaml.
    """
    use_microstructure: bool = True
    use_regime: bool = False
    use_sentiment: bool = False
    use_fundamentals: bool = False
    windows: Optional[Dict[str, int]] = None

    @staticmethod
    def from_config_dict(cfg: Dict[str, Any]) -> "FeatureConfig":
        feats = cfg.get("features", {}) if cfg else {}
        return FeatureConfig(
            use_microstructure=feats.get("use_microstructure", True),
            use_regime=feats.get("use_regime", False),
            use_sentiment=feats.get("use_sentiment", False),
            use_fundamentals=feats.get("use_fundamentals", False),
            windows=feats.get("windows", {"mom_short": 5, "mom_long": 20, "vol_lookback": 20}),
        )
