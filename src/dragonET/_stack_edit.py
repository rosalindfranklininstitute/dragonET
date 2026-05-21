#
# stack_edit.py
#
# Copyright (C) 2024 Diamond Light Source and Rosalind Franklin Institute
#
# Author: James Parkhurst
#
import mrcfile  # type: ignore[import-untyped]
import numpy as np


def exclude_images(data: np.ndarray, exclude: list) -> np.ndarray:
    """
    Remove images from stack

    """

    # If the exclude list is not None then exclude frames
    if exclude is not None:
        select = np.ones(data.shape[0], dtype=bool)
        select[exclude] = False
        data = data[select, :, :]
    return data


def _stack_edit(
    projections_in: str,
    projections_out: str,
    exclude: list,
):
    """
    Rebin the stack

    """

    def read_projections(filename):
        print("Reading projections from %s" % filename)
        return mrcfile.mmap(filename).data

    def write_projections(projections, filename):
        print("Writing projections to %s" % filename)
        handle = mrcfile.new(filename, overwrite=True)
        handle.set_data(projections)

    # Read the projections
    projections = read_projections(projections_in)

    # Rebin the stack
    projections = exclude_images(projections, exclude)

    # Write the projections
    write_projections(projections, projections_out)
