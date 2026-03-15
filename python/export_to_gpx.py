"""
Export all GPX files (routes and resupply) from qgis_data to the repo root.

Usage:
    PYTHONPATH=python /Applications/QGIS.app/Contents/MacOS/python python/export_to_gpx.py
"""

from config import Config
from export_resupply import export_resupply
from export_routes import export_routes


def main() -> None:
    config = Config()

    print("=== Routes ===")
    export_routes(config)

    print("\n=== Resupply ===")
    export_resupply(config)

    print("\nDone.")


if __name__ == "__main__":
    main()
