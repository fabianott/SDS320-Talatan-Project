# Talatan Solar Park: Mapping and Growth from Sentinel-2, 2016 to 2026

Semester project for SDS320 (Spatial Data Science), University of Zurich. Author: Fabian Ott.

## Short summary

The Talatan solar park in Qinghai, China, is one of the largest photovoltaic (PV) installations in the world. This project maps it from Sentinel-2 imagery with semantic segmentation. A U-Net trained on seven hand-labelled scenes from 2020, with six bands including the two shortwave infrared bands, is applied unchanged to one scene per year from 2016 to 2026. On a hand-labelled test scene from 2026 it reaches an IoU of 0.90 overall and 0.85 on the plants built after 2020, which the model never saw. Applied unchanged to a second park, Golmud (Qinghai), it reaches an IoU of 0.85. Four further parks in India, Germany and Spain are mapped for a visual check.

## Research question

How much did the PV area of the Talatan solar park grow between 2016 and 2026, and how reliably can it be mapped from Sentinel-2 with a segmentation model trained on a single year?

## Data sources

- **Sentinel-2 Level-2A**, bands B02, B03, B04, B08 (10 m) and B11, B12 (20 m, resampled to 10 m), from the Microsoft Planetary Computer (STAC API). Not stored in the repository; the notebooks download it.
- **Hand labels** of the PV area, digitised in QGIS: seven dates in 2020 for training, one date in 2026 for testing, and one date in 2026 for the Golmud solar park (transfer test). Stored in `data/raw/vectors/`.

Details on coverage, CRS, licences and processing are in [`data/README.md`](data/README.md).

## Methods

1. Scene selection with cloud and snow screening over the park (Scene Classification Layer) for the training scenes; for the yearly scenes the clearest day per season, with four days replaced by hand.
2. Offset correction for processing baseline 04.00 and scaling of the reflectance to 8 bit, with one upper limit per band.
3. Tiling into 384 × 384 px tiles and training of a U-Net with a ResNet34 encoder (`geoai`).
4. Prediction on the 2026 test scene and evaluation with IoU, F1, precision and recall, for the whole scene and separately for plants built before and after 2020.
5. Prediction on one scene per year from 2016 to 2026 and calculation of the PV area.
6. Transfer test: the unchanged model applied to the Golmud solar park and evaluated against hand labels.
7. Application to four further parks (Khavda, India; Witznitz, Germany; Francisco Pizarro and Núñez de Balboa, Spain), checked visually.

**Why six bands.** A first version of the model used only blue, green, red and near infrared. It mapped Talatan and Golmud well but missed large parts of the Spanish tracker plants, where modules with wide row spacing stand on bright, dry soil. In the shortwave infrared, modules are dark and dry soil is bright. With the same training data, the six-band model was trained twice:

| Test (IoU) | 4 bands | 6 bands, first run | 6 bands, final run |
| --- | --- | --- | --- |
| Talatan 2026, whole scene | 0.85 | 0.92 | 0.90 |
| Talatan 2026, plants built after 2020 | 0.79 | 0.88 | 0.85 |
| Golmud 2026 | 0.90 | 0.91 | 0.85 |

On Talatan, the SWIR bands improve the model clearly and in both runs, most of all on plants it never saw. In Spain, the six-band model found most of the tracker fields the four-band model had missed. On Golmud there is no clear gain: the two six-band runs differ by 0.06, which is about as much as the effect of the extra bands itself. The final run misses several plants with bright modules that the four-band model found. The project uses only the six-band model, as it is better where it matters most for the research question, the new plants in Talatan. The four-band version is kept in the git tag `v1-4band`; the first six-band run was not kept.

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
│   ├── 06_golmud_transfer.ipynb      transfer test on the Golmud solar park
│   └── 07_transfer_sites.ipynb       four further parks, visual check
├── scripts/
│   ├── scene_search.py           STAC search and download
│   ├── preprocessing.py          scaling to 8 bit, one limit per band
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

Then run the notebooks 01 to 07 in order, or all at once with `./run_all.sh`. Notebook 04 must run before 06, which compares its result with the Talatan metrics. Training in notebook 03 takes about one hour on a laptop CPU.

## Results

**Accuracy on the 2026 test scene**

| | U-Net |
| --- | --- |
| IoU | 0.90 |
| F1 | 0.95 |
| Precision | 0.92 |
| Recall | 0.98 |
| Mapped area | 366.8 km² |
| Labelled area | 340.9 km² |

The model finds almost all labelled PV. Its errors are mainly false positives along the narrow tracks between neighbouring blocks, which the labels leave out and the model at 10 m merges with the blocks. It therefore maps about 8 % more area than labelled.

The test scene is independent in time but not fully in space: 42 % of its labelled PV area lies on plants that already existed in 2020 and were seen during training.

| Part of the test scene | Share of labelled area | IoU | F1 |
| --- | --- | --- | --- |
| Plants built by 2020 (seen in training) | 42 % | 0.98 | 0.99 |
| Plants built after 2020 (unseen) | 58 % | 0.85 | 0.92 |
| Whole scene | 100 % | 0.90 | 0.95 |

The test uses the scene of 2026-10-06, the date of the hand labels. The time series uses 2026-10-03 for 2026, hence the slightly different area.

**Transfer test: Golmud solar park, 2026-11-06**

The model trained on Talatan was applied without retraining to the Golmud solar park, about 450 km west of Talatan, and compared with hand labels of the same scene.

| Study area | IoU | F1 | Precision | Recall | Mapped / labelled area |
| --- | --- | --- | --- | --- | --- |
| Labels plus 1.5 km margin | 0.85 | 0.92 | 0.93 | 0.91 | 62.7 / 64.7 km² |
| Labels plus 10 km margin | 0.84 | 0.91 | 0.93 | 0.90 | 62.8 / 64.7 km² |

There are few false positives, even in the larger area. Most of the error is missed area on older plants with bright modules, which hardly occur in the training data.

**Further parks (no labels, visual check)**

| Park | Scene | Mapped PV area | Area given by the operator |
| --- | --- | --- | --- |
| Khavda, India | 2026-10-04 | 223.6 km² | – |
| Energiepark Witznitz, Germany | 2026-08-15 | 4.1 km² | 3 km² of modules |
| Francisco Pizarro, Spain | 2026-10-14 | 21.1 km² | 13 km² plant site |
| Núñez de Balboa, Spain | 2026-10-27 | 8.6 km² | 10 km² plant site |

The modules are found in all four parks, including the Spanish tracker plants. At Witznitz and Francisco Pizarro the mapped area exceeds the area given by the operator: the model merges neighbouring module fields and the space between them, as on Talatan.

**PV area per year**

| Year | Scene | PV area (km²) |
| --- | --- | --- |
| 2016 | 2016-10-18 | 69.0 |
| 2017 | 2017-09-10 | 73.5 |
| 2018 | 2018-10-28 | 96.4 |
| 2019 | 2019-10-23 | 101.3 |
| 2020 | 2020-08-20 | 133.7 |
| 2021 | 2021-09-07 | 167.9 |
| 2022 | 2022-09-29 | 174.7 |
| 2023 | 2023-10-19 | 272.0 |
| 2024 | 2024-10-13 | 325.8 |
| 2025 | 2025-10-13 | 374.4 |
| 2026 | 2026-10-03 | 373.5 |

The mapped PV area grew more than fivefold, from about 69 km² in 2016 to about 374 km² in 2026. Growth almost paused in 2021/22 and was strongest in 2023. Between 2025 and 2026 the mapped area hardly changed. In 2026 the model maps about 33 km² more than the hand labels, mostly the tracks between blocks, so the absolute areas of the later years are likely about 8 to 10 % too high; the trend is not affected. For 2016, 2022, 2025 and 2026 the automatically chosen scene was replaced by another date of the same season (see `data/README.md`).

## Limitations

- The model was trained on one park and one year only. Transfer was measured on one other park (Golmud), on one date and in a similar setting on the Tibetan Plateau; the four further parks were only checked visually, without labels.
- Year-to-year differences of a few km² are not meaningful; only the overall trend is.
- Results vary between training runs. Two runs of the six-band model with identical data and settings reached an IoU of 0.91 and 0.85 on Golmud, mainly because bright modules ended up on different sides of the 0.5 threshold. All figures in this README come from one run.
- The model merges neighbouring blocks with the tracks between them, so it maps about 8 % more area than the hand labels on Talatan and more than the operators' figures at Witznitz and Francisco Pizarro.
- Bright modules, which are rare in the training data, are partly missed (Golmud).
- Training and validation tiles come from the same locations on different dates, so the validation IoU (0.97) is optimistic. On the 2026 test scene, the score on plants built after 2020 is the realistic measure for new installations.
- The areas after 2020 rest mostly on plants the model never saw and are therefore less certain than the earlier years.
- For 2016, 2022, 2025 and 2026 the scene was chosen by hand; for 2022, 2025 and 2026 after looking at the result of the earlier four-band model, which favours larger areas in those years.
- The hand labels were drawn on the same 10 m imagery and are themselves uncertain at block edges.

## AI use

Claude (Anthropic) was used as a coding assistant for structuring and debugging the code and for writing documentation. Study design, scene selection, all labels, model configuration and the interpretation of the results are the author's own.

## Licence and citation

Code: MIT licence. Hand labels: CC BY 4.0. Sentinel-2 data: Copernicus data policy, "Contains modified Copernicus Sentinel data 2016 to 2026".

> Ott, F. (2026). Mapping the growth of the Talatan solar park from Sentinel-2 imagery using semantic segmentation. SDS320 semester project, University of Zurich. https://github.com/fabianott/SDS320-Talatan-Project
