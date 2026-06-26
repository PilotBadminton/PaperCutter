"""
持久化模块 — 记住用户上次选择的输出路径
"""
import json
import os
import sys
from pathlib import Path


def _config_dir():
    if getattr(sys, 'frozen', False):
        base = Path(os.environ.get('APPDATA', Path(sys.executable).parent))
    else:
        base = Path.cwd()
    cfg_dir = base / "切题辅助工具"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir


def _config_path():
    return _config_dir() / "config.json"


def load() -> dict:
    path = _config_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}


def save(data: dict):
    path = _config_path()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def update(data: dict):
    cfg = load()
    cfg.update(data)
    save(cfg)
