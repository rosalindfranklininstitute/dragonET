from __future__ import annotations
import time
import typing

if typing.TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


NAME = "project"


def get_description() -> str:
    """
    Get the program description

    """
    return "Do the projection"


def add_arguments(parser: ArgumentParser) -> None:
    # Add some command line arguments
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default=None,
        dest="model",
        required=True,
        help=(
            """
            A file describing the initial model. This file can either be a
            .rawtlt file or a YAML file.
            """
        ),
    )
    parser.add_argument(
        "-v",
        "--volume",
        type=str,
        default=None,
        dest="volume",
        required=True,
        help=(
            """
            The volume to project from.
            """
        ),
    )
    parser.add_argument(
        "-p",
        "--projections",
        type=str,
        default="projections.mrc",
        dest="projections",
        help=(
            """
            The projection images.
            """
        ),
    )
    parser.add_argument(
        "--pixel_size",
        type=float,
        default=1,
        dest="pixel_size",
        help="The pixel size relative to the voxel size",
    )
    parser.add_argument(
        "--device",
        type=str,
        choices=["gpu", "gpu_and_host", "host"],
        default="gpu",
        dest="device",
        help="The device settings to use",
    )


def run(namespace: Namespace) -> None:
    """
    Reconstruct the volume

    """
    from dragonET._project import _project

    # Get the start time
    start_time = time.time()

    # Do the work
    _project(
        namespace.volume,
        namespace.model,
        namespace.projections,
        namespace.pixel_size,
        namespace.device,
    )

    # Write some timing stats
    print("Time taken: %.2f seconds" % (time.time() - start_time))
