"""Preparation of Sentinel-2 scenes for the segmentation model."""

import numpy as np
import rasterio

MAX_REFLECTANCE = 4000   # reflectance mapped to 255; above the 99th percentile of all scenes
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
    model is applied to, so scenes of different years stay comparable.

    Args:
        in_path: Sentinel-2 GeoTIFF holding reflectance values.
        out_path: Path of the 8 bit output file.
        offset: Value subtracted before scaling. Use BASELINE_OFFSET for scenes
            acquired from January 2022 onwards, 0 for earlier ones.
        max_reflectance: Reflectance that becomes 255. Higher values are clipped.

    Returns:
        Path to the written file.
    """
    with rasterio.open(in_path) as src:
        profile = src.profile.copy()
        profile.update(dtype="uint8", nodata=None)

        with rasterio.open(out_path, "w", **profile) as dst:
            for _, window in src.block_windows(1):
                data = src.read(window=window).astype("float32") - offset
                data = np.clip(data, 0, max_reflectance) * (255 / max_reflectance)
                dst.write(data.round().astype("uint8"), window=window)

    return out_path
