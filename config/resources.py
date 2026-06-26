"""
Runtime resource path helpers.
"""
import sys
from pathlib import Path


def app_root():
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def resource_path(*parts):
    return app_root().joinpath(*parts)
