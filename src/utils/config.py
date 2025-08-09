import os
from pathlib import Path
import yaml
from dataclasses import dataclass
from typing import Any, Dict

_DEFAULT_CONFIG_PATHS = [
    Path("config/config.yaml"),
    Path(__file__).resolve().parents[2] / "config" / "config.yaml",
]

@dataclass
class AppConfig:
    raw: Dict[str, Any]

    def get(self, path: str, default=None):
        """
        Dot-path getter: e.g. cfg.get("data.tickers")
        """
        cur = self.raw
        for key in path.split("."):
            if not isinstance(cur, dict) or key not in cur:
                return default
            cur = cur[key]
        return cur

def load_config(path: str | os.PathLike | None = None) -> AppConfig:
    candidates = [Path(path)] if path else _DEFAULT_CONFIG_PATHS
    for p in candidates:
        if p.exists():
            with open(p, "r") as f:
                data = yaml.safe_load(f) or {}
            return AppConfig(raw=data)
    raise FileNotFoundError(f"config.yaml not found. Tried: {candidates}")
