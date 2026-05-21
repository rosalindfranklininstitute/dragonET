from __future__ import annotations
import time
import typing

if typing.TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


NAME = "rebin"


def get_description() -> str:
    """
    Get the program description

    """
    return "Rebin the volume"


def add_arguments(parser: ArgumentParser) -> None:
    # Add some command line arguments
    parser.add_argument(
        "-i",
        type=str,
        default=None,
        dest="volume_in",
        required=True,
        help=(
            """
            The filename for the input projection images
            """
        ),
    )
    parser.add_argument(
        "-o",
        type=str,
        default="rebinned.mrc",
        dest="volume_out",
        required=False,
        help=(
            """
            The filename for the output projection images
            """
        ),
    )
    parser.add_argument(
        "-f",
        "--factor",
        type=float,
        default=1,
        dest="factor",
        help=(
            """
            The rebin factor (must be a power of 2).
            """
        ),
    )


def run(namespace: Namespace) -> None:
    """
    Rebin the volume

    """
    from dragonET._volume_rebin import _volume_rebin

    # Get the start time
    start_time = time.time()

    # Do the work
    _volume_rebin(
        namespace.volume_in,
        namespace.volume_out,
        namespace.factor,
    )

    # Write some timing stats
    print("Time taken: %.2f seconds" % (time.time() - start_time))
