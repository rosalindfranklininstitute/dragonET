#
# volume_select_sample_axis.py
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

import napari
import napari.layers

if typing.TYPE_CHECKING:
    from collections.abc import Iterable
    from os import PathLike

    from numpy.typing import NDArray
    from mrcfile.mrcmemmap import MrcMemmap


def _volume_select_sample_axis(
    volume_filename: str | PathLike[str],
    model_in_filename: str | PathLike[str],
    model_out_filename: str | PathLike[str],
) -> None:
    """
    Select sample axis

    """

    def read_volume(filename: str | PathLike[str]) -> MrcMemmap:
        print("Reading volume from %s" % filename)
        return mrcfile.mmap(filename)

    def read_model(filename: str | PathLike[str]):
        print("Reading model from %s" % filename)
        return yaml.safe_load(open(filename))

    def write_model(filename: str | PathLike[str], model) -> None:
        print("Writing model to %s" % filename)
        yaml.safe_dump(model, open(filename, "w"), default_flow_style=None)

    def normalise(v):
        n = np.linalg.norm(v)
        if n > 0:
            v = v / n
        return v

    def get_points(
        layers: Iterable[napari.layers.Layer], data: NDArray[typing.Any]
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        p1 = np.array((0, 0, 0))
        p2 = np.array((0, 1, 0))
        for layer in layers:
            if isinstance(layer, napari.layers.Points):
                points = np.asarray(layer.data)
                if points.shape[0] == 0:
                    print("- Warning: no points in layer")
                elif points.shape[0] == 1:
                    print("- Warning: only 1 point in layer")
                else:
                    p1 = points[0, :]
                    p2 = points[1, :]
                    print("Point 1: %f, %f, %f" % tuple(p1))
                    print("Point 2: %f, %f, %f" % tuple(p2))
                    p1 = p1 - np.array(data.shape) / 2
                    p2 = p2 - np.array(data.shape) / 2
                    break
        return (p1, p2)

    def compute_axis_and_origin(
        points: tuple[NDArray[np.float64], NDArray[np.float64]],
        shape: NDArray[np.integer],
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        p1, p2 = points
        axis = normalise(p2 - p1)
        t = -p1[1] / axis[1]
        axis_origin = t * axis + p1
        axis_origin = axis_origin / np.array(shape)
        return axis, axis_origin

    # Initialise the viewer
    viewer = napari.Viewer()

    # Load the projections data
    volume_file = read_volume(volume_filename)

    if volume_file.data is None:
        raise ValueError(f"No data in {volume_filename}")

    # Read the model
    model = read_model(model_in_filename)

    # Add the image layer
    viewer.add_image(volume_file.data, name="Projections")

    # Start Napari
    napari.run()

    volume_data = np.asarray(volume_file.data)

    # Compute origin and direction
    axis, axis_origin = compute_axis_and_origin(
        get_points(viewer.layers, volume_data), np.asarray(volume_data.shape)
    )
    print("Axis: %f, %f, %f" % tuple(axis))
    print("Axis origin: %f, %f, %f" % tuple(axis_origin))

    # Set the axis
    model["axis"] = axis.tolist()
    model["axis_origin"] = axis_origin.tolist()

    # Write the model
    write_model(model_out_filename, model)
