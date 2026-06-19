#
# run.py
#
# Copyright (C) 2024 Diamond Light Source and Rosalind Franklin Institute
#
# Author: James Parkhurst
#
from __future__ import annotations
import os
import typing

from dragonET._new import _new
from dragonET._track import _track
from dragonET._generate_angles import _generate_angles
from dragonET._reconstruct import _reconstruct
from dragonET._refine import _refine
from dragonET._stack_rebin import _stack_rebin
from dragonET._stack_transform import _stack_transform

if typing.TYPE_CHECKING:
    from os import PathLike


def _run(
    projections_filename: str | PathLike[str],
    angles_filename: str | PathLike[str],
    global_rotation: float = 0,
    rebin_factor: int = 1,
    device: str = "gpu",
    processes: int = 1,
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
            processes=processes,
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
