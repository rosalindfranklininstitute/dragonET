from __future__ import annotations
import time
import typing

if typing.TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


NAME = "SELECT_SAMPLE_AXIS"


def get_description() -> str:
    """
    Get the program description

    """
    return "Select the sample axis"


def add_arguments(parser: ArgumentParser) -> None:
    # Add some command line arguments
    parser.add_argument(
        "-v",
        "--volume",
        type=str,
        default=None,
        dest="volume",
        required=True,
        help=(
            """
            The volume.
            """
        ),
    )
    parser.add_argument(
        "-i",
        "--model_in",
        type=str,
        default=None,
        dest="model_in",
        required=True,
        help=(
            """
            A YAML file describing the geometry model.
            """
        ),
    )
    parser.add_argument(
        "-o",
        "--model_out",
        type=str,
        default="aligned_model.yaml",
        dest="model_out",
        help=(
            """
            A YAML file describing the geometry model.
            """
        ),
    )


def volume_select_sample_axis_impl(namespace: Namespace) -> None:
    """
    Select the sample axis

    """
    from dragonET._volume_select_sample_axis import _volume_select_sample_axis

    # Get the start time
    start_time = time.time()

    # Do the work
    _volume_select_sample_axis(
        namespace.volume,
        namespace.model_in,
        namespace.model_out,
    )

    # Write some timing stats
    print("Time taken: %.2f seconds" % (time.time() - start_time))
