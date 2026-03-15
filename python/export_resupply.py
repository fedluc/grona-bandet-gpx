import os

from osgeo import ogr

from config import Config
from utils import delete_if_exists, ensure_dir, find_files, make_transform, wgs84_srs


def _export_file(gpx_driver, src_path: str, output_dir: str) -> None:
    src_ds = ogr.Open(src_path)
    if src_ds is None:
        print(f"Could not open {src_path}, skipping.")
        return

    src_layer = src_ds.GetLayer(0)
    stem = os.path.splitext(os.path.basename(src_path))[0]
    out_path = os.path.join(output_dir, f"{stem}.gpx")
    transform = make_transform(src_layer.GetSpatialRef())

    delete_if_exists(gpx_driver, out_path)

    out_ds = gpx_driver.CreateDataSource(out_path)
    out_layer = out_ds.CreateLayer(
        "waypoints",
        srs=wgs84_srs(),
        geom_type=ogr.wkbPoint,
    )
    # Standard GPX fields — written as <name> and <desc>, not extensions
    out_layer.CreateField(ogr.FieldDefn("name", ogr.OFTString))
    out_layer.CreateField(ogr.FieldDefn("desc", ogr.OFTString))

    for feature in src_layer:
        geom = feature.GetGeometryRef().Clone()
        if transform:
            geom.Transform(transform)
        out_feature = ogr.Feature(out_layer.GetLayerDefn())
        out_feature.SetGeometry(geom)
        out_feature.SetField("name", feature.GetField("Name"))
        out_feature.SetField("desc", feature.GetField("Description"))
        out_layer.CreateFeature(out_feature)

    out_ds.FlushCache()
    out_ds = None
    src_ds = None
    print(f"  -> {os.path.basename(out_path)}")


def export_resupply(config: Config) -> None:
    resupply_files = find_files(config.qgis_data_dir, "*_resupply.gpkg")
    if not resupply_files:
        print("No *_resupply.gpkg files found in qgis_data/")
        return
    ensure_dir(config.output_dir)
    gpx_driver = ogr.GetDriverByName("GPX")
    print(f"Exporting {len(resupply_files)} resupply file(s) to GPX...")
    for src_path in resupply_files:
        _export_file(gpx_driver, src_path, config.output_dir)
