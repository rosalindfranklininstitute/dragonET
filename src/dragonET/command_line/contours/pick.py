from __future__ import annotations
import time
import typing

if typing.TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


NAME = "pick"


def get_description() -> str:
    """
    Get the program description

    """
    return "Manually pick fiduccials"


def add_arguments(parser: ArgumentParser) -> None:
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
        "-o",
        "--contours_out",
        type=str,
        default="contours.npz",
        dest="contours_out",
        help=(
            """
            A YAML file describing the picked point coordinates.
            """
        ),
    )
    parser.add_argument(
        "-i",
        "--contours_in",
        type=str,
        default=None,
        dest="contours_in",
        help=(
            """
            A YAML file describing the picked point coordinates.
            """
        ),
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default=None,
        dest="model",
        help=(
            """
            A YAML file describing the geometry model.
            """
        ),
    )


def run(namespace: Namespace) -> None:
    """
    Pick the fiduccials manually

    """
    from dragonET._contours_pick import _contours_pick

    # Get the start time
    start_time = time.time()

    # Do the work
    _contours_pick(
        namespace.projections,
        namespace.contours_out,
        namespace.contours_in,
        namespace.model,
    )

    # Write some timing stats
    print("Time taken: %.2f seconds" % (time.time() - start_time))
