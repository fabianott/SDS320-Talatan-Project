# Talatan Solar Park: Mapping and Growth from Sentinel-2, 2016 to 2026

Semester project for SDS320 (Spatial Data Science), University of Zurich. Author: Fabian Ott.

## Short summary

The Talatan solar park in Qinghai, China, is one of the largest photovoltaic (PV) installations in the world. This project maps it from Sentinel-2 imagery with semantic segmentation. A U-Net trained on seven hand-labelled scenes from 2020 is applied unchanged to one scene per year from 2016 to 2026. On a hand-labelled test scene from 2026 it reaches an IoU of 0.85 overall and 0.79 on the plants built after 2020, which the model never saw. A simple spectral index serves as a baseline (IoU 0.36).

## Research question

How much did the PV area of the Talatan solar park grow between 2016 and 2026, and how reliably can it be mapped from Sentinel-2 with a segmentation model trained on a single year?

## Data sources

- **Sentinel-2 Level-2A**, bands B02, B03, B04, B08 at 10 m, from the Microsoft Planetary Computer (STAC API). Not stored in the repository; notebook 01 downloads it.
- **Hand labels** of the PV area, digitised in QGIS: seven dates in 2020 for training, one date in 2026 for testing. Stored in `data/raw/vectors/`.

Details on coverage, CRS, licences and processing are in [`data/README.md`](data/README.md).

## Methods

1. Scene selection with cloud and snow screening over the park (Scene Classification Layer) for the training scenes; for the yearly scenes the clearest day per season, with four days replaced by hand.
2. Offset correction for processing baseline 04.00 and scaling of the reflectance to 8 bit.
3. Tiling into 384 × 384 px tiles and training of a U-Net with a ResNet34 encoder (`geoai`).
4. Prediction on the 2026 test scene and evaluation with IoU, F1, precision and recall, for the whole scene and separately for plants built before and after 2020.
5. Prediction on one scene per year from 2016 to 2026 and calculation of the PV area.
6. Comparison with a threshold-based spectral index (blue / NIR).

## Repository structure

```
├── README.md
├── environment.yml               Python environment
├── run_all.sh                    runs all notebooks in order
├── data/
│   ├── README.md                 data documentation
│   └── raw/vectors/              hand labels (other data folders are not tracked)
├── notebooks/
│   ├── 01_data_search.ipynb          scene search and download
│   ├── 02_labels_and_tiles.ipynb     label repair, scaling, tiling
│   ├── 03_train_model.ipynb          U-Net training
│   ├── 04_predict_and_evaluate.ipynb prediction and evaluation 2026
│   ├── 05_time_series.ipynb          time series 2016 to 2026
│   └── 06_index_baseline.ipynb       spectral index baseline
├── scripts/
│   ├── scene_search.py           STAC search and download
│   ├── preprocessing.py          scaling to 8 bit
│   └── spatial_subsets.py        course helper, not used
├── results/
│   ├── figures/                  maps and figures
│   └── evaluation/               metrics as CSV
└── report/
```

## How to run

```bash
git clone https://github.com/fabianott/SDS320-Talatan-Project.git
cd SDS320-Talatan-Project
conda env create -f environment.yml
conda activate sds320-talatan
```

Then run the notebooks 01 to 06 in order, or all at once with `./run_all.sh`. Notebook 04 must run before 06. Training in notebook 03 takes about one hour on a laptop CPU.

## Results

**Accuracy on the independent 2026 test scene**

| | U-Net | Index baseline |
| --- | --- | --- |
| IoU | 0.85 | 0.36 |
| F1 | 0.92 | 0.53 |
| Mapped area | 341.2 km² | 320.3 km² |
| Labelled area | 340.9 km² | 340.9 km² |

The test scene is independent in time but not fully in space: 42 % of its labelled PV area lies on plants that already existed in 2020 and were seen during training.

| Part of the test scene | Share of labelled area | IoU | F1 |
| --- | --- | --- | --- |
| Plants built by 2020 (seen in training) | 42 % | 0.95 | 0.98 |
| Plants built after 2020 (unseen) | 58 % | 0.79 | 0.88 |
| Whole scene | 100 % | 0.85 | 0.92 |

The test uses the scene of 2026-10-06, the date of the hand labels. The time series uses 2026-10-03 for 2026, hence the slightly different area (346.0 km²).

**PV area per year**

| Year | Scene | PV area (km²) |
| --- | --- | --- |
| 2016 | 2016-10-18 | 66.0 |
| 2017 | 2017-09-10 | 72.3 |
| 2018 | 2018-10-28 | 92.3 |
| 2019 | 2019-10-23 | 99.2 |
| 2020 | 2020-08-20 | 133.1 |
| 2021 | 2021-09-07 | 168.0 |
| 2022 | 2022-09-29 | 173.3 |
| 2023 | 2023-10-19 | 249.5 |
| 2024 | 2024-10-13 | 300.4 |
| 2025 | 2025-10-13 | 340.9 |
| 2026 | 2026-10-03 | 346.0 |

The PV area grew more than fivefold, from about 66 km² in 2016 to about 346 km² in 2026. Growth almost paused in 2021/22 and was strongest in 2023. For 2016, 2022, 2025 and 2026 the automatically chosen scene was replaced by another date of the same season (see `data/README.md`): on the automatic picks the park was less clear or the model mapped less area than in the year before, which a growing park cannot have.

## Limitations

- The model was trained on one park and one year only; transfer to other regions is untested.
- Year-to-year differences of a few km² are not meaningful; only the overall trend is.
- Training and validation tiles come from the same locations on different dates, so the validation IoU (0.96) is optimistic. On the 2026 test scene the model reaches 0.95 on plants seen in training but 0.79 on plants built after 2020; the second value is the realistic measure for new installations.
- The areas after 2020 rest mostly on plants the model never saw and are therefore less certain than the earlier years.
- For 2016, 2022, 2025 and 2026 the scene was chosen by hand after looking at the result, which favours larger areas in those years.
- The hand labels were drawn on the same 10 m imagery and are themselves uncertain at block edges.

## AI use

Claude (Anthropic) was used as a coding assistant for structuring and debugging the code and for writing documentation. Study design, scene selection, all labels, model configuration and the interpretation of the results are the author's own.

## Licence and citation

Code: MIT licence. Hand labels: CC BY 4.0. Sentinel-2 data: Copernicus data policy, "Contains modified Copernicus Sentinel data 2016 to 2026".

> Ott, F. (2026). Mapping the growth of the Talatan solar park from Sentinel-2 imagery using semantic segmentation. SDS320 semester project, University of Zurich. https://github.com/fabianott/SDS320-Talatan-Project
