#
# run.py
#
# Copyright (C) 2024 Diamond Light Source and Rosalind Franklin Institute
#
# Author: James Parkhurst
#
import time
from argparse import ArgumentParser
from typing import List

import mrcfile # type: ignore
import numpy as np
import yaml

__all__ = ["run"]


def get_description():
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
        "--rebnglobal_rotation",
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

    return parser


def run_impl(args):
    """
    Run the automated pipeline

    """

    # Get the start time
    start_time = time.time()

    # Do the work
    _run(
        args.projections,
        args.angles,
        args.model,
        args.global_rotation,
        args.rebin_factor,
        args.device,
    )

    # Write some timing stats
    print("Time taken: %.2f seconds" % (time.time() - start_time))


def run(args: List[str] | None = None):
    """
    Run the automated pipeline

    """
    new_impl(get_parser().parse_args(args=args))


def _run(
    projections_filename: str,
    angles_filename: str,
    global_rotation: float =0,
    rebin_factor: int = 1,
    device: str = "gpu",
):
    """
    Run the automated pipeline

    """
    # Set up some filenames
    initial_model_filename = os.path.join("output", "initial_model.yaml")
    tracked_model_filename = os.path.join("output", "tracked_model.yaml")
    tracked_contours_filename = os.path.join("output", "tracked_contours.npz")
    refined_model_fix_bc_filename = os.path.join("output", "refined_model_fix_bc.yaml")
    refined_model_fix_c_filename = os.path.join("output", "refined_model_fix_c.yaml")
    rebinned_projections_filename = os.path.join("output", "rebinned_projections.mrc")
    volume_fix_bc_filename = os.path.join("output", "volume_fix_bc.mrc")
    volume_fix_c_filename = os.path.join("output", "volume_fix_c.mrc")
    
    
    # Import the experimental data and create initial model
    _new(
        projections_filename, 
        angles_filename, 
        initial_model_filename, 
        global_rotation
    )

    # Find features and track them across images
    _track(
        projections_filename, 
        initial_model_filename, 
        tracked_model_filename, 
        tracked_contours_filename
    )

    # Refine the initial model based on the contours (fix=bc)
    _refine(
        initial_model_filename,
        refined_model_fix_bc_filename,
        tracked_contours_filename,
        fix="bc",
    )
    
    # Rerefine the model based on the contours (fix=c)
    _refine(
        refined_model_fix_bc_filename,
        refined_model_fix_c_filename,
        tracked_contours_filename,
        fix="c",
    )

    # Rebin the data
    _stack_rebin(projections_filename, rebinned_projections_filename, rebin_factor)

    # Reconstruct the volume from the fix bc model
    _reconstruct(
        rebinned_projections_filename,
        refined_model_fix_bc_filename,
        volume_fix_bc_filename,
        num_iterations=10
        device=device,
    )

    # Reconstruct the volume from the fix c model
    _reconstruct(
        rebinned_projections_filename,
        refined_model_fix_c_filename,
        volume_fix_c_filename,
        num_iterations=10
        device=device,
    )
