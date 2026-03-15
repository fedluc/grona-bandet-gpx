"""
Split *_route.gpkg files and export each feature as a GPX track in WGS 84.

Split files are written to a temporary directory that is deleted on completion.
GPX files are written to OUTPUT_DIR (repo root by default).
Intended for use with Garmin inReach Mini 2 (imported via Garmin Explore).

Usage:
    /Applications/QGIS.app/Contents/MacOS/python python/export_routes_to_gpx.py
"""

import os
import shutil
import tempfile

# Must be set before importing osgeo so PROJ can locate its database
os.environ.setdefault(
    "PROJ_DATA",
    "/Applications/QGIS.app/Contents/Resources/qgis/proj",
)

from osgeo import ogr, osr

from split_route_features import split_all

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

script_dir = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(script_dir, "..")  # repo root


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def wgs84_srs():
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    # Use traditional lon/lat order (required by the GPX driver)
    srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    return srs


def make_transform(src_srs) -> osr.CoordinateTransformation | None:
    if src_srs is None:
        return None
    if src_srs.GetAuthorityCode(None) == "4326":
        return None
    return osr.CoordinateTransformation(src_srs, wgs84_srs())


def export_to_gpx(gpx_driver, src_path: str) -> None:
    src_ds = ogr.Open(src_path)
    if src_ds is None:
        print(f"Could not open {src_path}, skipping.")
        return

    src_layer = src_ds.GetLayer(0)
    track_name = os.path.splitext(os.path.basename(src_path))[0]
    out_path = os.path.join(OUTPUT_DIR, f"{track_name}.gpx")
    transform = make_transform(src_layer.GetSpatialRef())

    if os.path.exists(out_path):
        gpx_driver.DeleteDataSource(out_path)

    out_ds = gpx_driver.CreateDataSource(out_path)

    # FORCE_GPX_TRACK: write LineString as <trk> instead of <rte>
    out_layer = out_ds.CreateLayer(
        "tracks",
        srs=wgs84_srs(),
        geom_type=ogr.wkbLineString,
        options=["FORCE_GPX_TRACK=YES"],
    )

    name_field = ogr.FieldDefn("name", ogr.OFTString)
    out_layer.CreateField(name_field)

    for feature in src_layer:
        geom = feature.GetGeometryRef().Clone()
        if transform:
            geom.Transform(transform)

        out_feature = ogr.Feature(out_layer.GetLayerDefn())
        out_feature.SetGeometry(geom)
        out_feature.SetField("name", track_name)
        out_layer.CreateFeature(out_feature)

    out_ds.FlushCache()
    out_ds = None
    src_ds = None
    print(f"  -> {os.path.basename(out_path)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    tmp_dir = tempfile.mkdtemp(prefix="gpx_split_")
    try:
        print("Splitting route files...")
        split_files = split_all(tmp_dir)

        if not split_files:
            return

        gpx_driver = ogr.GetDriverByName("GPX")
        print(f"\nExporting {len(split_files)} file(s) to GPX...")
        for src_path in split_files:
            export_to_gpx(gpx_driver, src_path)
    finally:
        shutil.rmtree(tmp_dir)
        print(f"\nCleaned up temp dir: {tmp_dir}")

    print("Done.")


if __name__ == "__main__":
    main()
