#
# stack_rebin.py
#
# Copyright (C) 2024 Diamond Light Source and Rosalind Franklin Institute
#
# Author: James Parkhurst
#
from __future__ import annotations
import typing

import mrcfile  # type: ignore[import-untyped]
import numpy as np

if typing.TYPE_CHECKING:
    from os import PathLike

    from numpy.typing import NDArray

    _ArrayT = typing.TypeVar("_ArrayT", np.floating, np.integer)


def rebin_stack(data: NDArray[_ArrayT], factor: int) -> NDArray[_ArrayT | np.float32]:
    """
    Rebin the image stack

    """

    def is_power_of_2(n: int) -> bool:
        return (n & (n - 1) == 0) and n != 0

    # Check rebin factor
    assert is_power_of_2(factor)

    # If factor is > 1 then rebin
    if factor > 1:
        shape = np.array(data.shape) // np.array([1, factor, factor])
        print(
            "Rebinning stack by factor %d from (%d, %d) -> (%d, %d)"
            % (factor, data.shape[1], data.shape[2], shape[1], shape[2])
        )
        shape = (
            shape[0],
            shape[1],
            factor,
            shape[2],
            factor,
        )
        data = data.reshape(shape).sum(-1).sum(2).astype(np.float32)
    return data


def _stack_rebin(
    projections_in: str | PathLike[str],
    projections_out: str | PathLike[str],
    factor: int,
):
    """
    Rebin the stack

    """

    def read_projections(filename) -> NDArray[typing.Any]:
        print("Reading projections from %s" % filename)
        data = mrcfile.mmap(filename).data
        if data is None:
            raise ValueError(f"No data in {filename}")
        return data

    def write_projections(
        projections: NDArray[typing.Any], filename: str | PathLike[str]
    ) -> None:
        print("Writing projections to %s" % filename)
        handle = mrcfile.new(filename, overwrite=True)
        handle.set_data(projections)

    # Read the projections
    projections = read_projections(projections_in)

    # Rebin the stack
    projections = rebin_stack(projections, factor)

    # Write the projections
    write_projections(projections, projections_out)
