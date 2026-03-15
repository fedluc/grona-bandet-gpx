import os
from dataclasses import dataclass

_PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.normpath(os.path.join(_PYTHON_DIR, ".."))


@dataclass
class Config:
    qgis_data_dir: str = os.path.join(_REPO_ROOT, "qgis_data")
    output_dir: str = os.path.join(_REPO_ROOT, "gpx")
