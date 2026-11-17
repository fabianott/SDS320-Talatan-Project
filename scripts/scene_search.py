"""Search and download Sentinel-2 scenes from the Microsoft Planetary Computer.

Two steps are needed in more than one notebook: find the acquisition days whose
scenes cover the study area with few clouds, and write one day's scenes to a
GeoTIFF. Both live here, so that the study area, the bands, the projection and
the resolution are defined once and every scene in the project is built the
same way.

Notebook 01 uses both functions, for the training scenes of 2020 and for the
prediction scene of 2026; notebook 05 uses them for one scene per year.
"""

from collections import defaultdict

import numpy as np
import odc.stac
import planetary_computer as pc
import rioxarray  # noqa: F401  (registers the .rio accessor used below)
from pystac_client import Client
from shapely.geometry import box, shape
from shapely.ops import unary_union

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
COLLECTION = "sentinel-2-l2a"

# Study area: [min_lon, min_lat, max_lon, max_lat] in WGS84, shifted south of
# the park centre so that the whole installation falls inside the box.
TALATAN_BBOX = [100.132, 35.87, 100.665, 36.23]

BANDS = ["B02", "B03", "B04", "B08"]   # blue, green, red, near infrared
CRS = "EPSG:32647"                     # WGS 84 / UTM zone 47N
RESOLUTION = 10                        # metres per pixel


def search_scenes(bbox, start, end, max_cloud=10, min_coverage=0.99):
    """Find acquisition days that cover the study area with few clouds.

    One acquisition day can consist of several STAC items, because the study
    area straddles two Sentinel-2 tiles. Items are therefore grouped by day and
    judged together.

    Args:
        bbox: Study area as [min_lon, min_lat, max_lon, max_lat] in WGS84.
        start: First date of the search period, as "YYYY-MM-DD".
        end: Last date of the search period, as "YYYY-MM-DD".
        max_cloud: Maximum cloud cover in percent. The value in the STAC
            metadata refers to a whole Sentinel-2 tile of about 110 by 110 km,
            so it works as a coarse pre-filter only. Screen the Scene
            Classification Layer for anything finer.
        min_coverage: Minimum share of the study area that a day's scenes must
            cover, between 0 and 1. Pass 0.0 to keep partially covered days.

    Returns:
        A list of dicts with the keys "day" (datetime.date), "items" (the STAC
        items of that day), "coverage" (0 to 1) and "clouds" (percent), sorted
        by cloud cover, lowest first.
    """
    items = list(
        Client.open(STAC_URL)
        .search(
            collections=[COLLECTION],
            bbox=bbox,
            datetime=f"{start}/{end}",
            query={"eo:cloud_cover": {"lt": max_cloud}},
        )
        .items()
    )

    by_day = defaultdict(list)
    for item in items:
        by_day[item.datetime.date()].append(item)

    aoi = box(*bbox)
    days = []

    for day, day_items in by_day.items():
        footprint = unary_union([shape(item.geometry) for item in day_items])
        coverage = footprint.intersection(aoi).area / aoi.area
        if coverage < min_coverage:
            continue
        days.append(
            {
                "day": day,
                "items": day_items,
                "coverage": coverage,
                "clouds": float(np.mean([i.properties["eo:cloud_cover"] for i in day_items])),
            }
        )

    return sorted(days, key=lambda d: d["clouds"])


def download_scene(
    items,
    bbox,
    out_path,
    bands=BANDS,
    crs=CRS,
    resolution=RESOLUTION,
    overwrite=False,
):
    """Write the scenes of one acquisition day to a multiband GeoTIFF.

    Reflectance is kept as unsigned 16-bit integers, exactly as delivered: the
    scaling to 8 bit that the model needs happens later, in
    preprocessing.scale_to_byte, so that the raw values stay available.

    Args:
        items: Unsigned STAC items of one day, as returned by search_scenes.
        bbox: Study area as [min_lon, min_lat, max_lon, max_lat] in WGS84.
        out_path: Target path of the GeoTIFF. Parent folders are created.
        bands: Band names in the order they are written.
        crs: Target coordinate reference system.
        resolution: Target resolution in metres.
        overwrite: If False, an existing file is kept and nothing is
            downloaded, which makes a rerun of the notebook cheap.

    Returns:
        out_path.
    """
    if out_path.exists() and not overwrite:
        return out_path

    data = (
        odc.stac.load(
            [pc.sign(item) for item in items],
            bands=bands,
            bbox=bbox,
            crs=crs,
            resolution=resolution,
            groupby="solar_day",
        )
        .isel(time=0)
        .compute()
    )

    raster = data[bands].to_array("band").astype("uint16")
    raster.rio.write_crs(crs, inplace=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    raster.rio.to_raster(out_path, compress="deflate", tiled=True)
    return out_path
