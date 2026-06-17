#
# contours_pick.py
#
# Copyright (C) 2024 Diamond Light Source and Rosalind Franklin Institute
#
# Author: James Parkhurst
#
from __future__ import annotations
import typing
from numpy._typing._array_like import NDArray
import yaml

import mrcfile  # type: ignore[import-untyped]
import numpy as np
from scipy.spatial.transform import Rotation

from dragonET import _stack_transform

if typing.TYPE_CHECKING:
    from os import PathLike


def _contours_pick(
    projections_filename: str | PathLike[str],
    contours_out_filename: str | PathLike[str],
    contours_in_filename: str | PathLike[str],
    model_in_filename: str | PathLike[str],
) -> None:
    """
    Pick the fiduccials manually

    """
    import napari  # type: ignore

    def read_projections(filename: str | PathLike[str]) -> NDArray[typing.Any]:
        print("Reading projections from %s" % filename)
        data = mrcfile.mmap(filename).data
        if data is None:
            raise ValueError(f"No data in {filename}")
        return data

    def read_contours(filename: str | PathLike[str]) -> typing.Any:
        print("Reading contours from %s" % filename)
        return np.load(filename)

    def read_model(filename: str | PathLike[str]) -> typing.Any:
        print("Reading model from %s" % filename)
        return yaml.safe_load(open(filename))

    def write_contours(filename: str | PathLike[str], contours) -> None:
        print("Writing contours to %s" % filename)
        np.savez(
            filename,
            data=contours["data"],
            mask=contours["mask"],
            octave=contours["octave"],
        )

    def set_contours(viewer, transform, contours, image_size) -> None:
        # Invert the transform
        transform = np.linalg.inv(transform)

        # If there are contours then add them as layers
        if contours:
            data = contours["data"]
            mask = contours["mask"]
            for index in range(data.shape[1]):
                print("Adding contour for point %d" % index)
                m = mask[:, index]
                z = np.where(m)[0]
                x, y = data[m, index, :].T
                x = x * image_size[1]
                y = y * image_size[0]
                c = np.stack([x, y, np.ones_like(x)]).T
                x, y, _ = (transform[z] @ c[:, :, None])[:, :, 0].T
                points = np.stack([z, y, x]).T
                name = "Points [%d]" % index if index > 0 else "Points"
                viewer.add_points(points, name=name, face_color="blue", size=5)

    def get_contours(viewer, transform, image_size):
        # Invert the transform
        # transform = np.linalg.inv(transform)

        # Loop through the point sets and get the lists of contours
        # Make sure to transform the points using the inverse transform
        contour_data = []
        contour_mask = []
        index = 0
        for layer in viewer.layers:
            if isinstance(layer, napari.layers.Points):
                points = layer.data
                if points.shape[0] == 0:
                    print("- Warning: skipping contour with no points")
                else:
                    print("Contour %d has %d points" % (index, points.shape[0]))
                    points = np.array(sorted(points.tolist(), key=lambda x: x[0]))
                    if points.shape[0] == 1:
                        print("- Warning: contour %d has only 1 point" % index)
                    if len(points[:, 0]) != len(set(points[:, 0])):
                        print(
                            "- Warning: Contour %d has more than 1 point per image, selecting one point"
                            % index
                        )
                    data = np.zeros((transform.shape[0], 2))
                    mask = np.zeros(transform.shape[0], dtype=bool)
                    for z, y, x in points.tolist():
                        x, y, _ = (transform[int(z)] @ np.array([x, y, 1])).tolist()
                        x /= image_size[1]
                        y /= image_size[0]
                        data[int(z)] = (x, y)
                        mask[int(z)] = 1
                    index += 1
                    contour_data.append(data[:, None, :])
                    contour_mask.append(mask[:, None])
        contours = {
            "data": np.concatenate(contour_data, axis=1),
            "mask": np.concatenate(contour_mask, axis=1),
        }
        contours["octave"] = np.ones(contours["data"].shape[1])
        return contours

    def get_transform_matrix(
        P: NDArray[typing.Any], image_size: NDArray[np.integer]
    ) -> NDArray[np.float64]:
        # Get the origin translation
        oy, ox = np.array(image_size) / 2

        # Get the components
        dx = P[:, 0] * image_size[1]
        dy = P[:, 1] * image_size[0]
        a = np.radians(P[:, [2]])
        np.radians(P[:, [3]])
        np.radians(P[:, [4]])

        # Only use in plane rotation and translation
        matrix = Rotation.from_euler("z", a).as_matrix()
        matrix[:, 0, 2] = dx
        matrix[:, 1, 2] = dy

        # Translate from centre of the image
        T = np.array([[1, 0, ox], [0, 1, oy], [0, 0, 1]])

        # First subtract the centre of image, then apply rotation, then
        # translate back to centre
        matrix = T @ matrix @ np.linalg.inv(T)

        # Return the matrix
        return matrix

    def transform_stack(projections, matrix):
        print("Transforming stack")
        return _stack_transform.transform_stack(projections, matrix)

    # Load the projections data
    projections = read_projections(projections_filename)

    # Read the contours
    contours = read_contours(contours_in_filename)

    # Read the model
    model = read_model(model_in_filename)

    # Get the transform matrix
    if model is not None:
        transform = get_transform_matrix(
            np.array(model["transform"]), np.asarray(projections.shape[1:])
        )
    else:
        transform = np.full((projections.shape[0], 3, 3), np.eye(3))

    # Transform the projections
    projections = transform_stack(projections, transform)

    # Initialise the viewer
    viewer = napari.Viewer()

    # Add the image layer
    viewer.add_image(projections, name="Projections")

    # Add the contours to the viewer
    set_contours(viewer, transform, contours, projections.shape[1:])

    # Start Napari
    napari.run()

    # Get the points layers
    contours = get_contours(viewer, transform, projections.shape[1:])

    # Write the contours
    write_contours(contours_out_filename, contours)
