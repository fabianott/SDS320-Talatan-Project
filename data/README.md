# Data documentation

Two datasets enter this project: Sentinel-2 imagery, which anyone can download
again, and hand labels, which cannot be reproduced from any outside source.
Everything else in `data/` is derived from these two by the notebooks.

---

## 1. Sentinel-2 Level-2A surface reflectance

| Field | Value |
| --- | --- |
| **Dataset name** | Sentinel-2 Level-2A (collection `sentinel-2-l2a`), bands B02 (blue), B03 (green), B04 (red), B08 (near infrared) |
| **Provider** | European Space Agency / Copernicus, hosted by the Microsoft Planetary Computer |
| **URL or access route** | STAC API at `https://planetarycomputer.microsoft.com/api/stac/v1`, queried in `notebooks/01_data_search.ipynb` with `pystac-client` and loaded with `odc-stac`. Asset URLs are signed anonymously with `planetary_computer.sign`; no account or token is needed. |
| **Download date** | 15 and 16 November 2026 |
| **Spatial coverage** | Bounding box 100.132 to 100.665 E, 35.87 to 36.23 N (WGS 84), about 48 by 40 km. Talatan solar park, Gonghe County, Hainan Tibetan Autonomous Prefecture, Qinghai, China |
| **Temporal coverage** | Seven scenes in 2020 (11 March, 15 April, 29 June, 20 August, 7 October, 13 November, 23 December) and one scene per year from 2016 to 2019 and 2021 to 2026 (15 October 2016, 10 September 2017, 28 October 2018, 23 October 2019, 7 September 2021, 17 October 2022, 19 October 2023, 13 October 2024, 18 October 2025, 6 October 2026) |
| **Format** | GeoTIFF, four bands, `uint16`, 10 m ground sampling distance, about 115 MB per scene, 17 scenes, roughly 2 GB in total |
| **Coordinate reference system** | EPSG:32647 (WGS 84 / UTM zone 47N), the native CRS of the Sentinel-2 tile |
| **Licence** | Free, full and open under the Copernicus data policy. Reuse requires the note "Contains modified Copernicus Sentinel data 2016 to 2026". |
| **Processing notes** | See section 4 below. |
| **Can the data be shared publicly?** | Yes, but it is not included in this repository because of its size. `notebooks/01_data_search.ipynb` downloads every scene again with the same query, so the repository stays reproducible without them. |

**Why these scenes.** Cloud and snow cover are not taken from the tile-wide
metadata, which describes a 110 by 110 km tile and says little about the park.
Instead `01_data_search.ipynb` reads the Scene Classification Layer at 60 m and
counts the classes cloud (8, 9), cirrus (10), cloud shadow (3) and snow (11)
inside a 300 m buffer around the labelled park area. A scene is accepted only
below 0.5 % affected pixels over the park and 5 % over the whole box.

The yearly scenes from 2016 to 2026 all come from the window 15 August to 31 October,
so that sun angle and vegetation state stay close to the training data and the
annual areas remain comparable. A scene from January 2026 was discarded during
the project: frost and a low sun made the modules brighter than anything in the
training data.

---

## 2. Hand labels of the photovoltaic area

| Field | Value |
| --- | --- |
| **Dataset name** | `own_labels_<date>.shp`, eight shapefiles |
| **Provider** | Digitised by the author (Fabian Ott) |
| **URL or access route** | In this repository under `data/raw/vectors/`. Not available anywhere else. |
| **Download date** | Created 15 November 2026, not downloaded |
| **Spatial coverage** | The built photovoltaic area inside the bounding box above |
| **Temporal coverage** | Seven dates in 2020 for training, plus 6 October 2026 for testing |
| **Format** | ESRI Shapefile, polygons, 252 to 363 features per date, about 440 KB in total. Each file consists of six parts (`.shp`, `.shx`, `.dbf`, `.prj`, `.cpg`, `.qmd`) which must stay together. |
| **Coordinate reference system** | EPSG:32647, identical to the imagery |
| **Licence** | CC BY 4.0, free to reuse with attribution |
| **Processing notes** | Digitised in QGIS directly on the Sentinel-2 scene of the same date, at a display scale of about 1:10,000, using a four-band display with fixed minimum and maximum values so that brightness stays comparable across dates. The 23 December 2020 scene was labelled first; each earlier date was then derived from the next later one by copying it and removing the blocks that had not yet been built. Access lanes and unbuilt patches inside a block were cut out as holes where they are wider than roughly 30 m. The labels for 6 October 2026 were drawn independently and never used for training. |
| **Can the data be shared publicly?** | Yes, and they are: they are tracked in this repository, because they are the one part of the input that cannot be regenerated. |

A caveat for the labels of 2020: because the earlier dates were derived
backwards from December, construction that was finished between two dates is
captured, but minor changes of a few modules may have been missed. They are
accurate enough for training, and for that reason the 2026 labels, drawn from
scratch, are used for every accuracy figure reported.

---

## 3. Derived data, not tracked

| Folder | Content | Produced by |
| --- | --- | --- |
| `data/processed/labels/` | the same labels as GeoPackages, with invalid self-intersecting geometries repaired | notebook 02 |
| `data/processed/scaled/` | the scenes mapped to 8 bit, see section 4 | notebooks 02, 04, 05 |
| `data/training/images/`, `data/training/labels/` | 1,001 image tiles and 1,001 label masks, 384 by 384 pixels | notebook 02 |

Together roughly 1.5 GB. All of it is deleted and rebuilt on each run of
notebook 02, so none of it is in the repository.

---

## 4. Processing chain

1. **Download.** The four bands are loaded for the bounding box at 10 m and
   written as a GeoTIFF per date, in the native UTM projection. No resampling,
   no mosaicking: single scenes only, so that no artefacts from compositing
   enter the imagery.
2. **Offset correction.** Level-2A products from processing baseline 04.00
   onwards, that is from January 2022, carry an added offset of 1000
   reflectance units. It is subtracted for every scene from 2022 on, so that
   the same pixel value means the same reflectance across all years.
3. **Scaling to 8 bit.** `scripts/preprocessing.py` maps reflectance 0 to 4000
   linearly onto 0 to 255 and clips above it. The cut-off of 4000 lies above
   the 99th percentile of all scenes, so almost nothing saturates. This step is
   not cosmetic: `geoai` divides input tiles by 255 and clips its brightness
   augmentations to [0, 1], which silently destroys most tiles when the input
   is 16-bit.
4. **Geometry repair.** Hand-drawn polygons can self-intersect, which makes the
   tiling abort. Notebook 02 runs `make_valid` and `explode` and writes the
   repaired geometries as GeoPackages, leaving the original shapefiles
   untouched.
5. **Tiling.** 384 by 384 pixels, no overlap, giving 143 tiles per scene and
   1,001 in total, split 80/20 into training and validation.
