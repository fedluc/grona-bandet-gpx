"""
Split features in *_route.gpkg files into separate GeoPackage files.

Each feature is saved as a new .gpkg file named <fid>_<name>.gpkg,
written to OUTPUT_DIR.

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


def stage_from_path(src_path: str) -> str:
    basename = os.path.basename(src_path)
    return basename.split("_route")[0]


def output_path(stage: str, fid: int, name: str) -> str:
    filename = f"stage_{stage}_fid_{fid}_name_{name}.gpkg"
    return os.path.join(OUTPUT_DIR, filename)


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


def split_file(driver, src_path: str) -> None:
    src_ds = ogr.Open(src_path)
    if src_ds is None:
        print(f"Could not open {src_path}, skipping.")
        return

    src_layer = src_ds.GetLayer(0)
    stage: str = stage_from_path(src_path)
    print(f"{os.path.basename(src_path)}: {src_layer.GetFeatureCount()} feature(s)")

    for feature in src_layer:
        fid: int = feature.GetFID()
        name: str = feature.GetField("name")
        out: str = output_path(stage, fid, name)
        write_feature(driver, src_layer, feature, out)
        print(f"  -> {os.path.basename(out)}")

    src_ds = None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    route_files = find_route_files(qgis_data_dir)
    if not route_files:
        print("No *_route.gpkg files found in qgis_data/")
        return

    ensure_dir(OUTPUT_DIR)
    driver = ogr.GetDriverByName("GPKG")

    for src_path in route_files:
        split_file(driver, src_path)

    print("Done.")


if __name__ == "__main__":
    main()
