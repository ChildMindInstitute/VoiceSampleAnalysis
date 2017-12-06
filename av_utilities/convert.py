#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert.py

Script to quickly convert an av file to another type.

Currently will convert from:
    .mp3 (stereo)
    .mxf (stereo)
    .wav (stereo)

Currently will convert to:
    .mp3 (stereo)
    .wav (PCM signed 16-bit little-endian, stereo)

Author:
        – Jon Clucas, 2016 (jon.clucas@childmind.org)

© 2016, Child Mind Institute, Apache v2.0 License

Created on Fri Dec 23 12:43:40 2016

@author: jon.clucas
"""
import argparse
import os
import shlex
import subprocess
    

def collect_extension(dirpath, extension, skips=[
    "@Recycle",
    "Tests"
]):
    """
    function to collect mxf files in a given directory, recursively
    
    Parameters
    ----------
    dirpath: string
        path to search
    
    extension: string
        filetype
        
    skips: list of strings, optional
        directory and file names to skip,
        default: ["@Recycle", "Tests"]
        
    Returns
    -------
    collected: list of strings
        list of paths to files with given extension
    """
    collected = []
    for fp in [
        os.path.abspath(
            os.path.join(
                dirpath,
                f
            )
        ) for f in os.listdir(
                dirpath
        ) if f not in skips
    ]:
        if os.path.isdir(fp):
            try:
                collected = [*collected, *collect_extension(fp, extension, skips)]
            except:
                print("No {0} files in `{1}`.".format(
                    extension,
                    fp
                ))
        elif fp.lower().endswith(extension.lower()):
            collected.append(fp)
    return(collected)


def convert(in_file, ext_from, ext_to, out_path=None):
    # make an output filename
    out_base = os.path.basename(in_file[:-(1 + len(ext_from))])
    out_i = 0
    out_path = os.path.dirname(in_file) if not out_path else out_path
    out_file = os.path.join(out_path, '.'.join([out_base, ext_to]))
    while os.path.exists(out_file):
        out_file = os.path.join(out_path, '{0}_{1}.{2}'.format(
            out_base,
            str(out_i),
            ext_to
        ))
        out_i = out_i + 1
    # do the conversion verbosely
    to_convert = ''.join([
        "ffmpeg -i ",
        shlex.quote(in_file),
        ffmpeg_middle(ext_to),
        shlex.quote(out_file)
    ])
    print(''.join(["Converting \"", in_file, "\" to \"", out_file, "\""]))
    subprocess.call(to_convert, shell=True)
    

def ffmpeg_middle(ext_to):
    """
    Function to get ffmpeg command middle section to convert to a given
    file extension.
    
    Parameter
    ---------
    ext_to: string
        filetype to convert to
        
    Returns
    -------
    ffmiddle: string
        ffmpeg command middle section
    """
    ffmiddles = {
        "mp3": " -codec:a libmp3lame -ac 2 -qscale:a 2 ",
        "wav": " -ac 2 -acodec pcm_s16le "
    }
    return(ffmiddles[ext_to.lower()])


def main():
    # script can be run from the command line
    parser = argparse.ArgumentParser()
    parser.add_argument('in_file', metavar='in_file', type=str)
    parser.add_argument('ext_from', metavar='ext_from', type=str)
    parser.add_argument('ext_to', metavar='ext_to', type=str)
    parser.add_argument('out_path', metavar='out_path', type=str, default="")
    arg = parser.parse_args()
    if len(out_file):
        mxf_to_mp3(arg.in_file, arg.ext_from, arg.ext_to, arg.out_path)
    else:
        mxf_to_mp3(arg.in_file, arg.ext_from, arg.ext_to)

# ============================================================================
if __name__ == '__main__':
    main()
