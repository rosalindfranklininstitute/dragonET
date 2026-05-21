from __future__ import annotations
import time
import typing

if typing.TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


NAME = "transform"


def get_description() -> str:
    """
    Get the program description

    """
    return "Transform the stack"


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
        default="transformed.mrc",
        dest="projections_out",
        required=False,
        help=(
            """
            The filename for the output projection images
            """
        ),
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default=None,
        dest="model_in",
        required=True,
        help=(
            """
            The transform model.
            """
        ),
    )


def run(namespace: Namespace) -> None:
    """
    Transform the stack

    """
    from dragonET._stack_transform import _stack_transform

    # Get the start time
    start_time = time.time()

    # Do the work
    _stack_transform(
        namespace.projections_in,
        namespace.projections_out,
        namespace.model_in,
    )

    # Write some timing stats
    print("Time taken: %.2f seconds" % (time.time() - start_time))
