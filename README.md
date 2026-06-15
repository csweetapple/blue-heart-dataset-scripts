# Example scripts for the the Blue Heart dataset publication

This repository contains a set of example scripts for accessing, viewing, processing and analysing the Blue Heart dataset (available separately from https://doi.org/10.5281/zenodo.20699635).

## Environment setup

Code has been developed and tested on Python 3.12. `uv` is used for dependency management and reproducibility:
1. Install uv
```
pip install uv
```
2. Create environment
```
uv venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
```
3. Install dependencies
```
uv sync
```
4. Run Jupyter lab for notebooks
```
uv run jupyter lab
```

## Scripts

### `blue_heart_data_handling.py`

Includes a function to access raw and quality controlled data from all or specified gauges.

### `1_feature_maps.ipynb`

Includes creation of maps showing:
* Catchment outline.
* Fluvial / overland system; and stormwater, combined and foul sewer system.
* Catchment elevation.
* Runoff coefficient and horton model infiltration parameters.
* Distribution of gauges in the study area (including identification of different gauge types).

### `2_catchment_stats.ipynb`

Provides calculation of catchment statistics, including:
* Catchment area.
* Catchment elevation statistics.
* Watercourse length.

### `3_gauge_raw_data_completeness.ipynb`

Analyses the coverage and completeness of the raw data at a gauge and catchment level. Includes:
* Plots showing data coverage and gaps for every parameter and every gauge.
* Summary of monitoring duration and complete data duration at every gauge.
* Plot showing distribution of monitoring durations and dataset completeness across all gauges.
* Summary plot showing the total number of gauges with data available each day.
* Identification of minimum/median/maximum gauge-level monitoring periods and down times.


### `4_gauge_raw_data_quality_checks.ipynb`

Implementation of simple quality control checks on raw data, including:
* Definition and application of range checks.
* Definition and application of rate-of-change checks.
* Definition and application of persistence checks.
* Generation of quality control codes for every data point..

### `5_gauge_raw_data_quality_analysis.ipynb`

Analysis of data quality, based on output of quality control checks (results of which are included in the Blue Heart dataset). Includes:
* Calculation of the proportion of each parameter's data for each gauge categorised with each quality code.
* Box plots showing the proportion of data from each gauge with a quality flag of 1 (split by gauge type)
* Catchment-level summary of the proportion of datapoints with each quality label.

### `6_timeseries_plots.ipynb`

Generation of example timeseries plots and general statistics related to the timeseries, including:
* Plot of water levels recorded at a subset of the highway gullies.
* Calculation of minimum, maximum and percentile water levels and ranges at individual highway gullies.
* Plot of water levels recorded at all boreholes.
* Calculation of water level ranges at individual boreholes.
* Plot of water levels recorded at a subset of the sewer level gauges.
* Plot of water levels recorded at a subset of the fluvial gauges.
* Plot of air temperatures recorded at a subset of the gauges.
* Calculation of air temperature percentile ranges at individual gauges.
* Calculation of intra class correlation coefficient for air temperatures recorded at different gauges and inter-gauge standard deviation.
* Plot of water temperatures recorded at a subset of the gauges.
* Calculation of water temperature percentile ranges at individual fluvial gauges.
* Calculation of intra class correlation coefficient for water temperatures recorded at different fluvial gauges and inter-gauge standard deviation.
* Plot of daily rainfall depths recorded at all rain gauges (each on a separate subplot, with data gaps identified)
* Plot of water levels recorded at all gauges (of all types) within a specified radius of a defined point, and rainfall from the nearest gauge.

## Acknowledgements

This research was completed for the ‘Blue Heart’ project and funded by Defra as part of the £200 million Flood and Coastal Innovation Programmes which is managed by the Environment Agency. The programmes will drive innovation in flood and coastal resilience and adaptation to a changing climate.
The authors gratefully acknowledge Southern Water for providing access to their sewer monitoring data and for granting permission to share the dataset publicly.