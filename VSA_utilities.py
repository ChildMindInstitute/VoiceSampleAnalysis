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


def archival_storages(archive_top="/Volumes/Voice Sample Data"):
    """
    Function to get archival directories
    
    Parameter
    ---------
    archive_top : string, optional
        default="/Volumes/Voice Sample Data"
    
    Returns
    -------
    archival_storages : set of strings
        directories in `archive_top` that end in a 4-digit number
    """
    if not os.path.exists(archive_top):
        print("{0} does not exist or is not connected".format(archive_top))
        return(set())
    else:
        return({os.path.abspath(os.path.join(archive_top, d)) for
                   d in
                   os.listdir(archive_top)
                   if (d[-4:].isdigit() and os.path.isdir(os.path.join(archive_top, d)))
               })


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
        int_date = int(
            "20{0}".format(str(int(int_date)))
            ) if len(str(int(int_date))) == 6 else int_date
        return(date(int(str(int_date)[:4]), int(str(int_date)[4:6]), int(str(int_date)[6:8])))
    except:
        return(np.nan)
    

def describe_lens(array, array_name):
    """
    Function to return descriptive array strings
    
    Parameters
    ----------
    array : list of 3-tuples of:
        RandID : integer
            participant ID
            
        upload_date : date
        
        recording_len : floats, given "usable", else empty list
           lengths in seconds
    
    array_name : string
    
    Returns
    -------
    array_name : string
    
    array_description : string
    """
    concatenated = dict()
    for r, u, l in array:
        concatenated[r] = l if r not in concatenated else concatenated[r] + l
    array = np.array(list(concatenated.values()))
    if len(array):
        array_stats = stats.describe(array)
        return("".join([array_name,
                    ": mean≈", time_rounding(np.nanmean(array)),
                    ", median≈", time_rounding(np.nanmedian(array)),
                    ", n=", str(array_stats.nobs - sum(np.isnan(array))),
                    ", min≈", time_rounding(np.nanmin(array)),
                    ", max≈", time_rounding(np.nanmax(array)),
                    ", total≈", time_rounding(np.nansum(array))
                    ])
              )
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
    lens_usable : list of 3-tuples of:
        RandID : integer
            participant ID
            
        upload_date : date
        
        recording_len : floats, given "usable", else empty list
           lengths in seconds
    
    lens_all : list of 3-tuples of:
        RandID : integer
            participant ID
            
        upload_date : date
        
        recording_len : floats
            lengths in seconds
    """
    f = os.path.basename(path)
    RandID = int(f[:7])
    RandID = 5178472 if RandID == 5174872 else RandID # miscoded participant
    upload_date = datetime.fromtimestamp(os.stat(path).st_birthtime)
    lens_usable = []
    lens_all = []
    if RandID in list(usable_table["RandID"]):
        if (upload_date.date() >=
        [v for v in usable_table[usable_table["RandID"] == RandID]["Date of recording"]][0]) or (
        [v for v in usable_table[usable_table["RandID"] == RandID]["Date of recording"]][0] ==
        np.nan):
            lens_usable.append((RandID, upload_date, dur))
        else:
            print("!!!!! {0}, {1}".format(RandID, upload_date))
    lens_all.append((RandID, upload_date, dur))
    return(lens_usable, lens_all)

    
def get_durs(path, usable=None, dur_dict={}):
    """
    Function to get durations from all files in a path and their subdirectories
    
    Parameters
    ----------
    path : string
       top-level directory
    
    usable : DataFrame, optional
        with columns ["RandID", "Date of recording"]
        
        
    Returns
    -------
    lens_usable : list of 3-tuples of:
        RandID : integer
            participant ID
            
        upload_date : date
        
        recording_len : floats, given "usable", else empty list
    
    lens_all : list of 3-tuples of:
        RandID : integer
            participant ID
            
        upload_date : date
        
        recording_len : floats
    
    dur_dict : dictionary with RandID keys of 
        dictionaries with f_path keys of
            (upload_date, duration) tuple values
    
    description : string
    
    Output
    ------
    durations : csv
    """
    outfile = os.path.join(path, "".join([os.path.basename(path), "_", str(date.today()), ".csv"]))
    desc_file = "_".join([outfile, "description.txt"])
    lens_usable = []
    lens_all = []
    dur_dict = {}
    description = ""
    for fpath in os.listdir(path):
        f_path = os.path.join(path, fpath)
        upload_date = datetime.fromtimestamp(os.stat(f_path).st_birthtime)
        if (os.path.isdir(f_path) and fpath not in ["@Recycle", "Tests"]):
            print("Loading directory `{0}`".format(fpath))
            u, a, dd2, desc = get_durs(f_path, usable)
            for i in u:
                lens_usable.append(i)
            for i in a:
                lens_all.append(i)
            dur_dict = {**dur_dict, **dd2}
            if len(desc):
                description = "\n\n".join([description, desc]) if len(description) else desc
        elif f_path.endswith(".txt") or f_path.endswith(".csv") or f_path.endswith(".docx") or \
            f_path.endswith(".xlsx") or ".DS_Store" in f_path or "Thumbs.db" in f_path or ".smbdelete" in f_path or \
            fpath in ["@Recycle", "Tests"]:
                continue
        else:
            randid = fpath[:7] if fpath[:7].isdigit() else os.path.basename(path)[:7]
            randid = randid if randid.isdigit() else fpath[:6]
            randid = randid if randid.isdigit() else os.path.dirname(fpath)[:7]
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
                dur_dict[randid] = (
                    upload_date,
                    dur
                ) if randid not in dur_dict else (
                    max(
                        upload_date,
                        dur_dict[randid][0]
                    ),
                    sum([
                        dur,
                        dur_dict[randid][1]
                    ])
                )
                for i in u:
                    lens_usable.append(i)
                for i in a:
                    lens_all.append(i)
            except (ValueError, TypeError):
                lens_all.append((randid, upload_date, float(re.sub(
                    r"\n",
                    "",
                    re.sub(
                        r"duration=",
                        "",
                        subprocess.check_output(
                            "".join([
                                "ffprobe -v quiet -show_entries format=duration ",
                                g,
                                " | grep duration="
                            ]),
                            shell=True
                        ).decode('utf-8')
                    )
                ))))
                dur_dict[randid] = (
                    upload_date,
                    dur
                ) if randid not in dur_dict else (
                    max(
                        upload_date,
                        dur_dict[randid][0]
                    ),
                    sum([
                        dur,
                        dur_dict[randid][1]
                    ])
                )
            except:
                print(" ".join(["Could not load", g, ":", str(sys.exc_info()[0])]))
                dur_dict[randid] = (
                    upload_date,
                    np.nan
                ) if randid not in dur_dict else (
                    max(
                        upload_date,
                        dur_dict[randid][0]
                    ),
                    dur_dict[randid][1]
                )
    if len(dur_dict) > 1:
        try:
            for d in dur_dict:
                ii = pd.DataFrame.from_dict(dur_dict[d], orient='index').rename(
                         columns={0: 'upload_date', 1: 'duration'}
                     )
                ii.index.name = 'filepath'
                ii['RandID'] = str(d)
                ii = ii[['RandID', 'upload_date', 'duration']]
                ii.to_csv(outfile)
        except:
            print("Could not save {0} as {1}".format(dur_dict, outfile))
        description = "\n\n".join([description, describe_lens(lens_all, path)]) if len(description
                      ) else describe_lens(lens_all, path)
        if('MRI' in path):
            description = "{0}\n…\t(usable): {1}".format(description, describe_lens(lens_usable, path))
        print(description)
        with open(desc_file, "w") as d_file:
            d_file.write(description)
    elif os.path.exists(outfile):
        print('rm -rf {0}'.format(outfile))
    return(lens_usable, lens_all, dur_dict, description)


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
            return ("{0} ({1}′{2}″)".format(
                "%#.3g minutes" % minutes,
                str(int(minutes // 1)),
                str(int(seconds % 60))
            ))
        else:
            hours = minutes/60
            return ("{0} ({1}′{2}″)".format(
                "%#.3g hours" % hours,
                str(format(int(minutes // 1), ",d")),
                str(int(seconds % 60))
            ))