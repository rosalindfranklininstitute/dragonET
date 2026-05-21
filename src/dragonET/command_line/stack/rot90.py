from __future__ import annotations
import time
import typing

if typing.TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


NAME = "rot90"


def get_description() -> str:
    """
    Get the program description

    """
    return "Rotate the stack"


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
        default="rotated.mrc",
        dest="projections_out",
        help=(
            """
            The filename for the output projection images
            """
        ),
    )
    parser.add_argument(
        "-n",
        "--number",
        type=int,
        default=1,
        dest="number",
        help=(
            """
            The number of times to rotate by 90 degrees.
            """
        ),
    )


def stack_rot90_impl(namespace: Namespace) -> None:
    """
    Rotate the stack

    """
    from dragonET._stack_rot90 import _stack_rot90

    # Get the start time
    start_time = time.time()

    # Do the work
    _stack_rot90(
        namespace.projections_in,
        namespace.projections_out,
        namespace.number,
    )

    # Write some timing stats
    print("Time taken: %.2f seconds" % (time.time() - start_time))
