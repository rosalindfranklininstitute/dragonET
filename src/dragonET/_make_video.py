#
# make_video.py
#
# Copyright (C) 2024 Diamond Light Source and Rosalind Franklin Institute
#
# Author: James Parkhurst
#
from __future__ import annotations
import imageio
import typing

import mrcfile  # type: ignore[import-untyped]
import numpy as np

if typing.TYPE_CHECKING:
    from os import PathLike

    from numpy.typing import NDArray


def rebin_stack(data: np.ndarray, factor: int) -> NDArray[np.float32]:
    """
    Rebin the image stack

    """

    def is_power_of_2(n) -> bool:
        return (n & (n - 1) == 0) and n != 0

    # Check rebin factor
    if not is_power_of_2(factor):
        raise ValueError("Argument 'factor' must be a factor of 2")

    # If factor is > 1 then rebin
    if factor > 1:
        shape = np.array(data.shape) // np.array([1, factor, factor])
        print(
            "Rebinning stack by factor %d from (%d, %d) -> (%d, %d)"
            % (factor, data.shape[1], data.shape[2], shape[1], shape[2])
        )
        temp_shape = (
            shape[1],
            factor,
            shape[2],
            factor,
        )
        new_data = np.zeros(shape)
        for i in range(data.shape[0]):
            print(f"Rebinning image {i}")
            new_data[i] = data[i].reshape(temp_shape).sum(-1).sum(1).astype("float32")
        data = new_data
    return data


def sum_stack(data: NDArray[typing.Any], factor: int) -> NDArray[np.float32]:
    """
    Sum the stack.

    """

    def is_power_of_2(n) -> bool:
        return (n & (n - 1) == 0) and n != 0

    # Check sum factor
    if not is_power_of_2(factor):
        raise ValueError("Argument 'factor' must be a factor of 2")

    # If factor is > 1 then rebin
    if factor > 1:
        shape = np.array(data.shape) // np.array([factor, 1, 1])
        shape = (
            shape[0],
            factor,
            shape[1],
            shape[2],
        )
        data = data.reshape(shape).sum(1).astype("float32")
    return data


def _make_video(
    mrc_filename: str | PathLike[str],
    movie_filename: str | PathLike[str],
    factor: int,
    swapaxis: bool = False,
    fps: float = 10,
    summed: int = 1,
    scaled_vmin: int = 0,
    scaled_vmax: int = 255,
) -> None:
    """
    Make a video

    """
    h = mrcfile.mmap(mrc_filename)
    if h.data is None:
        raise ValueError(f"No data in {mrc_filename}")
    data = np.asarray(h.data)

    if swapaxis:
        print("Swapping axes")
        data = np.swapaxes(data, 0, 1)

    if factor > 1:
        print("Rebinning data")
        data = rebin_stack(data, factor)

    if summed > 1:
        print("Summing data")
        data = sum_stack(data, summed)

    vmin = data.min()
    vmax = data.max()
    s1 = 255.0 / (vmax - vmin)
    s0 = -s1 * vmin

    t1 = 255.0 / (scaled_vmax - scaled_vmin)
    t0 = -t1 * scaled_vmin

    try:
        writer = imageio.get_writer(
            str(movie_filename),
            format="FFMPEG",  # type: ignore
            mode="I",
            fps=fps,
            codec="libx264",
        )
        for image in data:
            image = image * s1 + s0
            image = image * t1 + t0
            image = np.clip(image, 0, 255).astype(np.uint8)

            writer.append_data(image)
    finally:
        writer.close()
