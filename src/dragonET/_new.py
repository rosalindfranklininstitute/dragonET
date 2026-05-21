#
# new.py
#
# Copyright (C) 2024 Diamond Light Source and Rosalind Franklin Institute
#
# Author: James Parkhurst
#
import mrcfile  # type: ignore[import-untyped]
import numpy as np
import yaml


def _new(
    projections_filename: str,
    angles_filename: str,
    model_filename: str,
    global_rotation=0,
):
    """
    Import the experimental description

    """

    def read_projections(filename):
        print("Reading projections from %s" % filename)
        return mrcfile.mmap(filename)

    def read_angles(filename):
        print("Reading angles from %s" % filename)
        return np.array(list(map(float, open(filename).readlines())))

    def write_model(filename, model):
        print("Writing model to %s" % filename)
        yaml.safe_dump(model, open(filename, "w"), default_flow_style=None)

    # Load the projections data
    projections_file = read_projections(projections_filename)

    # Read the angles
    angles = read_angles(angles_filename)

    # Check input
    assert projections_file.data.shape[0] == angles.size

    # Set the image size
    image_size = projections_file.data.shape[1:]

    # Construct the transform
    P = np.zeros((angles.size, 5))
    P[:, 2] = global_rotation
    P[:, 4] = angles

    # Construct the model dictionary
    model = {
        "axis_origin": (0, 0, 0),
        "axis": (0, 1, 0),
        "image_size": image_size,
        "transform": P.tolist(),
    }

    # Write the model
    write_model(model_filename, model)
