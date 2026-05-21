#
# generate_angles.py
#
# Copyright (C) 2024 Diamond Light Source and Rosalind Franklin Institute
#
# Author: James Parkhurst
#
import mrcfile  # type: ignore[import-untyped]
import numpy as np


def _generate_angles(
    projections_filename: str,
    angles_filename: str,
):
    """
    Generate an angles.rawtlt file.

    """

    def read_projections(filename):
        print("Reading projections from %s" % filename)
        return mrcfile.mmap(filename)

    def write_angles(filename, angles):
        print("Write angles to %s" % filename)
        with open(filename, "w") as outfile:
            for a in angles:
                print(a)
                outfile.write("%f\n" % a)

    # Load the projections data
    projections_file = read_projections(projections_filename)

    # Generate some angles
    step = 180 / (projections_file.data.shape[0] - 1)
    angles = -90 + step * np.arange(projections_file.data.shape[0])

    # Write out the angles
    write_angles(angles_filename, angles)
