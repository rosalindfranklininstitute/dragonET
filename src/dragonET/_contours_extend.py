#
# contours_extend.py
#
# Copyright (C) 2024 Diamond Light Source and Rosalind Franklin Institute
#
# Author: James Parkhurst
from __future__ import annotations
import typing
import yaml

import mrcfile  # type: ignore[import-untyped]
import numpy as np
import scipy.ndimage

from scipy.spatial.transform import Rotation

from dragonET import _contours_triangulate, _stack_predict

if typing.TYPE_CHECKING:
    from os import PathLike

    from numpy.typing import NDArray

    _ArrayT = typing.TypeVar("_ArrayT", np.integer, np.floating)


def compute_derivatives(
    predicted: NDArray[typing.Any], image: NDArray[typing.Any]
) -> tuple[NDArray[typing.Any], NDArray[typing.Any], NDArray[typing.Any]]:
    """
    Compute the image derivatives

    """
    stencil = np.array([1 / 12, -2 / 3, 0, 2 / 3, -1 / 12])
    Ix = scipy.ndimage.convolve(predicted, stencil[None, :], mode="nearest")
    Iy = scipy.ndimage.convolve(predicted, stencil[:, None], mode="nearest")
    It = image - predicted
    return Ix, Iy, It


def compute_optical_flow(
    Ix: NDArray[typing.Any], Iy: NDArray[typing.Any], It: NDArray[typing.Any]
) -> NDArray[np.float64]:
    # Compute the weights
    # Wx = scipy.signal.windows.gaussian(Ix.shape[0], Ix.shape[0] / (2*3))
    # Wy = scipy.signal.windows.gaussian(Iy.shape[0], Iy.shape[0] / (2*3))
    # W = np.diag((Wx[None, :] * Wy[:, None]).flatten())

    # Compute the optical flow
    A = np.stack([Ix.flatten(), Iy.flatten()]).T
    B = -It.flatten()
    # V = np.linalg.pinv(A.T @ W @ A) @ (A.T @ W @ B)
    V = np.linalg.pinv(A.T @ A) @ (A.T @ B)
    return V


def extend_contours_for_image(
    stack: NDArray[typing.Any],
    image: NDArray[typing.Any],
    P_stack: NDArray[typing.Any],
    P_image: NDArray[typing.Any],
    points: NDArray[typing.Any],
    data: NDArray[typing.Any],
    mask: NDArray[np.bool_],
    octave: NDArray[np.int64],
    max_threshold: float = 0.8,
) -> tuple[NDArray[np.float64], NDArray[np.bool_]]:
    """
    Try to extend the contours onto the image

    """

    # Initialise the data and mask
    data_image = np.zeros((1, data.shape[1], data.shape[2]), dtype=np.float64)
    mask_image = np.zeros((1, mask.shape[1]), dtype=np.bool_)

    # Predict the image from the images
    predicted = _stack_predict.predict_image(stack, P_stack, P_image)

    # Compute the derivatives
    Ix, Iy, It = compute_derivatives(predicted, image)

    # Select features that are visible in the stack
    select = np.count_nonzero(mask, axis=0) > 0

    # Predict the feature on the image
    dx = P_image[0] + stack.shape[2] // 2
    dy = P_image[1] + stack.shape[1] // 2
    a = np.radians(P_image[2])
    b = np.radians(P_image[3])
    c = np.radians(P_image[4])

    # Get the rotation matrices
    Rabc = Rotation.from_euler("yxz", np.stack([c, b, a])).as_matrix()
    R = np.stack([Rabc[0, :], Rabc[1, :]])

    # The translation
    t = np.array([dx, dy])

    # Predict the points
    W = R @ points[:, select] + t[:, None]
    X = W[0, :]
    Y = W[1, :]

    # Compute the sizes
    size = 16 * 2 ** octave[select]

    # Loop through selected features
    cc = np.zeros(X.shape[0])
    Vx = np.zeros(X.shape[0])
    Vy = np.zeros(X.shape[0])
    for index in range(X.shape[0]):
        # Predict the x, y location of the feature
        xc = X[index]
        yc = Y[index]

        # Compute ROI
        i0 = int(max(0, np.floor(xc - size[index] // 2)))
        i1 = int(min(stack.shape[2], np.ceil(i0 + size[index])))
        j0 = int(max(0, np.floor(yc - size[index] // 2)))
        j1 = int(min(stack.shape[1], np.ceil(j0 + size[index])))
        if i0 >= i1 or j0 >= j1:
            continue

        # Compute the optical flow to register the feature
        V = compute_optical_flow(Ix[j0:j1, i0:i1], Iy[j0:j1, i0:i1], It[j0:j1, i0:i1])

        # Compute the CC of the registered feature
        p = predicted[j0:j1, i0:i1]
        o = image[j0:j1, i0:i1]
        o = scipy.ndimage.shift(o, V, order=1, prefilter=False, mode="nearest")
        cc[index] = np.corrcoef(p.flatten(), o.flatten())[0, 1]

        # Update the position
        Vx[index] = -V[0]
        Vy[index] = -V[1]

    # Set the updated points
    data_image[0, select, 0] = X + Vx
    data_image[0, select, 1] = Y + Vy

    # Select only those points whose cc is greater than a given value
    Q1, Q3 = np.quantile(cc, [0.25, 0.75])
    IQR = Q3 - Q1
    threshold = min(max_threshold, (Q1 - 1.5 * IQR))
    mask_image[0, select] = cc > threshold
    print(
        "Tracked %d / %d features with cc > %.2f and average shift of (%.1f, %.1f)"
        % (
            np.count_nonzero(mask_image),
            np.count_nonzero(select),
            threshold,
            np.mean(Vx),
            np.mean(Vy),
        )
    )

    # Return the data and mask
    return data_image, mask_image


def extend_contours_internal(
    projections: NDArray[typing.Any],
    P: NDArray[typing.Any],
    data: NDArray[_ArrayT],
    mask: NDArray[np.bool_],
    octave: NDArray[np.int64],
    subset_size: int,
) -> tuple[NDArray[_ArrayT], NDArray[np.bool_]]:
    """
    Try to extend the contours

    """

    # Check the subset size is atleast 1
    assert subset_size >= 1

    # Get the parameters
    dx = P[:, 0] + projections.shape[2] // 2
    dy = P[:, 1] + projections.shape[1] // 2
    a = np.radians(P[:, 2])
    b = np.radians(P[:, 3])
    c = np.radians(P[:, 4])

    # Triangulate the 3D points
    points = _contours_triangulate.triangulate(dx, dy, a, b, c, data, mask)

    # Copy input
    data = data.copy()
    mask = mask.copy()

    # Extend the contours for each image from adjacent images
    for j in range(data.shape[0]):
        for k, (i0, i1) in enumerate(
            [(j - subset_size, j), (j + 1, j + 1 + subset_size)]
        ):
            if i0 >= 0 and i1 <= data.shape[0]:
                print(
                    "Extending contours onto image %d from images %d to %d"
                    % (j, i0, i1)
                )
                data[j], mask[j] = extend_contours_for_image(
                    projections[i0:i1],
                    projections[j],
                    P[i0:i1],
                    P[j],
                    points,
                    data[i0:i1],
                    mask[i0:i1],
                    octave,
                )

    # Return the data and mask
    return data, mask


def _contours_extend(
    projections_in: str | PathLike[str],
    model_in: str | PathLike[str],
    contours_in: str | PathLike[str],
    contours_out: str | PathLike[str],
    subset_size: int,
) -> None:
    """
    Extend the contours

    """

    def read_projections(filename: str | PathLike[str]) -> NDArray[typing.Any]:
        print("Reading projections from %s" % filename)
        data = mrcfile.mmap(filename).data
        if data is None:
            raise ValueError(f"No data in {filename}")
        return data

    def read_points(
        filename: str | PathLike[str],
    ) -> tuple[NDArray[typing.Any], NDArray[np.bool_], NDArray[np.int64]]:
        print("Reading points from %s" % filename)
        handle = np.load(filename)
        return handle["data"], handle["mask"], handle["octave"]

    def read_model(filename: str | PathLike[str]) -> dict:
        print("Reading model from %s" % filename)
        return yaml.safe_load(open(filename, "r"))

    def write_points(
        filename: str | PathLike[str],
        data: NDArray[typing.Any],
        mask: NDArray[np.bool_],
        octave: NDArray[np.int64],
    ) -> None:
        print("Writing contours to %s" % filename)
        np.savez(open(filename, "wb"), data=data, mask=mask, octave=octave)

    # Read the projections
    projections = read_projections(projections_in)

    # Read the model
    model = read_model(model_in)

    # Get the parameters
    P = np.array(model["transform"])

    # Read the points
    data, mask, octave = read_points(contours_in)

    # Try to extend the contours
    data, mask = extend_contours_internal(
        projections, P, data, mask, octave, subset_size
    )

    # Write the contours
    write_points(contours_out, data, mask, octave)
