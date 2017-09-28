"""
Utility functions for VoiceSampleAnalysis
"""
from datetime import date, datetime
import numpy as np
import os
import pandas as pd
import re
from scipy import stats
import shlex
import subprocess
import sys

def date_from_int(int_date):
    """
    Function to turn an int into a date
    
    Parameter
    ---------
    int_date : int
        YYYYMMDD
    
    Returns
    -------
    date_date : date
    """
    try:
        return(date(int(str(int_date)[:4]), int(str(int_date)[4:6]), int(str(int_date)[6:8])))
    except:
        return(np.nan)
    

def describe_lens(array, array_name):
    """
    Function to return descriptive array strings
    
    Parameters
    ----------
    array : array of lengths in seconds
    
    array_name : string
    
    Returns
    -------
    array_name : string
    
    array_description : string
    """
    if len(array):
        array_stats = stats.describe(array)
        return("".join([array_name,
                    ": mean=", time_rounding(np.array(array).mean()),
                    ", median=", time_rounding(np.median(np.array(array))),
                    ", n=", str(array_stats.nobs),
                    ", min=", time_rounding(array_stats.minmax[0]),
                    ", max=", time_rounding(array_stats.minmax[1])]))
    else:
        return("[Empty array]")
    
    
def dur_usable(dur, path, usable_table):
    """
    Function to discriminate usable durations
    
    Parameters
    ----------
    dur : float
       duration in seconds
    
    path : string
    
    usable_table : DataFrame, optional
        with columns ["RandID", "Date of recording"]
        
        
    Returns
    -------
    lens_usable : list of floats, given "usable", else empty list
    
    lens_all : list of floats
    """
    f = os.path.basename(path)
    lens_usable = []
    lens_all = []
    if int(f[:7]) in list(usable_table["RandID"]):
        if (datetime.fromtimestamp(os.stat(path).st_birthtime).date() >= 
        [v for v in usable_table[usable_table["RandID"] == int(f[:7])]["Date of recording"]][0]) or (
        [v for v in usable_table[usable_table["RandID"] == int(f[:7])]["Date of recording"]][0] ==
        np.nan):
            lens_usable.append(dur)
    lens_all.append(dur)
    return(lens_usable, lens_all)

    
def get_durs(path, usable=None, dur_dict={}):
    """
    Function to get durations from all files in a path and their subdirectories
    
    Parameters
    ----------
    path : string
    
    usable : DataFrame, optional
        with columns ["RandID", "Date of recording"]
        
        
    Returns
    -------
    lens_usable : list of floats, given "usable", else empty list
    
    lens_all : list of floats
    
    dur_dict : dict of (path, filepath, RandID, duration) tuples
    
    Output
    ------
    durations : csv
    """
    outfile = os.path.join(path, "".join([os.path.basename(path), "_", str(date.today()), ".csv"]))
    lens_usable = []
    lens_all = []
    dur_dict = {}
    for fpath in os.listdir(path):
        f_path = os.path.join(path, fpath)
        if os.path.isdir(f_path):
            print("Loading directory `{0}`".format(fpath))
            u, a, dd2 = get_durs(f_path, usable)
            for i in u:
                lens_usable.append(i)
            for i in a:
                lens_all.append(i)
            dur_dict = {**dur_dict, **dd2}
        elif f_path.endswith(".txt") or f_path.endswith(".csv") or f_path.endswith(".docx") or \
            f_path.endswith(".xlsx") or ".DS_Store" in f_path or "Thumbs.db" in f_path:
                continue
        else:
            randid = fpath[:7] if fpath[:7].isdigit() else os.path.basename(path)[:7]
            randid = randid if randid.isdigit() else os.path.dirname(path)[:7]
            print("… Loading {0}".format(fpath))
            try:
                g = shlex.quote(os.path.join(path, fpath))
                dur = float(re.sub(
                        r"\n",
                        "",
                        re.sub(
                            r"duration=",
                            "",
                            subprocess.check_output(
                                "".join([
                                    "ffprobe -v quiet -show_entries format=duration ",
                                    g,
                                    " | grep duration="]), shell=True).decode('utf-8'))
                    ))
                u, a = dur_usable(dur, os.path.join(path, fpath), usable)
                dur_dict[f_path] = (path, fpath, randid, dur)
                for i in u:
                    lens_usable.append(i)
                for i in a:
                    lens_all.append(i)
            except (ValueError, TypeError):
                lens_all.append(float(re.sub(
                        r"\n",
                        "",
                        re.sub(
                            r"duration=",
                            "",
                            subprocess.check_output(
                                "".join([
                                    "ffprobe -v quiet -show_entries format=duration ",
                                    g,
                                    " | grep duration="]), shell=True).decode('utf-8'))
                )))
                dur_dict[f_path] = (path, fpath, randid, dur)
            except:
                print(" ".join(["Could not load", g, ":", str(sys.exc_info()[0])]))
                dur_dict[f_path] = (path, fpath, randid, np.nan)
    if len(dur_dict) > 1:
        try:
            pd.DataFrame.from_dict(dur_dict, orient='index').rename(
                columns={0: 'directory', 1: 'filename', 2: 'RandID', 3: 'duration'}
                ).set_index('filename').to_csv(outfile)
        except:
            print("Could not save {0} as {1}".format(dur_dict, outfile))
        print(describe_lens(lens_all, path))
        if('MRI' in path):
            print('… (usable): {0}'.format(describe_lens(lens_all, path)))
    elif os.path.exists(outfile):
        print('rm -rf {0}'.format(outfile))
    return(lens_usable, lens_all, dur_dict)


def time_rounding(seconds, sig=3):
    """
    Function to round seconds to `sig` significant digits
    
    Parameters
    ----------
    seconds : float or int
    
    sig : int, optional
       number of significant digits
       
    Returns
    -------
    rounded_time : string
    """
    if seconds < 120:
        return ("%#.3g seconds" % seconds)
    else:
        minutes = seconds/60
        if minutes < 120:
            return ("%#.3g minutes" % minutes)
        else:
            hours = minutes/60
            return ("%#.3g hours" % hours)