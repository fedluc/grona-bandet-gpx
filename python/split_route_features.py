"""
Split features in *_route.gpkg files into separate GeoPackage files.

Each feature is saved as a new .gpkg file named stage<N>.<rescaled_fid>_route.gpkg.
Can be run standalone (writes to OUTPUT_DIR) or imported and called with a
custom output directory via split_all().

Usage:
    /Applications/QGIS.app/Contents/MacOS/python python/split_route_features.py
"""

import glob
import os

from osgeo import ogr

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

script_dir = os.path.dirname(os.path.abspath(__file__))
qgis_data_dir = os.path.join(script_dir, "..", "qgis_data")
OUTPUT_DIR = os.path.join(qgis_data_dir, "split")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def find_route_files(directory: str) -> list[str]:
    return sorted(glob.glob(os.path.join(directory, "*_route.gpkg")))


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def stage_number_from_path(src_path: str) -> str:
    # e.g. "stage1_route.gpkg" -> "1", "stage2_alt_route.gpkg" -> "2_alt"
    basename = os.path.basename(src_path)
    return basename.split("_route")[0].replace("stage", "")


def output_path(out_dir: str, stage_number: str, rescaled_fid: int) -> str:
    filename = f"stage{stage_number}.{rescaled_fid}_route.gpkg"
    return os.path.join(out_dir, filename)


def write_feature(driver, src_layer, feature, out_path: str) -> None:
    if os.path.exists(out_path):
        driver.DeleteDataSource(out_path)

    layer_defn = src_layer.GetLayerDefn()
    layer_name: str = os.path.splitext(os.path.basename(out_path))[0]

    out_ds = driver.CreateDataSource(out_path)
    out_layer = out_ds.CreateLayer(
        layer_name,
        srs=src_layer.GetSpatialRef(),
        geom_type=src_layer.GetGeomType(),
    )

    for i in range(layer_defn.GetFieldCount()):
        out_layer.CreateField(layer_defn.GetFieldDefn(i))

    out_feature = ogr.Feature(out_layer.GetLayerDefn())
    out_feature.SetGeometry(feature.GetGeometryRef().Clone())
    for i in range(layer_defn.GetFieldCount()):
        out_feature.SetField(layer_defn.GetFieldDefn(i).GetName(), feature.GetField(i))
    out_layer.CreateFeature(out_feature)

    out_ds.FlushCache()
    out_ds = None


def split_file(driver, src_path: str, out_dir: str) -> list[str]:
    """Split one source file into per-feature gpkg files. Returns output paths."""
    src_ds = ogr.Open(src_path)
    if src_ds is None:
        print(f"Could not open {src_path}, skipping.")
        return []

    src_layer = src_ds.GetLayer(0)
    stage_number: str = stage_number_from_path(src_path)
    print(f"{os.path.basename(src_path)}: {src_layer.GetFeatureCount()} feature(s)")

    features = sorted(src_layer, key=lambda f: f.GetFID())
    out_paths = []

    for rescaled_fid, feature in enumerate(features, start=1):
        out = output_path(out_dir, stage_number, rescaled_fid)
        write_feature(driver, src_layer, feature, out)
        out_paths.append(out)
        print(f"  -> {os.path.basename(out)}")

    src_ds = None
    return out_paths


# ---------------------------------------------------------------------------
# Public API (used by export_routes_to_gpx.py)
# ---------------------------------------------------------------------------


def split_all(out_dir: str) -> list[str]:
    """Split all *_route.gpkg files into out_dir. Returns list of output paths."""
    route_files = find_route_files(qgis_data_dir)
    if not route_files:
        print("No *_route.gpkg files found in qgis_data/")
        return []

    ensure_dir(out_dir)
    driver = ogr.GetDriverByName("GPKG")
    all_paths = []

    for src_path in route_files:
        all_paths.extend(split_file(driver, src_path, out_dir))

    return all_paths


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    split_all(OUTPUT_DIR)
    print("Done.")


if __name__ == "__main__":
    main()
