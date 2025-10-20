"""Configuration helpers for Posteract."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

_DEFAULT_CONFIG_PATH = Path("config.yaml")


def load_config(path: str | Path = _DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """Load Posteract configuration from YAML."""
    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)
