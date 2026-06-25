#
# run.py
#
# Copyright (C) 2024 Diamond Light Source and Rosalind Franklin Institute
#
# Author: James Parkhurst
#
from __future__ import annotations
import time
import typing

if typing.TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


NAME = "run"


def get_description() -> str:
    """
    Get the program description

    """
    return "Run the automated pipeline"


def add_arguments(parser: ArgumentParser) -> None:
    """
    Add arguments to the run parser

    """
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
        default=None,
        required=False,
        help=(
            """
            The angles in the rawtlt file.
            """
        ),
    )
    parser.add_argument(
        "-r",
        "--global-rotation",
        type=float,
        default=0,
        dest="global_rotation",
        help="The global in plane rotation (degrees)",
    )
    parser.add_argument(
        "-f",
        "--rebin-factor",
        type=int,
        default=1,
        dest="rebin_factor",
        help=(
            """
            The rebin factor (must be a power of 2).
            """
        ),
    )
    parser.add_argument(
        "--device",
        type=str,
        choices=["gpu", "gpu_and_host", "host"],
        default="gpu",
        dest="device",
        help="The device settings to use",
    )
    parser.add_argument(
        "--processes",
        type=int,
        default=1,
        dest="processes",
        help=(
            """
            Number of processes to perform tracking with.
            """
        ),
    )


def run(namespace: Namespace) -> None:
    """
    Run the automated pipeline

    """
    from dragonET._run import _run

    # Get the start time
    start_time = time.time()

    # Do the work
    _run(
        namespace.projections,
        namespace.angles,
        namespace.global_rotation,
        namespace.rebin_factor,
        namespace.device,
        namespace.processes,
    )

    # Write some timing stats
    print("Time taken: %.2f seconds" % (time.time() - start_time))
