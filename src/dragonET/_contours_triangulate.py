#
# contours_triangulate.py
#
# Copyright (C) 2024 Diamond Light Source and Rosalind Franklin Institute
#
# Author: James Parkhurst
#
from __future__ import annotations
import typing
import yaml

import numpy as np
from scipy.spatial.transform import Rotation

if typing.TYPE_CHECKING:
    from os import PathLike

    from numpy.typing import NDArray


def triangulate(dx, dy, a, b, c, data, mask: NDArray[np.bool_]) -> NDArray[np.float64]:
    """
    Triangulate the points

    """

    # Create the observation matrix
    W = np.concatenate([data[:, :, 0], data[:, :, 1]], axis=0)
    M = np.concatenate([mask, mask], axis=0)

    # Get number of points
    num_points = W.shape[1]

    # Get the rotation matrices
    Rabc = Rotation.from_euler("yxz", np.stack([c, b, a], axis=1)).as_matrix()
    R = np.concatenate([Rabc[:, 0, :], Rabc[:, 1, :]], axis=0)

    # The translation
    t = np.concatenate([dx, dy])

    # Subtract centroid
    W = W - t[:, None]

    # Compute the 3D spot positions
    S = np.zeros((3, num_points), dtype=np.float64)
    for j in range(num_points):
        Mj = M[:, j]
        W0 = W[Mj, j]
        Rj = R[Mj, :]
        S[:, j] = np.linalg.inv(Rj.T @ Rj) @ Rj.T @ W0
    return S


def _contours_triangulate(
    model_in: str | PathLike[str],
    contours_in: str | PathLike[str],
    points_out: str | PathLike[str],
):
    """
    Triangulate the contours

    """

    def read_points(filename) -> tuple:
        print("Reading points from %s" % filename)
        handle = np.load(filename)
        return handle["data"], handle["mask"], handle["octave"]

    def read_model(filename) -> dict:
        print("Reading model from %s" % filename)
        return yaml.safe_load(open(filename, "r"))

    def write_points(filename, points):
        print("Writing contours to %s" % filename)
        np.savez(open(filename, "wb"), points=points)

    # Read the model
    model = read_model(model_in)

    # Get the parameters
    P = np.array(model["transform"])

    # The image size
    model["image_size"]

    # Read the points
    data, mask, octave = read_points(contours_in)

    # Get the parameters
    dx = P[:, 0] + 0.5
    dy = P[:, 1] + 0.5
    a = np.radians(P[:, 2])
    b = np.radians(P[:, 3])
    c = np.radians(P[:, 4])

    # Triangulate the points
    points = triangulate(dx, dy, a, b, c, data, mask)

    # Write the contours
    write_points(points_out, points)
