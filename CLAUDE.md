# Gröna Bandet GPX — Claude Notes

## Project overview

This repo generates GPX files for a multi-stage hiking route (Gröna Bandet, Sweden) and
visualises them in a Leaflet map (`index.html`). Source data lives in `qgis_data/` as
GeoPackage (`.gpkg`) files edited in QGIS.

## Python environment

All Python must be run with the QGIS bundled interpreter:

```
/Applications/QGIS.app/Contents/MacOS/python
```

Scripts use `osgeo` (GDAL/OGR) which is bundled with QGIS — do not use system Python.
`PROJ_DATA` is set automatically in `python/utils.py` before osgeo is imported.

Because scripts import each other, always set `PYTHONPATH=python` when running from the
repo root:

```bash
PYTHONPATH=python /Applications/QGIS.app/Contents/MacOS/python python/export_to_gpx.py
```

## Generating GPX files

`python/export_to_gpx.py` is the single entry point. It:
1. Splits each `*_route.gpkg` into per-feature files in a temp dir (deleted on completion)
2. Exports each split file as a GPX track (`<trk>`) to `gpx/`
3. Exports each `*_resupply.gpkg` as GPX waypoints (`<wpt>`) to `gpx/`

GPX tracks use `FORCE_GPX_TRACK=YES` so LineString features become `<trk>` not `<rte>`.
Resupply descriptions use the standard `<desc>` element (not OGR extensions) so Garmin
devices and browsers can read them.

## Python file structure

```
python/
  config.py          # Config dataclass with default paths (qgis_data_dir, output_dir)
  utils.py           # Shared geo helpers: wgs84_srs, make_transform, find_files, ...
  split_routes.py    # Splits *_route.gpkg features into per-feature .gpkg files
  export_routes.py   # Exports split route files as GPX tracks
  export_resupply.py # Exports resupply files as GPX waypoints
  export_to_gpx.py   # Entry point — imports and calls the above
```

Internal helpers within a module are prefixed with `_`. Only the top-level functions
intended to be called from outside (`split_all`, `export_routes`, `export_resupply`) are
public.

## Visualisation

Serve the repo root over HTTP (not file://) to avoid CORS errors:

```bash
PYTHONPATH=python /Applications/QGIS.app/Contents/MacOS/python -m http.server 8080
```

Or use the VS Code task: **Terminal > Run Task > Serve index.html**, then open
http://localhost:8080.

Stage colours in `index.html` are controlled by the `stageColors` map keyed by stage
number. All `stage<N>_*` files (e.g. stage2 and stage2_alt) share the same colour.

## VS Code debugging

`launch.json` has a single config "Run with QGIS Python" that debugs whichever file is
currently active (`${file}`). Open a script, set breakpoints, press F5.

The launch config sets `PYTHONPATH` to `${workspaceFolder}/python` so cross-module
imports work when debugging any script.

## Type annotations in osgeo code

The osgeo bindings are SWIG-generated and do not expose all types as Python attributes.

- **Safe to annotate**: `osr.SpatialReference`, `osr.CoordinateTransformation` — these are
  real constructible classes accessible on the module.
- **Do not annotate**: objects returned from factory functions such as `ogr.GetDriverByName()`,
  `ogr.Open()`, `src_ds.GetLayer()`, etc. — the corresponding types (`ogr.Driver`,
  `ogr.DataSource`, `ogr.Layer`) do not exist as module attributes and will raise
  `AttributeError` at import time. Leave these parameters and variables unannotated.

## Key decisions

- **Split then export**: route files can contain multiple features (segments); they are
  split into one-feature-per-file before GPX export so each segment becomes a separate
  named track on the Garmin device.
- **Rescaled FIDs**: features are sorted by original FID and renumbered 1, 2, 3, ... to
  give stable, readable filenames like `stage2.1_route.gpx`.
- **WGS 84 / EPSG:4326 with OAMS_TRADITIONAL_GIS_ORDER**: required by the GPX driver
  which expects lon/lat, not lat/lon (GDAL 3+ default).
- **Temporary split dir**: split `.gpkg` files are intermediate artefacts and are deleted
  after export. `qgis_data/split/` and `qgis_data/gpx/` are in `.gitignore`. `gpx/` is
  committed to the repo.
