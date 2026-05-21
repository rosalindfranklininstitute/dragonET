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

    # Check the header for the extended header. If the extended header exists
    # then use the angles as the rawtlt angles, otherwise, lets just assume
    # that the angular range is 180 degrees.
    if projections_file.header.exttyp in [b"FEI1", b"FEI2"]:
        assert len(projections_file.indexed_extended_header.shape) == 1
        assert (
            projections_file.indexed_extended_header.shape[0]
            == projections_file.data.shape[0]
        )
        extended_header = projections_file.indexed_extended_header
        angles = extended_header["Alpha tilt"]
    else:
        print("WARNING: Assuming ±90 angular range")
        step = 180 / (projections_file.data.shape[0] - 1)
        angles = -90 + step * np.arange(projections_file.data.shape[0])

    # Write out the angles
    write_angles(angles_filename, angles)
