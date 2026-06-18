#
# volume_rebin.py
#
# Copyright (C) 2024 Diamond Light Source and Rosalind Franklin Institute
#
# Author: James Parkhurst
#
from __future__ import annotations
import typing

import mrcfile  # type: ignore[import-untyped]
from mrcfile.utils import mode_from_dtype
import numpy as np

if typing.TYPE_CHECKING:
    from os import PathLike

    from numpy.typing import NDArray

    _ArrayT = typing.TypeVar("_ArrayT", np.integer, np.floating)


def downsample_volume(data: NDArray[typing.Any], factor: int) -> NDArray[np.float32]:
    """
    Rebin the volume

    """

    def is_power_of_2(n: int) -> bool:
        return (n & (n - 1) == 0) and n != 0

    # Check rebin factor
    assert is_power_of_2(factor)

    # Downsample the volume
    shape = np.asarray(data.shape) // np.asarray([factor, factor, factor])
    print(
        "Rebinning volume by factor %d from (%d, %d, %d) -> (%d, %d, %d)"
        % (
            factor,
            data.shape[0],
            data.shape[1],
            data.shape[2],
            shape[0],
            shape[1],
            shape[2],
        )
    )
    shape = (
        shape[0],
        factor,
        shape[1],
        factor,
        shape[2],
        factor,
    )
    data = data.reshape(shape).sum(-1).sum(-2).sum(-3).astype(np.float32)

    # Return the sampled data
    return data


def upsample_volume(data: NDArray[_ArrayT], factor: int) -> NDArray[_ArrayT]:
    """
    Rebin the volume

    """

    def is_power_of_2(n) -> bool:
        return (n & (n - 1) == 0) and n != 0

    # Check rebin factor
    assert is_power_of_2(factor)

    # Save the original data scaled down
    scaled_original = data / factor**3

    # Upsample the volume
    shape = np.array(data.shape) * np.array([factor, factor, factor])
    print(
        "Rebinning volume by factor %d from (%d, %d, %d) -> (%d, %d, %d)"
        % (
            factor,
            data.shape[0],
            data.shape[1],
            data.shape[2],
            shape[0],
            shape[1],
            shape[2],
        )
    )
    data = np.zeros_like(data, shape=shape)
    for k in range(factor):
        for j in range(factor):
            for i in range(factor):
                data[k::factor, j::factor, i::factor] = scaled_original

    # Return the sampled data
    return data


def rebin_volume(
    data: NDArray[_ArrayT], factor: float
) -> NDArray[_ArrayT | np.float32]:
    """
    Rebin the volume

    """
    if factor > 1:
        return downsample_volume(data, int(np.round(factor)))
    elif factor < 1:
        return upsample_volume(data, int(np.round(1.0 / factor)))
    return data


def _volume_rebin(
    volume_in: str | PathLike[str],
    volume_out: str | PathLike[str],
    factor: float,
) -> None:
    """
    Rebin the volume

    """

    def read_volume(filename: str | PathLike[str]) -> NDArray[typing.Any]:
        print("Reading volume from %s" % filename)
        data = mrcfile.mmap(filename).data
        if data is None:
            raise ValueError(f"No data in {filename}")
        return data

    def write_volume(
        volume: NDArray[typing.Any], filename: str | PathLike[str]
    ) -> None:
        print("Writing volume to %s" % filename)
        handle = mrcfile.new_mmap(
            filename,
            volume.shape,
            mrc_mode=mode_from_dtype(volume.dtype),
            overwrite=True,
        )
        if handle.data is None:
            raise ValueError(f"No data in {filename}")
        handle.data[:] = volume

    # Read the volume
    volume = read_volume(volume_in)

    # Rebin the volume
    volume = rebin_volume(volume, factor)

    # Write the volume
    write_volume(volume, volume_out)
