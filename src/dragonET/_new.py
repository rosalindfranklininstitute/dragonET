#
# new.py
#
# Copyright (C) 2024 Diamond Light Source and Rosalind Franklin Institute
#
# Author: James Parkhurst
#
from __future__ import annotations
import typing

import mrcfile  # type: ignore[import-untyped]
import numpy as np
import yaml

if typing.TYPE_CHECKING:
    from os import PathLike

    from numpy.typing import NDArray


def _new(
    projections_filename: str | PathLike[str],
    angles_filename: str | PathLike[str],
    model_filename: str | PathLike[str],
    global_rotation: float = 0,
) -> None:
    """
    Import the experimental description

    """

    def read_projections(filename: str | PathLike[str]) -> NDArray[typing.Any]:
        print("Reading projections from %s" % filename)
        data = mrcfile.mmap(filename).data
        if data is None:
            raise ValueError(f"No data in {filename}")
        return data

    def read_angles(filename: str | PathLike[str]) -> NDArray[np.float64]:
        print("Reading angles from %s" % filename)
        with open(filename) as f:
            return np.asarray([float(_) for _ in f.readlines()], dtype=np.float64)

    def write_model(filename: str | PathLike[str], model: typing.Any) -> None:
        print("Writing model to %s" % filename)
        yaml.safe_dump(model, open(filename, "w"), default_flow_style=None)

    # Load the projections data
    projections_data = read_projections(projections_filename)

    # Read the angles
    angles = read_angles(angles_filename)

    # Check input
    assert projections_data.shape[0] == angles.size

    # Set the image size
    image_size = projections_data.shape[1:]

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
