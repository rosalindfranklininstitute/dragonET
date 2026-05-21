from __future__ import annotations
import time
import typing

if typing.TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


NAME = "predict"


def get_description() -> str:
    """
    Get the program description

    """
    return "Predict the stack images"


def add_arguments(parser: ArgumentParser) -> None:
    # Add some command line arguments
    parser.add_argument(
        "-i",
        type=str,
        default=None,
        dest="projections_in",
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
        default="predicted.mrc",
        dest="projections_out",
        required=False,
        help=(
            """
            The filename for the output projection images
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
        "-s",
        "--subset_size",
        type=int,
        default=1,
        dest="subset_size",
        help=(
            """
            The size of the subset to use to predict adjacent images.
            """
        ),
    )


def run(namespace: Namespace) -> None:
    """
    Predict the stack images

    """
    from dragonET._stack_predict import _stack_predict

    # Get the start time
    start_time = time.time()

    # Do the work
    _stack_predict(
        namespace.projections_in,
        namespace.projections_out,
        namespace.model_in,
        namespace.subset_size,
    )

    # Write some timing stats
    print("Time taken: %.2f seconds" % (time.time() - start_time))
