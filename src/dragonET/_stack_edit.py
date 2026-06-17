#
# stack_edit.py
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

    _ArrayT = typing.TypeVar("_ArrayT", np.integer, np.floating)


def exclude_images(data: NDArray[_ArrayT], exclude: list[int]) -> NDArray[_ArrayT]:
    """
    Remove images from stack

    """

    # If the exclude list is not None then exclude frames
    if exclude is not None:
        select = np.ones(data.shape[0], dtype=bool)
        select[exclude] = False
        data = data[select, :, :]
    return data


def _stack_edit(
    projections_in: str | PathLike[str],
    projections_out: str | PathLike[str],
    exclude: list[int],
) -> None:
    """
    Rebin the stack

    """

    def read_projections(filename: str | PathLike[str]) -> NDArray[typing.Any]:
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
    projections = exclude_images(projections, exclude)

    # Write the projections
    write_projections(projections, projections_out)
