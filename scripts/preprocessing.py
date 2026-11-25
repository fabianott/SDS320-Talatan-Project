"""Preparation of Sentinel-2 scenes for the segmentation model."""

import numpy as np
import rasterio

# Reflectance mapped to 255, one value per band in the order of scene_search.BANDS
# (B02, B03, B04, B08, B11, B12). 4000 lies above the 99th percentile of all scenes
# for the four 10 m bands. Dry, bright soil is brighter in the shortwave infrared, so
# B11 and B12 get the 99th percentile of the 2020 training scenes, rounded up to the
# next 500 (computed in notebook 02).
MAX_REFLECTANCE = np.array([4000, 4000, 4000, 4000, 4500, 4000])
BASELINE_OFFSET = 1000   # added to Level-2A reflectance since processing baseline 04.00 (January 2022)


def scale_to_byte(in_path, out_path, offset=0, max_reflectance=MAX_REFLECTANCE):
    """Rescale a Sentinel-2 scene to the 0-255 range and write it as 8 bit.

    geoai divides every input image by 255 before it reaches the model, both
    while training and while predicting, which assumes 8 bit imagery. Sentinel-2
    reflectance values of several thousand therefore end up far outside the
    0 to 1 range the ImageNet encoder was trained on, and the brightness and
    contrast augmentations clip everything above 1 to white. Mapping the
    reflectance to 0 to 255 beforehand keeps the model in the range it expects.

    The same mapping is used for the training tiles and for every scene the
    model is applied to, so scenes of different years stay comparable. Every
    band has its own upper limit, see MAX_REFLECTANCE.

    Args:
        in_path: Sentinel-2 GeoTIFF holding reflectance values.
        out_path: Path of the 8 bit output file.
        offset: Value subtracted before scaling. Use BASELINE_OFFSET for scenes
            acquired from January 2022 onwards, 0 for earlier ones.
        max_reflectance: Reflectance that becomes 255, either one value for all
            bands or one value per band. Higher values are clipped.

    Returns:
        Path to the written file.
    """
    limits = np.asarray(max_reflectance, dtype="float32")
    if limits.ndim == 1:
        limits = limits[:, None, None]   # one limit per band, broadcast over rows and columns

    with rasterio.open(in_path) as src:
        if limits.ndim == 3 and limits.shape[0] != src.count:
            raise ValueError(f"{limits.shape[0]} limits for {src.count} bands in {in_path}")
        profile = src.profile.copy()
        profile.update(dtype="uint8", nodata=None)

        with rasterio.open(out_path, "w", **profile) as dst:
            for _, window in src.block_windows(1):
                data = src.read(window=window).astype("float32") - offset
                data = np.clip(data, 0, limits) * (255 / limits)
                dst.write(data.round().astype("uint8"), window=window)

    return out_path
