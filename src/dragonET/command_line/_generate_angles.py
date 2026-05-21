#
# generate_angles.py
#
# Copyright (C) 2024 Diamond Light Source and Rosalind Franklin Institute
#
# Author: James Parkhurst
#
import time
from argparse import ArgumentParser
from typing import List

import mrcfile  # type: ignore[import-untyped]
import numpy as np


__all__ = ["generate_angles"]


def get_description():
    """
    Get the program description

    """
    return "Generate an angles.rawtlt file."


def get_parser(parser: ArgumentParser | None = None) -> ArgumentParser:
    """
    Get the generate_angles parser

    """

    # Initialise the parser
    if parser is None:
        parser = ArgumentParser(description=get_description())

    # Add some command line arguments
    parser.add_argument(
        "-p",
        "--projections",
        type=str,
        default=None,
        dest="projections",
        required=True,
        help=(
            """
            The projection images.
            """
        ),
    )
    parser.add_argument(
        "-a",
        "--angles",
        type=str,
        default="angles.rawtlt",
        help=(
            """
            The angles in the rawtlt file.
            """
        ),
    )

    return parser


def generate_angles_impl(args):
    """
    Generate an angles.rawtlt file.

    """

    # Get the start time
    start_time = time.time()

    # Do the work
    _generate_angles(
        args.projections,
        args.angles,
    )

    # Write some timing stats
    print("Time taken: %.2f seconds" % (time.time() - start_time))


def generate_angles(args: List[str] | None = None):
    """
    Generate an angles.rawtlt file.

    """
    generate_angles_impl(get_parser().parse_args(args=args))


def _generate_angles(
    projections_filename: str,
    angles_filename: str,
):
    """
    Generate an angles.rawtlt file.

    """

    def read_projections(filename):
        print("Reading projections from %s" % filename)
        return mrcfile.mmap(filename)

    def write_angles(filename, angles):
        print("Write angles to %s" % filename)
        with open(filename, "w") as outfile:
            for a in angles:
                print(a)
                outfile.write("%f\n" % a)

    # Load the projections data
    projections_file = read_projections(projections_filename)

    # Generate some angles
    step = 180 / (projections_file.data.shape[0] - 1)
    angles = -90 + step * np.arange(projections_file.data.shape[0])

    # Write out the angles
    write_angles(angles_filename, angles)
