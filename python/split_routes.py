import os

from osgeo import ogr

from config import Config
from utils import delete_if_exists, ensure_dir, find_files


def _stage_number(src_path: str) -> str:
    # "stage1_route.gpkg" -> "1", "stage2_alt_route.gpkg" -> "2_alt"
    return os.path.basename(src_path).split("_route")[0].replace("stage", "")


def _split_path(out_dir: str, stage_number: str, rescaled_fid: int) -> str:
    return os.path.join(out_dir, f"stage{stage_number}.{rescaled_fid}_route.gpkg")


def _write_feature(driver, src_layer, feature, out_path: str) -> None:
    delete_if_exists(driver, out_path)

    layer_defn = src_layer.GetLayerDefn()
    out_ds = driver.CreateDataSource(out_path)
    out_layer = out_ds.CreateLayer(
        os.path.splitext(os.path.basename(out_path))[0],
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


def _split_file(driver, src_path: str, out_dir: str) -> list[str]:
    src_ds = ogr.Open(src_path)
    if src_ds is None:
        print(f"Could not open {src_path}, skipping.")
        return []

    src_layer = src_ds.GetLayer(0)
    stage_number = _stage_number(src_path)
    print(f"{os.path.basename(src_path)}: {src_layer.GetFeatureCount()} feature(s)")

    out_paths = []
    for rescaled_fid, feature in enumerate(
        sorted(src_layer, key=lambda f: f.GetFID()), start=1
    ):
        out = _split_path(out_dir, stage_number, rescaled_fid)
        _write_feature(driver, src_layer, feature, out)
        out_paths.append(out)
        print(f"  -> {os.path.basename(out)}")

    src_ds = None
    return out_paths


def split_all(config: Config, out_dir: str) -> list[str]:
    """Split all *_route.gpkg files into out_dir. Returns list of output paths."""
    route_files = find_files(config.qgis_data_dir, "*_route.gpkg")
    if not route_files:
        print("No *_route.gpkg files found in qgis_data/")
        return []

    ensure_dir(out_dir)
    driver = ogr.GetDriverByName("GPKG")
    return [
        path
        for src_path in route_files
        for path in _split_file(driver, src_path, out_dir)
    ]
