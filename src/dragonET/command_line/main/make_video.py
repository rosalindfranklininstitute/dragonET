from __future__ import annotations
import time
import typing

if typing.TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


NAME = "make_video"


def get_description() -> str:
    """
    Get the program description

    """
    return "Make a video from a set of projections"


def add_arguments(parser: ArgumentParser) -> None:
    # Add some command line arguments
    parser.add_argument(
        "--mrc_filename",
        type=str,
        default=None,
        dest="mrc_filename",
        required=True,
        help=(
            """
            The mrc filename.
            """
        ),
    )
    parser.add_argument(
        "--movie_filename",
        type=str,
        default="movie.mp4",
        dest="movie_filename",
        help=(
            """
            The output movie filename.
            """
        ),
    )
    parser.add_argument(
        "--factor",
        type=int,
        default=1,
        dest="factor",
        help="The image binning factor.",
    )

    parser.add_argument(
        "--swap_axis",
        type=bool,
        default=False,
        dest="swap_axis",
        help="Swap the image axis.",
    )

    parser.add_argument(
        "--fps",
        type=float,
        default=10,
        dest="fps",
        help="The output frames per second.",
    )

    parser.add_argument(
        "--summed",
        type=int,
        default=1,
        dest="summed",
        help="The number of images to sum in output.",
    )

    parser.add_argument(
        "--vmin",
        type=int,
        default=0,
        dest="vmin",
        help="The minimum scaled image value.",
    )

    parser.add_argument(
        "--vmax",
        type=int,
        default=255,
        dest="vmax",
        help="The maximum scaled image value.",
    )


def run(namespace: Namespace) -> None:
    """
    Import the experimental description

    """
    from dragonET._make_video import _make_video

    # Get the start time
    start_time = time.time()

    # Do the work
    _make_video(
        namespace.mrc_filename,
        namespace.movie_filename,
        namespace.factor,
        namespace.swap_axis,
        namespace.fps,
        namespace.summed,
        namespace.vmin,
        namespace.vmax,
    )

    # Write some timing stats
    print("Time taken: %.2f seconds" % (time.time() - start_time))
