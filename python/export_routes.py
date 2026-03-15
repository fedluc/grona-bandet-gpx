import os
import shutil
import tempfile

from osgeo import ogr

from config import Config
from split_routes import split_all
from utils import delete_if_exists, ensure_dir, make_transform, wgs84_srs


def _export_file(gpx_driver, src_path: str, output_dir: str) -> None:
    src_ds = ogr.Open(src_path)
    if src_ds is None:
        print(f"Could not open {src_path}, skipping.")
        return

    src_layer = src_ds.GetLayer(0)
    track_name = os.path.splitext(os.path.basename(src_path))[0]
    out_path = os.path.join(output_dir, f"{track_name}.gpx")
    transform = make_transform(src_layer.GetSpatialRef())

    delete_if_exists(gpx_driver, out_path)

    out_ds = gpx_driver.CreateDataSource(out_path)
    # FORCE_GPX_TRACK: write LineString as <trk> instead of <rte>
    out_layer = out_ds.CreateLayer(
        "tracks",
        srs=wgs84_srs(),
        geom_type=ogr.wkbLineString,
        options=["FORCE_GPX_TRACK=YES"],
    )
    out_layer.CreateField(ogr.FieldDefn("name", ogr.OFTString))

    for feature in src_layer:
        geom = feature.GetGeometryRef().Clone()
        if transform:
            geom.Transform(transform)
        out_feature = ogr.Feature(out_layer.GetLayerDefn())
        out_feature.SetGeometry(geom)
        out_feature.SetField("name", feature.GetField("name") or track_name)
        out_layer.CreateFeature(out_feature)

    out_ds.FlushCache()
    out_ds = None
    src_ds = None
    print(f"  -> {os.path.basename(out_path)}")


def export_routes(config: Config) -> None:
    tmp_dir = tempfile.mkdtemp(prefix="gpx_split_")
    try:
        print("Splitting route files...")
        split_files = split_all(config, tmp_dir)
        if not split_files:
            return
        ensure_dir(config.output_dir)
        gpx_driver = ogr.GetDriverByName("GPX")
        print(f"\nExporting {len(split_files)} route file(s) to GPX...")
        for src_path in split_files:
            _export_file(gpx_driver, src_path, config.output_dir)
    finally:
        shutil.rmtree(tmp_dir)
