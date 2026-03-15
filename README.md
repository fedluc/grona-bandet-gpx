# grona-bandet-gpx
A collection of gpx files that describe my Gröna Bandet route for Summer 2026. [Click here](https://fedluc.github.io/grona-bandet-gpx/) to visualize the route.

## Requirements

[QGIS](https://qgis.org) must be installed. The scripts use the QGIS bundled Python
interpreter and its GDAL/OGR bindings.

## Generating GPX files

From the repo root, run:

```bash
PYTHONPATH=python <qgis-python> python/export_to_gpx.py
```

where `<qgis-python>` is the path to the QGIS Python interpreter. To find it, open the
QGIS Python Console and run `import sys; print(sys.executable)`.

GPX files are written to the `gpx/` folder.
