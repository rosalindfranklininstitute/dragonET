from __future__ import annotations
import time
import typing

if typing.TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


NAME = "rebin"


def get_description() -> str:
    """
    Get the program description

    """
    return "Rebin the stack"


def add_arguments(parser: ArgumentParser) -> None:
    """
    Get the stack rebin parser

    """

    # Initialise the parser
    if parser is None:
        parser = ArgumentParser(description=get_description())

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
        default="rebinned.mrc",
        dest="projections_out",
        required=False,
        help=(
            """
            The filename for the output projection images
            """
        ),
    )
    parser.add_argument(
        "-f",
        "--factor",
        type=int,
        default=1,
        dest="factor",
        help=(
            """
            The rebin factor (must be a power of 2).
            """
        ),
    )


def stack_rebin_impl(namespace: Namespace) -> None:
    """
    Rebin the stack

    """
    from dragonET._stack_rebin import _stack_rebin

    # Get the start time
    start_time = time.time()

    # Do the work
    _stack_rebin(
        namespace.projections_in,
        namespace.projections_out,
        namespace.factor,
    )

    # Write some timing stats
    print("Time taken: %.2f seconds" % (time.time() - start_time))
