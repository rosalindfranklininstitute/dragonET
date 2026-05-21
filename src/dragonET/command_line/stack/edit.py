from __future__ import annotations
import time
import typing

if typing.TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


NAME = "edit"


def get_description() -> str:
    """
    Get the program description

    """
    return "Rebin the stack"


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
        default="edited.mrc",
        dest="projections_out",
        required=False,
        help=(
            """
            The filename for the output projection images
            """
        ),
    )
    parser.add_argument(
        "--exclude",
        type=lambda x: [int(xx) for xx in x.split(",")],
        default=None,
        dest="exclude",
        help=(
            """
            The image indices (zero indexed) to exclude.
            """
        ),
    )


def run(namespace: Namespace) -> None:
    """
    Rebin the stack

    """
    from dragonET._stack_edit import _stack_edit

    # Get the start time
    start_time = time.time()

    # Do the work
    _stack_edit(
        namespace.projections_in,
        namespace.projections_out,
        namespace.exclude,
    )

    # Write some timing stats
    print("Time taken: %.2f seconds" % (time.time() - start_time))
