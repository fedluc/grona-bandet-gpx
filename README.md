# grona-bandet-gpx
A collection of gpx files that describe my Gröna Bandet route for Summer 2026. [Click here](https://fedluc.github.io/grona-bandet-gpx/) to visualize the route.

## Requirements

[QGIS](https://qgis.org) must be installed. The scripts use the QGIS bundled Python
interpreter and its GDAL/OGR bindings.

## Setup

Copy `.env.example` to `.env` and set `QGIS_PYTHON` to the path of the QGIS bundled
Python interpreter on your machine:

```bash
cp .env.example .env
# then edit .env
```

## Generating GPX files

```bash
source .env && $QGIS_PYTHON python/export_to_gpx.py
```

GPX files are written to the `gpx/` folder.
