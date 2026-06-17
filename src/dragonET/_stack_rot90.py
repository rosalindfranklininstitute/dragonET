#
# stack_rot90.py
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


def _stack_rot90(
    projections_in: str | PathLike[str],
    projections_out: str | PathLike[str],
    number: int,
) -> None:
    """
    Rotate the stack

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

    # Rotate the stack
    if number != 0:
        projections = np.rot90(projections, number, axes=(1, 2))

    # Write the projections
    write_projections(projections, projections_out)
