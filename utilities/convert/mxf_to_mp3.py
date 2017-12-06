#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mxf_to_mp3.py

Script to quickly convert an mxf file to an mp3 file.

Author:
        – Jon Clucas, 2016 (jon.clucas@childmind.org)

© 2016, Child Mind Institute, Apache v2.0 License

Created on Fri Dec 23 12:43:40 2016

@author: jon.clucas
"""
import argparse, subprocess
from os import path

def mxf_to_mp3(in_file, out_path=None):
    # make an output filename
    out_base = path.basename(in_file).strip('.mxf').strip('.MXF')
    out_i = 0
    out_path = path.dirname(in_file) if not out_path else out_path
    out_file = path.join(out_path, ''.join([out_base, '.mp3']))
    while path.exists(out_file):
        out_file = path.join(out_path, ''.join([out_base, '_',
                   str(out_i), '.mp3']))
        out_i = out_i + 1
    # do the conversion verbosely
    to_convert = ''.join([
        "ffmpeg -i ",
        in_file,
        " -codec:a libmp3lame -qscale:a 2 ",
        out_file
    ])
    print(''.join(["Converting ", in_file, " to ", out_file]))
    subprocess.call(to_convert, shell=True)

def main():
    # script can be run from the command line
    parser = argparse.ArgumentParser(description='get mxf')
    parser.add_argument('in_file', metavar='in_file', type=str)
    parser.add_argument('out_path', metavar='out_path', type=str, default="")
    arg = parser.parse_args()
    if len(out_file):
        mxf_to_mp3(arg.in_file, arg.out_path)
    else:
        mxf_to_mp3(arg.in_file)

# ============================================================================
if __name__ == '__main__':
    main()
