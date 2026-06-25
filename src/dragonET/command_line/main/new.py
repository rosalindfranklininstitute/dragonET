from __future__ import annotations
import time
import typing

if typing.TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


NAME = "new"


def get_description() -> str:
    """
    Get the program description

    """
    return "Import experimental description"


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
        "-a",
        "--angles",
        type=str,
        default=None,
        required=True,
        help=(
            """
            The angles in the rawtlt file.
            """
        ),
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="initial_model.yaml",
        dest="model",
        help=(
            """
            A YAML file describing the initial model.
            """
        ),
    )
    parser.add_argument(
        "-r",
        "--global-rotation",
        type=float,
        default=0,
        dest="global_rotation",
        help="The global in plane rotation (degrees)",
    )


def run(namespace: Namespace) -> None:
    """
    Import the experimental description

    """
    from dragonET._new import _new

    # Get the start time
    start_time = time.time()

    # Do the work
    _new(
        namespace.projections,
        namespace.angles,
        namespace.model,
        namespace.global_rotation,
    )

    # Write some timing stats
    print("Time taken: %.2f seconds" % (time.time() - start_time))
