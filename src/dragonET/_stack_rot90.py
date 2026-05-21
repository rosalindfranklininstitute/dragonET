#
# stack_rot90.py
#
# Copyright (C) 2024 Diamond Light Source and Rosalind Franklin Institute
#
# Author: James Parkhurst
#
import mrcfile  # type: ignore[import-untyped]
import numpy as np


def _stack_rot90(
    projections_in: str,
    projections_out: str,
    number: int,
):
    """
    Rotate the stack

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

    # Rotate the stack
    if number != 0:
        projections = np.rot90(projections, number, axes=(1, 2))

    # Write the projections
    write_projections(projections, projections_out)
