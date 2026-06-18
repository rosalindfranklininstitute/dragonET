#
# stack_predict.py
#
# Copyright (C) 2024 Diamond Light Source and Rosalind Franklin Institute
#
# Author: James Parkhurst
#
from __future__ import annotations
import typing
import yaml

import mrcfile  # type: ignore[import-untyped]
import numpy as np
from scipy.spatial.transform import Rotation

import dragonET._reconstruct

if typing.TYPE_CHECKING:
    from os import PathLike

    from numpy.typing import NDArray

    _ArrayT = typing.TypeVar("_ArrayT", np.integer, np.floating)


def get_matrix_from_parameters(P: NDArray[typing.Any]) -> NDArray[np.float64]:
    """
    Get the matrices from the parameters

    """

    # Create the rotation matrix for each image
    a = np.radians(P[:, 2])  # Yaw
    b = np.radians(P[:, 3])  # Pitch
    c = np.radians(P[:, 4])  # Roll
    Rabc = Rotation.from_euler("yxz", np.stack([c, b, a]).T).as_matrix()

    # Construct the matrix from the parameters
    R = np.full((P.shape[0], 4, 4), np.eye(4), dtype=np.float64)
    R[:, :3, :3] = Rabc
    R[:, 0, 3] = P[:, 0]  # Shift X
    R[:, 1, 3] = P[:, 1]  # Shift Y
    return R


def get_parameters_from_matrix(R: NDArray[typing.Any]) -> NDArray[np.float64]:
    """
    Get the parameters from the matrix

    """
    euler = Rotation.from_matrix(R[:, :3, :3]).as_euler("yxz")
    P = np.zeros((R.shape[0], 5), dtype=np.float64)
    P[:, 0] = R[:, 0, 3]
    P[:, 1] = R[:, 1, 3]
    P[:, 2] = np.degrees(euler[:, 2])
    P[:, 3] = np.degrees(euler[:, 1])
    P[:, 4] = np.degrees(euler[:, 0])
    return P


def predict_image(
    data: NDArray[typing.Any], P_data: NDArray[typing.Any], P_image: NDArray[typing.Any]
):
    """
    Predict the image

    """
    # Check the data and parameter shapes
    assert data.shape[0] == P_data.shape[0]

    # Get matrices for the image
    R_data = get_matrix_from_parameters(P_data)
    R_image = get_matrix_from_parameters(P_image[None, :])

    # Rotate all the input images w.r.t the output image
    R_data = R_data @ np.linalg.inv(R_image)
    R_image = R_image @ np.linalg.inv(R_image)

    # Get the updated parameter arrays
    P_data = get_parameters_from_matrix(R_data)
    P_image = get_parameters_from_matrix(R_image)

    # Compute the maximum angular difference between images
    R_diff = np.dot(R_data[:, :3, :3], R_image[:3, :3].T)
    cos_theta = (np.trace(R_diff, axis1=1, axis2=2) - 1) / 2
    diff_angle = np.abs(np.arccos(cos_theta))

    # Compute the height of the volume to reconstruct
    height = int(np.ceil(np.max(data.shape[1:]) * np.max(np.abs(np.sin(diff_angle)))))
    #    height = min(height, 10)

    # Init the volume
    shape = (data.shape[1], height, data.shape[2])
    volume = np.zeros(shape, dtype="float32")

    # Prepare to reconstruct
    data = np.swapaxes(data, 0, 1).copy()

    # Reconstruct the volume from the input images
    volume = dragonET._reconstruct.recon(
        data, P_data, volume, 1, (0, 1, 0), (0, 0, 0), 1, "gpu"
    )

    # Return the predicted image by projecting along the axis
    return np.sum(volume, axis=1)


def predict_stack(
    data: NDArray[_ArrayT], P: NDArray[typing.Any], subset_size: int
) -> NDArray[_ArrayT]:
    """
    Predict the stack images

    """
    # Check the subset size is atleast 1
    assert subset_size >= 1

    # Initialise the result. We have 2 predictions per image
    result = np.zeros_like(data)

    # Do the prediction for each image
    for j in range(data.shape[0]):
        i0 = np.clip(j - subset_size, 0, data.shape[0])
        i1 = np.clip(j + subset_size + 1, 0, data.shape[0])
        select = np.concatenate([np.arange(i0, j), np.arange(j + 1, i1)])
        print("Predicting image %d from images %d to %d" % (j, i0, i1))
        result[j] = predict_image(data[select], P[select], P[j])

    # Return the result
    return result


def _stack_predict(
    projections_in: str | PathLike[str],
    projections_out: str | PathLike[str],
    model_in: str | PathLike[str],
    subset_size: int,
) -> None:
    """
    Predict the stack images

    """

    def read_projections(filename: str | PathLike[str]) -> NDArray[typing.Any]:
        print("Reading projections from %s" % filename)
        data = mrcfile.mmap(filename).data
        if data is None:
            raise ValueError(f"No data in {filename}")
        return data

    def read_model(filename: str | PathLike[str]) -> typing.Any:
        print("Reading model from %s" % filename)
        return yaml.safe_load(open(filename))

    def write_projections(
        projections: NDArray[typing.Any], filename: str | PathLike[str]
    ) -> None:
        print("Writing projections to %s" % filename)
        handle = mrcfile.new(filename, overwrite=True)
        handle.set_data(projections)

    # Read the projections
    projections = read_projections(projections_in)

    # Read the model
    P = np.array(read_model(model_in)["transform"])

    # Predict the stack images
    projections = predict_stack(projections, P, subset_size)

    # Write the projections
    write_projections(projections, projections_out)
