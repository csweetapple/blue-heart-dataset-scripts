from enum import Enum, unique
import pandas as pd
from typing import List
import numpy as np


# Gauge types
@unique
class GaugeTypes(Enum):
    Borehole = 'Borehole'
    Fluvial = 'Fluvial'
    HighwayGully = 'Highway gully'
    Rain = 'Rain'
    Sewer = 'Sewer'


# Gauge parameters
@unique
class GaugeParameters(Enum):
    AirTemperature = 'Air Temperature [°C]'
    DepthToWater = 'Depth To Water [m]'
    RainfallDepth = 'Rainfall Depth [mm]'
    SewerLevel = 'Sewer Level [mm]'
    SignalToNoiseRatio = 'Signal-to-noise ratio [dB]'
    WaterDepth = 'Water Depth [m]'
    WaterLevelMM = 'Water Level [mm]'
    WaterLevelM = 'Water Level [mAOD]'
    WaterTemperature = 'Water Temperature [°C]'


# Quality control flags
@unique
class QCFlags(Enum):
    Good = 1
    Suspect = 2
    Bad = 3


# Quality control labels
@unique
class QCLabels(Enum):
    NA = ''
    AboveRange = 'A'
    BelowRange = 'B'
    LowSNR = 'C'
    HighRateOfChange = 'D'
    PersistentlyHigh = 'E'


# Data type options
@unique
class DataTypeOptions(Enum):
    Raw = 'Raw',    # Raw data only
    RawWithQualityCodes = 'RawWithQualityCodes'  # Raw data and quality codes
    Quality1 = 'Quality1'   # Only data with quality code '1'


def get_gauge_data(
        data_type_option: DataTypeOptions,
        filter_gauge_names: List[str] | None = None,
        filter_gauge_types: List[GaugeTypes] | None = None,
        filter_gauge_parameters: List[GaugeParameters] | None = None,
        date_start: pd.Timestamp | None = None,
        date_end: pd.Timestamp | None = None,
        path_root_folder: str = '..',
):

    """Load data for gauge(s) from .csv file(s)

    Parameters:
        data_type_option (DataTypeOptions): Data type to return (raw only, raw
            with quality flags, or only data with quality flag '1')
        filter_gauge_names (List[str] | None): Only return gauge names that
            appear in this list, if provided.
        filter_gauge_types (List[GaugeTypes] | None): Only return gauge names
            that appear in this list, if provided.
        filter_gauge_parameters (List[GaugeParameters] | None): Only return
            gauge parameters that appear in this list, if provided.
        path_root_folder (str): Path for root folder containing gauge data
            index csv and data folders
        date_start (pd.Timestamp | None): Only retrieve data from this date
            onwards
        date_end (pd.Timestamp | None): Only retrieve data up until this date
        path_index_telemetry_data (str): Path for gauge data index.

    Returns:
        dict: Dictionary containing separate dataframes for each gauge
        location and parameter

    """

    # Load gauge index
    path_index_telemetry_data = f'{path_root_folder}/index_telemetry_data.csv'
    df_index = _load_gauge_index(path_index_telemetry_data)

    # Filter gauges
    df_index_filtered = _filter_gauge_index(
        df_index,
        filter_gauge_names,
        filter_gauge_types,
        filter_gauge_parameters
    )

    # Create dictionary to store gauge data (key = gauge name)
    gauge_dfs = {}

    # If no parameter filter defined, include all parameters present
    if filter_gauge_parameters is None:
        filter_gauge_parameters = list(GaugeParameters)

    # Load data from each gauge
    for index, gauge_row in df_index_filtered.iterrows():

        # Initialise dictionary for gauge
        gauge_name = gauge_row['locationName']
        gauge_dfs[gauge_name] = {}

        # Load raw data
        path_data = f'{path_root_folder}/{gauge_row['dataPath']}'
        df_gauge = pd.read_csv(path_data)

        # Convert to timezone-aware datetime index
        df_gauge = _convert_to_tz_aware_index(df_gauge)

        # Add quality data if required
        if data_type_option != DataTypeOptions.Raw:

            # Load quality data and convert to timezone-aware datetime index
            path_quality_flags = (
                f'{path_root_folder}/{gauge_row['dataQualityFlagsPath']}'
                )
            df_gauge_quality = pd.read_csv(path_quality_flags, dtype=str)
            df_gauge_quality = _convert_to_tz_aware_index(df_gauge_quality)

            # Combine with data
            df_gauge = pd.concat(
                [df_gauge, df_gauge_quality], axis=1, sort=True, join='outer')

        # Extract data associated with each required parameters
        for parameter in filter_gauge_parameters:
            parameter_columns = df_gauge.columns[
                df_gauge.columns.str.contains(parameter.value, regex=False)]
            if len(parameter_columns) == 0:
                # If no data for specified parameter
                continue
            df_parameter = df_gauge[parameter_columns].copy()

            # Filter data with quality flag '1' if required
            if data_type_option == DataTypeOptions.Quality1:
                quality_column = df_parameter.columns[
                    df_parameter.columns.str.contains('Quality -')][0]
                df_parameter = df_parameter[
                    df_parameter[quality_column] == '1']
                df_parameter.drop(columns=[quality_column], inplace=True)

            # If using quality checked data, identify timesteps and insert
            # NaNs in gaps
            if data_type_option != DataTypeOptions.Raw:

                # Identify all intentional timesteps
                timesteps_intentional = get_intentional_timesteps(df_parameter)

                # Identify the maximum intentional timestep
                timesteps_intentional_max = (
                    get_max_intentional_timestep_minutes(timesteps_intentional)
                    )

                # Insert NaNs in gaps
                df_parameter.sort_index(inplace=True)
                df_parameter.reset_index(inplace=True)
                dt = df_parameter['timestamp'].diff()
                data_column = df_parameter.columns[1]
                df_parameter.loc[dt > pd.Timedelta(
                    minutes=timesteps_intentional_max), data_column] = np.nan
                df_parameter.set_index('timestamp', inplace=True)

            # Filter by start and end date, if specified
            filter_date_start = (
                df_parameter.index.min() if date_start is None else date_start
                )
            filter_date_end = (
                df_parameter.index.max() if date_end is None else date_end
                )
            df_parameter = df_parameter[
                (df_parameter.index >= filter_date_start) &
                (df_parameter.index <= filter_date_end)
                ]

            # Store parameter data in dictionary
            gauge_dfs[gauge_name][parameter] = df_parameter
    return gauge_dfs


def get_intentional_timesteps(
        df: pd.DataFrame,
        min_occurrences: float = 100
):

    """
    Identify different timesteps present in the dataframe index and return
    timesteps that occur at least a specified minimum number of times

    Parameters:
        df (pd.DataFrame): Dataframe containing timeseries data with datetime
            index
        min_occurrences (float): Minimum number of occurrences required for a
            timestep to be considered intentional

    Returns:
        pd.Series: Series containing intentional timesteps identified and
            their occurrence counts

    """

    attempts = 0
    timesteps_counts = df.reset_index(
        names='timestamp')['timestamp'].diff().value_counts()
    timesteps_intentional = timesteps_counts[
        timesteps_counts.astype(float) > min_occurrences]
    while (timesteps_intentional.shape[0]) == 0 and (attempts < 50):
        attempts += 1
        while min_occurrences * 0.9 > 1:
            min_occurrences *= 0.9
            timesteps_intentional = timesteps_counts[
                timesteps_counts.astype(float) > min_occurrences]
    return timesteps_intentional


def get_max_intentional_timestep_minutes(
        timesteps_intentional: pd.Series,
        default_minutes: float = 60
        ):

    """Identify maximum intentional timestep

    Parameters:
        timesteps_intentional (pd.Series): timesteps_intentional retrieved
            from get_intentional_timesteps
        default_minutes (float): Assumed timestep if no timesteps identified
            from data

    Returns:
        float: Timestep in minutes

    """

    if timesteps_intentional.shape[0] > 0:
        return timesteps_intentional.index.max().total_seconds()/60
    return default_minutes


def get_modal_intentional_timestep_minutes(
        timesteps_intentional: pd.Series,
        ):

    """Identify typical (most common) intentional timestep

    Parameters:
        timesteps_intentional (pd.Series): Intentional timesteps, as retrieved
            from get_intentional_timesteps

    Returns:
        float: Timestep in minutes

    """

    if timesteps_intentional.shape[0] > 0:
        return (
            timesteps_intentional
            .sort_values(ascending=False)
            .index[0].total_seconds()/60
            )
    return np.nan


def _convert_to_tz_aware_index(
        df: pd.DataFrame,
        datetime_column: str = 'timestamp'):

    """Convert datetime column to timezone-aware times and set as index

    Parameters:
        df (pd.DataFrame): Dataframe containing timeseries data with a column
            containing timestamps
        datetime_column (str): Name of column containing datetime timestamps

    Returns:
        pd.DataFrame: Dataframe with a timezone-aware datetime index

    """

    df[datetime_column] = pd.to_datetime(df[datetime_column])
    is_tz_aware_data = df[datetime_column].dt.tz is not None
    if not is_tz_aware_data:
        df[datetime_column] = df[datetime_column].dt.tz_localize('UTC')
    df.set_index('timestamp', inplace=True)
    return df


def _filter_gauge_index(
        df_index: pd.DataFrame,
        filter_gauge_names: List[str] | None,
        filter_gauge_types: List[GaugeTypes] | None,
        filter_gauge_parameters: List[GaugeParameters] | None,
):

    """Filter list of gauges, based on specified gauge name, type and
    parameter filters

    Parameters:
        df_index (pd.DataFrame): Gauge data index
        filter_gauge_names (List[str] | None): Only return gauge names that
            appear in this list, if provided.
        filter_gauge_types (List[GaugeTypes] | None): Only return gauge types
            that appear in this list, if provided.
        filter_gauge_parameters (List[GaugeParameters] | None): Only return
            gauge parameters that appear in this list, if provided.

    Returns:
        pd.DataFrame: Filtered gauge data index

    """

    gauge_mask = pd.Series(True, index=df_index.index)

    # Filter gauge names
    if filter_gauge_names is not None:
        gauge_mask &= df_index['locationName'].isin(filter_gauge_names)

    # Filter gauge types
    if filter_gauge_types is not None:
        gauge_mask &= df_index['gaugeType'].isin(
            [filter_gauge_type.value for
             filter_gauge_type in filter_gauge_types])

    # Filter gauge parameters
    if filter_gauge_parameters is not None:

        parameter_lists = (
            df_index['gaugeParameters'].str.split(r';\s*', regex=True)
            )
        # Strip units from parameter and find
        gauge_mask &= parameter_lists.apply(
            lambda params: any(
                p in params for p in
                [filter_gauge_parameter.value.split(" [", 1)[0] for
                 filter_gauge_parameter in filter_gauge_parameters]
                )
        )

    return df_index[gauge_mask]


def _load_gauge_index(
        path_index_telemetry_data: str
):

    """Load gauge data index]

    Parameters:
        path_index_telemetry_data (str): Path of index .csv file

    Returns:
        pd.DataFrame: Index of available gauges

    """

    try:
        return pd.read_csv(path_index_telemetry_data)
    except FileNotFoundError:
        raise Exception(
            f'Error loading gauge data index from {path_index_telemetry_data}'
            )
