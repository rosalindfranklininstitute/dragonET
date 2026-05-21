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
    return "Refine a model to align the projection images"


def add_arguments(parser: ArgumentParser) -> None:
    # Add some command line arguments
    parser.add_argument(
        "--contours",
        type=str,
        default=None,
        dest="contours",
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
            A YAML file describing the refined model.
            """
        ),
    )
    parser.add_argument(
        "--fix",
        type=str,
        default="c",
        dest="fix",
        choices=["bc", "c", "none"],
        help="Fix parameters in refinement",
    )
    parser.add_argument(
        "--max_iter",
        type=int,
        default=100,
        dest="max_iter",
        help="The maximum number of iterations to perform",
    )
    parser.add_argument(
        "--smoothness",
        type=float,
        default=10,
        dest="smoothness",
        help="The smoothness regularisation parameter for angle refinement",
    )
    parser.add_argument(
        "--reference_image",
        type=int,
        default=None,
        dest="reference_image",
        help="Set the reference image, if not set the angle closest to zero will be chosen",
    )
    parser.add_argument(
        "--plots_out",
        type=str,
        default="plots",
        dest="plots_out",
        help=(
            """
            The directory to write some plots
            """
        ),
    )
    parser.add_argument(
        "--info_out",
        type=str,
        default=None,
        dest="info_out",
        help=(
            """
            A YAML file containing refinement information.
            """
        ),
    )
    parser.add_argument(
        "-v",
        default=False,
        dest="verbose",
        action="store_true",
        help=(
            """
            Set verbose output
            """
        ),
    )


def run(namespace: Namespace) -> None:
    """
    Refine the model of the sample and align the images

    """
    from dragonET._refine import _refine

    # Get the start time
    start_time = time.time()

    # Do the work
    _refine(
        namespace.model_in,
        namespace.model_out,
        namespace.contours,
        namespace.plots_out,
        namespace.info_out,
        namespace.fix,
        namespace.max_iter,
        namespace.smoothness,
        namespace.reference_image,
        namespace.verbose,
    )

    # Write some timing stats
    print("Time taken: %.2f seconds" % (time.time() - start_time))
