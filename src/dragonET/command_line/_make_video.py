#
# make_video.py
#
# Copyright (C) 2024 Diamond Light Source and Rosalind Franklin Institute
#
# Author: James Parkhurst
#
import time
from argparse import ArgumentParser
from typing import List

import mrcfile  # type: ignore
import numpy as np
import imageio


__all__ = ["make_video"]


def get_description():
    """
    Get the program description

    """
    return "Make a video from a set of projections"


def get_parser(parser: ArgumentParser | None = None) -> ArgumentParser:
    """
    Get the new parser

    """

    # Initialise the parser
    if parser is None:
        parser = ArgumentParser(description=get_description())

    # Add some command line arguments
    parser.add_argument(
        "--mrc_filename",
        type=str,
        default=None,
        dest="mrc_filename",
        required=True,
        help=(
            """
            The mrc filename.
            """
        ),
    )
    parser.add_argument(
        "--movie_filename",
        type=str,
        default="movie.mp4",
        dest="movie_filename",
        help=(
            """
            The output movie filename.
            """
        ),
    )
    parser.add_argument(
        "--factor",
        type=int,
        default=1,
        dest="factor",
        help="The image binning factor.",
    )

    parser.add_argument(
        "--swap_axis",
        type=bool,
        default=False,
        dest="swap_axis",
        help="Swap the image axis.",
    )

    parser.add_argument(
        "--fps",
        type=float,
        default=10,
        dest="fps",
        help="The output frames per second.",
    )

    parser.add_argument(
        "--summed",
        type=int,
        default=1,
        dest="summed",
        help="The number of images to sum in output.",
    )

    parser.add_argument(
        "--vmin",
        type=int,
        default=0,
        dest="vmin",
        help="The minimum scaled image value.",
    )

    parser.add_argument(
        "--vmax",
        type=int,
        default=255,
        dest="vmax",
        help="The maximum scaled image value.",
    )

    return parser


def make_video_impl(args) -> None:
    """
    Import the experimental description

    """

    # Get the start time
    start_time = time.time()

    # Do the work
    _make_video(
        args.mrc_filename,
        args.movie_filename,
        args.factor,
        args.swap_axis,
        args.fps,
        args.summed,
        args.vmin,
        args.vmax,
    )

    # Write some timing stats
    print("Time taken: %.2f seconds" % (time.time() - start_time))


def make_video(args: List[str] | None = None):
    """
    Make a video from a set of projections

    """
    make_video_impl(get_parser().parse_args(args=args))


def rebin_stack(data: np.ndarray, factor: int) -> np.ndarray:
    """
    Rebin the image stack

    """

    def is_power_of_2(n):
        return (n & (n - 1) == 0) and n != 0

    # Check rebin factor
    assert is_power_of_2(factor)

    # If factor is > 1 then rebin
    if factor > 1:
        shape = np.array(data.shape) // np.array([1, factor, factor])
        print(
            "Rebinning stack by factor %d from (%d, %d) -> (%d, %d)"
            % (factor, data.shape[1], data.shape[2], shape[1], shape[2])
        )
        temp_shape = (
            shape[1],
            factor,
            shape[2],
            factor,
        )
        new_data = np.zeros(shape)
        for i in range(data.shape[0]):
            print(f"Rebinning image {i}")
            new_data[i] = data[i].reshape(temp_shape).sum(-1).sum(1).astype("float32")
        data = new_data
    return data


def sum_stack(data: np.ndarray, factor: int) -> np.ndarray:
    """
    Sum the stack.

    """

    def is_power_of_2(n):
        return (n & (n - 1) == 0) and n != 0

    # Check rebin factor
    assert is_power_of_2(factor)

    # If factor is > 1 then rebin
    if factor > 1:
        shape = np.array(data.shape) // np.array([factor, 1, 1])
        shape = (
            shape[0],
            factor,
            shape[1],
            shape[2],
        )
        data = data.reshape(shape).sum(1).astype("float32")
    return data


def _make_video(
    mrc_filename: str,
    movie_filename: str,
    factor: int,
    swapaxis: bool = False,
    fps: float = 10,
    summed: int = 1,
    scaled_vmin: int = 0,
    scaled_vmax: int = 255,
) -> None:
    """
    Make a video

    """
    h = mrcfile.mmap(mrc_filename)
    data = h.data

    if swapaxis:
        print("Swapping axes")
        data = np.swapaxes(data, 0, 1)

    if factor > 1:
        print("Rebinning data")
        data = rebin_stack(data, factor)

    if summed > 1:
        print("Summing data")
        data = sum_stack(data, summed)

    vmin = data.min()
    vmax = data.max()
    s1 = 255.0 / (vmax - vmin)
    s0 = -s1 * vmin

    t1 = 255.0 / (scaled_vmax - scaled_vmin)
    t0 = -t1 * scaled_vmin

    try:
        writer = imageio.get_writer(
            movie_filename,
            format="FFMPEG",  # type: ignore
            mode="I",
            fps=fps,
            codec="libx264",
        )
        for image in data:
            image = image * s1 + s0
            image = image * t1 + t0
            image = np.clip(image, 0, 255).astype(np.uint8)

            writer.append_data(image)
    finally:
        writer.close()
