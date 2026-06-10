"""Tiện ích: load config, setup logging."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import yaml


def load_config(config_path: str | Path = "config.yaml") -> dict:
    path = Path(config_path)
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    # Gắn root_dir để DataLoader tính đường dẫn tuyệt đối
    cfg["root_dir"] = str(path.parent)
    return cfg


def setup_logging(level: str = "INFO") -> None:
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=fmt,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
