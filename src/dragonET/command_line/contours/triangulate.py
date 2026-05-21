from __future__ import annotations
import time
import typing

if typing.TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


NAME = "triangulate"


def get_description() -> str:
    """
    Get the program description

    """
    return "Refine a model to align the projection images"


def add_arguments(parser: ArgumentParser) -> None:
    """
    Get the contours_triangulate parser

    """

    # Initialise the parser
    if parser is None:
        parser = ArgumentParser(description=get_description())

    # Add some command line arguments
    parser.add_argument(
        "--contours_in",
        type=str,
        default=None,
        dest="contours_in",
        required=True,
        help=(
            """
            A YAML file containing contour information.
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
            A file describing the initial model. This file can either be a
            .rawtlt file or a YAML file.
            """
        ),
    )
    parser.add_argument(
        "--points_out",
        type=str,
        default="triangulated.npz",
        dest="points_out",
        help=(
            """
            A YAML file describing the refined model.
            """
        ),
    )


def run(namespace: Namespace) -> None:
    """
    Triangulate the contours

    """
    from dragonET._contours_triangulate import _contours_triangulate

    # Get the start time
    start_time = time.time()

    # Do the work
    _contours_triangulate(
        namespace.model_in,
        namespace.contours_in,
        namespace.points_out,
    )

    # Write some timing stats
    print("Time taken: %.2f seconds" % (time.time() - start_time))
