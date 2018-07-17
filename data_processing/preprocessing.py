#preprocessing data


import pandas as pd
import numpy as np

def mad(arr):
    '''
    Computes the Median Absolute Deviation of the provided numerical array.
    https://en.wikipedia.org/wiki/Median_absolute_deviation
    '''
    return np.median(np.abs(arr - np.median(arr)))

def mad_outliers(series, sensitivity=12, delta=1):
    '''
    Use the MAD to select outliers in the timeseries data.
    For a window of +- delta hours, points that are more than sensitivity*MAD(window)
    Will be marked as outliers.
    Returns a list of indices in the series that have been identified as outliers,
    For either removal or interpolation.
    '''
    #creating a Pandas timedelta for proper indexing
    timedelta = pd.Timedelta("{} hour".format(delta))

    outliers = []

    series_start = pd.to_datetime(series.index[0])
    series_end = pd.to_datetime(series.index[-1])

    for i in range(len(series)):
        #selecting date range, accounting for beginning and end of series
        #NOTE: this means that window size will vary at the beginning and end of the series
        window_start = max(pd.to_datetime(series.index[i]) - timedelta, series_start)
        window_end = min(pd.to_datetime(series.index[i]) + timedelta, series_end)

        window = series.loc[str(window_start):str(window_end)].values
        dev = mad(window)
        med = np.median(window)
#         display(dev)
#         display(med)
#         display(window)
#         display(series[series.index[i]])

        #marking as an outlier if farther away from median than sensitivity*dev
        if np.abs(series[series.index[i]]- med) > sensitivity*dev:
            outliers.append(series.index[i])

    print ("{} outliers identified out of {} total points".format(len(outliers), len(series)))

    return outliers


def interpolate_series(series, outliers):
    '''
    Helper function wrapping the built-in Pandas interpolation function.
    Using 4th-order piecewise polynomial interpolation.
    '''
    #replacing outliers with NaNs

    #avoid editing in place
    series = series.copy()
    series[outliers] = np.nan


    #converting index explicitly to datetime
    series.index = pd.to_datetime(series.index)
    series = series.interpolate(method="piecewise_polynomial", limit_direction="both" , order=4)

    return series


def preprocess_rms(rms):
    '''
    Runs preprocessing on RMS DataFrame.
    Returns a DataFrame with outliers removed, and index converted to explict DateTime type.
    '''

    cols = rms.columns.values

    interpolated = {}

    for col in cols:
        col_series = rms[col]
        outliers = mad_outliers(col_series)

        interp = interpolate_series(col_series, outliers)

        interpolated[col] = interp

    return pd.DataFrame(interpolated)


def add_power_feature(rms):
    '''
    Adds the power (current * voltage) feature to the DataFrame.
    '''
    rms['power'] = rms['motor_current']*rms['motor_voltage']


def add_torque(rms):
    '''
    Computes the torque currently exerted by the motor.
    '''
    rms['torque'] = rms['power']/rms['rpm']

def add_temp_diff(rms):
    '''
    Adds a feature equal to the difference between the motor and inlet temperature.
    '''

    rms['temp_diff'] = rms['motor_temp'] - rms['inlet_temp']

def add_alarms(rms, alarms):
    '''
    Incorporates alarm system data into the DataFrame.
    '''

    #Each data point can be modeled as a sample taken in a 10-minute interval, so explicit
    #discretization or re-sampling would be unproductive and add noise.

    #To incorporate warnings, marking whether or not a warning occured between each observation
    #and the following observation.

    warning_occured = np.zeros(len(rms))
    error_occured = np.zeros(len(rms))

    alarms.index = pd.to_datetime(alarms.index)

    # print(alarms.index)
    # print(rms.index)

    #not sure why some of them weren't sorted.
    alarms = alarms.sort_index()

    for i, index in enumerate(rms.index[:-2]):
        next_index = rms.index[i + 1]
        # print(index, next_index)
        alarms_in_range = alarms.loc[index:next_index]
        if len(alarms_in_range) > 0:
            if "warning" in alarms_in_range.values:
                warning_occured[i] = 1
            if "error" in alarms_in_range.values:
                error_occured[i] = 1

    rms['error_occured'] = error_occured
    rms['warning_occured'] = warning_occured

def preprocess_all(data_dict):
    '''
    Performs preprocessing on all loaded elements in a data dictionary.
    '''

    results = {}

    for item in data_dict.keys():
        print("preprocessing {}".format(item))
        rms = preprocess_rms(data_dict[item]['rms'])
        add_power_feature(rms)
        add_temp_diff(rms)
        add_alarms(rms, data_dict[item]['alarms'])
        results[item] = rms
