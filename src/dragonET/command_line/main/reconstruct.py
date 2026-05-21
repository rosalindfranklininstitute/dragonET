from __future__ import annotations
import time
import typing

if typing.TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


NAME = "reconstruct"


def get_description() -> str:
    """
    Get the program description

    """
    return "Do the reconstruction"


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
        default="volume.mrc",
        dest="volume",
        help=(
            """
            The reconstructed volume.
            """
        ),
    )
    parser.add_argument(
        "-i",
        "--initial_volume",
        type=str,
        default=None,
        dest="initial_volume",
        help=(
            """
            The initial volume.
            """
        ),
    )
    parser.add_argument(
        "--volume_shape",
        type=lambda x: tuple(map(int, x.split(","))),
        default=None,
        dest="volume_shape",
        help="The shape of the volume",
    )
    parser.add_argument(
        "--pixel_size",
        type=float,
        default=1,
        dest="pixel_size",
        help="The pixel size relative to the voxel size",
    )
    parser.add_argument(
        "-n",
        "--num_iterations",
        type=int,
        default=1,
        dest="num_iterations",
        help="The number of iterations.",
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
    from dragonET._reconstruct import _reconstruct

    # Get the start time
    start_time = time.time()

    # Do the work
    _reconstruct(
        namespace.projections,
        namespace.model,
        namespace.volume,
        namespace.initial_volume,
        namespace.volume_shape,
        namespace.pixel_size,
        namespace.num_iterations,
        namespace.device,
    )

    # Write some timing stats
    print("Time taken: %.2f seconds" % (time.time() - start_time))
