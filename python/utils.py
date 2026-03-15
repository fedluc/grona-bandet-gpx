import glob
import os

# Must be set before importing osgeo so PROJ can locate its database
os.environ.setdefault(
    "PROJ_DATA",
    "/Applications/QGIS.app/Contents/Resources/qgis/proj",
)

from osgeo import ogr, osr


def wgs84_srs() -> osr.SpatialReference:
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    # Traditional lon/lat order required by the GPX driver
    srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    return srs


def make_transform(src_srs: osr.SpatialReference) -> osr.CoordinateTransformation | None:
    if src_srs is None:
        return None
    if src_srs.GetAuthorityCode(None) == "4326":
        return None
    return osr.CoordinateTransformation(src_srs, wgs84_srs())


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def find_files(directory: str, pattern: str) -> list[str]:
    return sorted(glob.glob(os.path.join(directory, pattern)))


def delete_if_exists(driver, path: str) -> None:
    if os.path.exists(path):
        driver.DeleteDataSource(path)
