"""
Utility functions for VoiceSampleAnalysis
"""
from datetime import date, datetime
import numpy as np
import os
import re
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
    
    all_minus_usable : list of floats
    """
    f = os.path.basename(path)
    lens_usable = []
    lens_all = []
    all_minus_usable = []
    if int(f[:7]) in list(usable_table["RandID"]):
        if (datetime.fromtimestamp(os.stat(path).st_birthtime).date() >= 
        [v for v in usable_table[usable_table["RandID"] == int(f[:7])]["Date of recording"]][0]) or (
        [v for v in usable_table[usable_table["RandID"] == int(f[:7])]["Date of recording"]][0] ==
        np.nan):
            lens_usable.append(dur)
    elif "Post-MRI Audio Video" not in f:
        all_minus_usable.append(dur)
    lens_all.append(dur)
    return(lens_usable, lens_all, all_minus_usable)

    
def get_durs(path, usable=None):
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
    
    all_minus_usable : list of floats
    """
    lens_usable = []
    lens_all = []
    all_minus_usable = []
    for fpath in os.listdir(path):
        f_path = os.path.join(path, fpath)
        if os.path.isdir(f_path):
            print(" ".join(["Loading", fpath]))
            u, a, amu = get_durs(f_path, usable)
            for i in u:
                lens_usable.append(i)
            for i in a:
                lens_all.append(i)
            for i in amu:
                all_minus_usable.append(i)
        else:
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
                u, a, amu = dur_usable(dur, os.path.join(path, fpath), usable)
                for i in u:
                    lens_usable.append(i)
                for i in a:
                    lens_all.append(i)
                for i in amu:
                    all_minus_usable.append(i)
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
            except:
                print(" ".join(["Could not load", g, ":", str(sys.exc_info()[0])]))
    return(lens_usable, lens_all, all_minus_usable)