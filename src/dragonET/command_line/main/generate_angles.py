from __future__ import annotations
import time
import typing

if typing.TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


NAME = "generate_angles"


def get_description() -> str:
    """
    Get the program description

    """
    return "Generate an angles.rawtlt file."


def add_arguments(parser: ArgumentParser) -> None:
    """
    Get the generate_angles parser

    """
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
        "-a",
        "--angles",
        type=str,
        default="angles.rawtlt",
        help=(
            """
            The angles in the rawtlt file.
            """
        ),
    )


def run(namespace: Namespace) -> None:
    """
    Generate an angles.rawtlt file.

    """
    from dragonET._generate_angles import _generate_angles

    # Get the start time
    start_time = time.time()

    # Do the work
    _generate_angles(
        namespace.projections,
        namespace.angles,
    )

    # Write some timing stats
    print("Time taken: %.2f seconds" % (time.time() - start_time))
