from __future__ import annotations
import time
import typing

if typing.TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


NAME = "track"


def get_description() -> str:
    """
    Get the program description

    """
    return "Do a rough alignment of the projection images"


def add_arguments(parser: ArgumentParser) -> None:
    # Add some command line arguments
    parser.add_argument(
        "-p",
        type=str,
        default=None,
        dest="projections_in",
        required=True,
        help=(
            """
            The filename for the projection images
            """
        ),
    )
    parser.add_argument(
        "--model_in",
        type=str,
        default=None,
        dest="model_in",
        required=True,
        help=(
            """
            A file describing the initial model.
            """
        ),
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=1,
        dest="threads",
        help=(
            """
            Number of threads to perform tracking with.
            """
        ),
    )
    parser.add_argument(
        "--model_out",
        type=str,
        default="tracked_model.yaml",
        dest="model_out",
        help=(
            """
            A file describing the output model.
            """
        ),
    )
    parser.add_argument(
        "--contours",
        type=str,
        default="contours.npz",
        dest="contours_out",
        help=(
            """
            A binary file describing the contours.
            """
        ),
    )


def run(namespace: Namespace) -> None:
    """
    Do a rough alignment of the projection images

    """
    from dragonET._track import _track

    # Get the start time
    start_time = time.time()

    # Do the work
    _track(
        namespace.projections_in,
        namespace.model_in,
        namespace.model_out,
        namespace.contours_out,
        namespace.threads,
    )

    # Write some timing stats
    print("Time taken: %.2f seconds" % (time.time() - start_time))
