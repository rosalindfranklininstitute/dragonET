#
# run.py
#
# Copyright (C) 2024 Diamond Light Source and Rosalind Franklin Institute
#
# Author: James Parkhurst
#
import time
import os
from argparse import ArgumentParser, Namespace
from typing import List

from dragonET._new import _new
from dragonET._track import _track
from dragonET._generate_angles import _generate_angles
from dragonET._reconstruct import _reconstruct
from dragonET._refine import _refine
from dragonET._stack_rebin import _stack_rebin
from dragonET._stack_transform import _stack_transform


__all__ = ["run"]


def get_description() -> str:
    """
    Get the program description

    """
    return "Run the automated pipeline"


def get_parser(parser: ArgumentParser | None = None) -> ArgumentParser:
    """
    Get the run parser

    """

    # Initialise the parser
    if parser is None:
        parser = ArgumentParser(description=get_description())

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
        required=False,
        help=(
            """
            The angles in the rawtlt file.
            """
        ),
    )
    parser.add_argument(
        "-r",
        "--global_rotation",
        type=float,
        default=0,
        dest="global_rotation",
        help="The global in plane rotation (degrees)",
    )
    parser.add_argument(
        "-f",
        "--rebin-factor",
        type=int,
        default=1,
        dest="rebin_factor",
        help=(
            """
            The rebin factor (must be a power of 2).
            """
        ),
    )
    parser.add_argument(
        "--device",
        type=str,
        choices=["gpu", "gpu_and_host", "host"],
        default="gpu",
        dest="device",
        help="The device settings to use",
    )

    return parser


def run_impl(args: Namespace) -> None:
    """
    Run the automated pipeline

    """

    # Get the start time
    start_time = time.time()

    # Do the work
    _run(
        args.projections,
        args.angles,
        args.global_rotation,
        args.rebin_factor,
        args.device,
    )

    # Write some timing stats
    print("Time taken: %.2f seconds" % (time.time() - start_time))


def run(args: List[str] | None = None) -> None:
    """
    Run the automated pipeline

    """
    run_impl(get_parser().parse_args(args=args))


def _run(
    projections_filename: str,
    angles_filename: str,
    global_rotation: float = 0,
    rebin_factor: int = 1,
    device: str = "gpu",
) -> None:
    """
    Run the automated pipeline

    """

    def is_power_of_2(n: int) -> bool:
        return (n & (n - 1) == 0) and n != 0

    # Check rebin factor
    assert is_power_of_2(rebin_factor)

    # Set up some filenames
    initial_model_filename = os.path.join("output", "initial_model.yaml")
    tracked_model_filename = os.path.join("output", "tracked_model.yaml")
    tracked_contours_filename = os.path.join("output", "tracked_contours.npz")
    refined_model_fix_bc_filename = os.path.join("output", "refined_model_fix_bc.yaml")
    refined_model_fix_c_filename = os.path.join("output", "refined_model_fix_c.yaml")
    rebinned_projections_filename = os.path.join("output", "rebinned_projections.mrc")
    aligned_projections_tracked_filename = os.path.join(
        "output", "aligned_projections_tracked.mrc"
    )
    aligned_projections_fix_bc_filename = os.path.join(
        "output", "aligned_projections_fix_bc.mrc"
    )
    aligned_projections_fix_c_filename = os.path.join(
        "output", "aligned_projections_fix_c.mrc"
    )
    volume_fix_bc_filename = os.path.join("output", "volume_fix_bc.mrc")
    volume_fix_c_filename = os.path.join("output", "volume_fix_c.mrc")

    # If no angles are specified
    if angles_filename is None or not os.path.exists(angles_filename):
        # Set the angles filename
        angles_filename = os.path.join("output", "angles.rawtlt")

        # And generate some new angles
        _generate_angles(projections_filename, angles_filename)

    # Import the experimental data and create initial model
    if not os.path.exists(initial_model_filename):
        _new(
            projections_filename,
            angles_filename,
            initial_model_filename,
            global_rotation,
        )

    # Find features and track them across images
    if not os.path.exists(tracked_contours_filename):
        _track(
            projections_filename,
            initial_model_filename,
            tracked_model_filename,
            tracked_contours_filename,
        )

    # Refine the initial model based on the contours (fix=bc)
    if not os.path.exists(refined_model_fix_bc_filename):
        _refine(
            initial_model_filename,
            refined_model_fix_bc_filename,
            tracked_contours_filename,
            fix="bc",
        )

    # Rerefine the model based on the contours (fix=c)
    if not os.path.exists(refined_model_fix_c_filename):
        _refine(
            refined_model_fix_bc_filename,
            refined_model_fix_c_filename,
            tracked_contours_filename,
            fix="c",
        )

    # Rebin the data
    if not os.path.exists(rebinned_projections_filename):
        _stack_rebin(projections_filename, rebinned_projections_filename, rebin_factor)

    # Make an aligned stack from the tracked projections
    if not os.path.exists(aligned_projections_tracked_filename):
        _stack_transform(
            rebinned_projections_filename,
            aligned_projections_tracked_filename,
            tracked_model_filename,
        )

    # Make an aligned stack from the fix bc projections
    if not os.path.exists(aligned_projections_fix_bc_filename):
        _stack_transform(
            rebinned_projections_filename,
            aligned_projections_fix_bc_filename,
            refined_model_fix_bc_filename,
        )

    # Make an aligned stack from the fix c projections
    if not os.path.exists(aligned_projections_fix_c_filename):
        _stack_transform(
            rebinned_projections_filename,
            aligned_projections_fix_c_filename,
            refined_model_fix_c_filename,
        )

    # Reconstruct the volume from the fix bc model
    if not os.path.exists(volume_fix_bc_filename):
        _reconstruct(
            rebinned_projections_filename,
            refined_model_fix_bc_filename,
            volume_fix_bc_filename,
            num_iterations=10,
            device=device,
        )

    # Reconstruct the volume from the fix c model
    if not os.path.exists(volume_fix_c_filename):
        _reconstruct(
            rebinned_projections_filename,
            refined_model_fix_c_filename,
            volume_fix_c_filename,
            num_iterations=10,
            device=device,
        )
