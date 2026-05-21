from __future__ import annotations
import time
import typing

if typing.TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


NAME = "refine"


def get_description() -> str:
    """
    Get the program description

    """
    return "Refine the contours to match features better across images"


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
        "--model_out",
        type=str,
        default="refined_model.yaml",
        dest="model_out",
        help=(
            """
            A file describing the initial model. This file can either be a
            .rawtlt file or a YAML file.
            """
        ),
    )
    parser.add_argument(
        "--contours_out",
        type=str,
        default="refined.npz",
        dest="contours_out",
        help=(
            """
            A YAML file describing the refined model.
            """
        ),
    )
    parser.add_argument(
        "--num_macro_cycles",
        type=int,
        default=1,
        dest="num_macro_cycles",
        help=(
            """
            The number of macro cycles in the refinement.
            """
        ),
    )


def run(namespace: Namespace) -> None:
    """
    Extend the contours

    """
    from dragonET._contours_refine import _contours_refine

    # Get the start time
    start_time = time.time()

    # Do the work
    _contours_refine(
        namespace.projections_in,
        namespace.model_in,
        namespace.model_out,
        namespace.contours_in,
        namespace.contours_out,
        namespace.num_macro_cycles,
    )

    # Write some timing stats
    print("Time taken: %.2f seconds" % (time.time() - start_time))
