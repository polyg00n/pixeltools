"""
aov_selector.py

Handles detection and selection of available AOV channels from EXR files.
Provides utilities to support populating dropdowns or automated channel handling.
"""

import OpenEXR
import Imath


def list_aovs_from_exr(filepath):
    """
    Given an EXR file, returns a sorted list of unique AOV names.
    """
    if not filepath.endswith(".exr"):
        return []

    exr = OpenEXR.InputFile(filepath)
    header = exr.header()
    channels = header["channels"].keys()
    aovs = set()

    for chan in channels:
        if '.' in chan:
            aov = chan.split('.')[0]
            aovs.add(aov)

    return sorted(list(aovs))


def has_aov(filepath, aov_name):
    """
    Check if the specified AOV exists in the EXR file.
    """
    exr = OpenEXR.InputFile(filepath)
    return any(c.startswith(f"{aov_name}.") for c in exr.header()['channels'].keys())
