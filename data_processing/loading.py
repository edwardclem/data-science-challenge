#helper functions for loading data

import pandas as pd
import os

def load_rms(filename):
    return pd.read_csv(filename, index_col="timestamp")
def load_alarms(filename):
    #loading alarms rather than description.
    return pd.read_csv(filename, header=None, names=["timestamp", "message"], index_col="timestamp")

def load_folder(folder):
    '''
    Loads all alarm and RMS files from a folder.
    '''

    #dict of dicts, each element containing an 'alarms' and 'rms' key/val pair.
    files = {}

    for f in os.listdir(folder):

        #extracting unit name info
        split = f.split("_")

        unit_name = split[0]

        record_type = split[1].replace(".csv", "")

        if unit_name not in files.keys():
            files[unit_name] = {}

        fullpath = "{}/{}".format(folder, f)

        if record_type == "alarms":
            files[unit_name][record_type] = load_alarms(fullpath)
        elif record_type == "rms":
            files[unit_name][record_type] = load_rms(fullpath)


    return files

if __name__=="__main__":
    folder = "../data/test"

    files = load_folder(folder)

    print(files)
