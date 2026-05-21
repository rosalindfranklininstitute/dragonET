from __future__ import annotations
import time
import typing

if typing.TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


NAME = "align"


def get_description() -> str:
    """
    Get the program description

    """
    return "Do a rough alignment of the projection images"


def add_arguments(parser: ArgumentParser) -> None:
    # Add some command line arguments
    parser.add_argument(
        "-p",
        type=str,
        default=None,
        dest="projections_in",
        required=True,
        help=(
            """
            The filename for the projection images
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
            A file describing the initial model.
            """
        ),
    )
    parser.add_argument(
        "--model_out",
        type=str,
        default="aligned_model.yaml",
        dest="model_out",
        help=(
            """
            A YAML file describing the refined model.
            """
        ),
    )
    parser.add_argument(
        "--reference_image",
        type=int,
        default=None,
        dest="reference_image",
        help="Set the reference image, if not set the angle closest to zero will be chosen",
    )
    parser.add_argument(
        "--max_shift",
        type=float,
        default=0.25,
        dest="max_shift",
        help="Maximum normalised image shift (between 0 and 1)",
    )
    parser.add_argument(
        "--max_iter",
        type=int,
        default=10,
        dest="max_iter",
        help="Maximum number of iterations (> 0)",
    )
    parser.add_argument(
        "--max_images",
        type=int,
        default=3,
        dest="max_images",
        help="Maximum number of images to use in multiple correlation (> 0)",
    )
    parser.add_argument(
        "--device",
        type=str,
        choices=["gpu", "cpu"],
        default="gpu",
        dest="device",
        help="The device settings to use",
    )


def run(namespace: Namespace) -> None:
    """
    Do a rough alignment of the projection images

    """
    from dragonET._align import _align

    # Get the start time
    start_time = time.time()

    # Do the work
    _align(
        namespace.projections_in,
        namespace.model_in,
        namespace.model_out,
        namespace.reference_image,
        namespace.max_shift,
        namespace.max_iter,
        namespace.max_images,
        namespace.device,
    )

    # Write some timing stats
    print("Time taken: %.2f seconds" % (time.time() - start_time))
