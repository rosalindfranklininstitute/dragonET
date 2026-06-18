#
# reconstruct.py
#
# Copyright (C) 2024 Diamond Light Source and Rosalind Franklin Institute
#
# Author: James Parkhurst
#
from __future__ import annotations
import typing
import yaml

import astra  # type: ignore[import-untyped]
import mrcfile  # type: ignore[import-untyped]
import numpy as np
from scipy.spatial.transform import Rotation

if typing.TYPE_CHECKING:
    from os import PathLike

    from numpy.typing import NDArray


def _prepare_astra_geometry(
    P: NDArray[typing.Any],
    pixel_size: float = 1,
    image_size: tuple = (0, 0),
    axis: tuple[float, float, float] = (0, 1, 0),
    axis_origin: tuple[float, float, float] = (0, 0, 0),
) -> NDArray[typing.Any]:
    """
    Prepare the geometry vectors

    Params:
        P: The array of parameters
        pixel_size: The pixel size relative to the voxel size
        axis: The sample axis to align
        axis_origin: The sample axis origin to align

    Returns:
        The array of geometry vectors

    """

    def matrix_to_rotate_a_onto_b(
        a: NDArray[typing.Any], b: NDArray[typing.Any]
    ) -> NDArray[typing.Any]:
        # Compute the unit vectors
        a = a / np.linalg.norm(a)
        b = b / np.linalg.norm(b)

        # Compute the matrix
        # cos(t), -sin(t), 0
        # sin(t), cos(t), 0
        # 0, 0, 1
        d_ab = np.dot(a, b)
        c_ab = np.linalg.norm(np.cross(a, b))
        G = np.array([[d_ab, -c_ab, 0], [c_ab, d_ab, 0], [0, 0, 1]])

        # Compute the rotation matrix U such that Ua = b
        u = a
        v = b - np.dot(a, b) * a
        len_v = np.linalg.norm(v)
        if len_v > 0:
            v = v / len_v
            w = np.cross(b, a)
            F = np.linalg.inv(np.stack([u, v, w]).T)
            U = np.linalg.inv(F) @ G @ F
        else:
            U = np.diag((1.0, 1.0, 1.0))

        # Return the rotation matrix
        return U

    def prepare_sample_alignment_rotation_and_translation(
        axis: tuple[float, float, float],
        axis_origin: tuple[float, float, float],
        image_size: NDArray[np.integer],
    ) -> tuple[NDArray[typing.Any], NDArray[typing.Any]]:
        U = matrix_to_rotate_a_onto_b(np.asarray(axis), np.asarray((0, 1, 0)))
        new_axis_origin = -np.asarray(axis_origin) * np.asarray(
            [image_size[1], image_size[0], image_size[1]]
        )
        return U, new_axis_origin

    # print("Preparing geometry with pixel size %f" % pixel_size)
    assert all(np.array(image_size) > 0)

    # Prepare the transform to align the sample. The origin is wrt the centre
    # of the volume and the direction is a unit vector. Here we compute the
    # rotation matrix and translation that put a given line along the centre of
    # the reconstruction volume
    Rs, Ts = prepare_sample_alignment_rotation_and_translation(
        axis, axis_origin, np.asarray(image_size)
    )

    # The transformation
    shiftx = P[:, 0] * image_size[1]  # Shift X
    shifty = P[:, 1] * image_size[0]  # Shift Y
    a = np.radians(P[:, [2]])  # Yaw
    b = np.radians(P[:, [3]])  # Pitch
    c = np.radians(P[:, [4]])  # Roll

    # Create the rotation matrix for each image
    Ra = Rotation.from_euler("z", a).as_matrix()
    Rb = Rotation.from_euler("x", b).as_matrix()
    Rc = Rotation.from_euler("y", c).as_matrix()

    # Need to invert the rotation matrix for astra convention
    R = np.linalg.inv(Ra @ Rb @ Rc @ Rs.T)

    # Create the translation vector for each image
    t = np.stack([-shiftx, -shifty, np.zeros(shiftx.size)], axis=1)

    # Initialise the per-image geometry vectors
    vectors = np.zeros((P.shape[0], 12))

    # Ray direction vector
    vectors[:, 0:3] = R @ (0, 0, -1)

    # Detector centre
    vectors[:, 3:6] = (np.einsum("...ij,...j", R, t) + Ts) * pixel_size

    # Vector from detector pixel (0,0) to (0,1)
    vectors[:, 6:9] = R @ (pixel_size, 0, 0)

    # Vector from detector pixel (0,0) to (1,0)
    vectors[:, 9:12] = R @ (0, pixel_size, 0)

    # Return the vectors
    return vectors


def _reconstruct_with_astra(
    projections: NDArray[typing.Any],
    vectors: NDArray[typing.Any],
    volume: NDArray[typing.Any],
    num_iterations: int = 1,
    device: str = "gpu",
) -> NDArray[typing.Any]:
    """
    Do the reconstruction with astra

    Params:
        projections: The array of projections in sinogram order
        vectors: The array of geometry vectors
        volume: The initial volume
        num_iterations: The number of iterations
        device: The device to do the reconstruction on

    Returns:
        The reconstructed volume

    """

    # Create the volume geometry
    vol_geom = astra.create_vol_geom(
        volume.shape[1],  # Num rows in reconstruction (axis 1)
        volume.shape[2],  # Num cols in reconstruction (axis 2)
        volume.shape[0],  # Num slices in reconstruction (axis 0)
    )

    # Create the projection geometry
    proj_geom = astra.create_proj_geom(
        "parallel3d_vec",
        projections.shape[0],  # Num rows in projections (axis 0)
        projections.shape[2],  # Num cols in projections (axis 2)
        vectors,  # Geometry vectors
    )

    # Create the projection and reconstruction data
    projections_id = astra.data3d.create("-sino", proj_geom, projections)
    volume_id = astra.data3d.create("-vol", vol_geom, volume)

    # Check the device input
    if device not in ["gpu", "gpu_and_host", "host"]:
        raise RuntimeError("Device must be 'gpu' or 'host', got %s" % device)

    # Create the projector object
    if device in ["gpu", "gpu_and_host"]:
        projector_id = astra.create_projector("cuda3d", proj_geom, vol_geom)
    elif device in ["host"]:
        raise RuntimeError("Not implemented")

    # Configure the algorithm to use.
    if False:  # device in ["gpu"]:
        alg_cfg = astra.astra_dict("CGLS3D_CUDA")
    elif True:  # device in ["host", "gpu_and_host"]:
        astra.plugin.register(astra.plugins.CGLSPlugin)
        alg_cfg = astra.astra_dict("CGLS-PLUGIN")

    # Configure the algorithm
    alg_cfg["ProjectorId"] = projector_id
    alg_cfg["ProjectionDataId"] = projections_id
    alg_cfg["ReconstructionDataId"] = volume_id
    algorithm_id = astra.algorithm.create(alg_cfg)

    # Do the reconstruction
    # print("Reconstructing with %d iterations" % num_iterations)
    astra.algorithm.run(algorithm_id, iterations=num_iterations)

    # Get the reconstructed volume
    volume = astra.data3d.get(volume_id)

    # Cleanup the astra objects
    astra.algorithm.delete(algorithm_id)
    astra.data3d.delete(volume_id)
    astra.data3d.delete(projections_id)

    # Return the reconstructed volume
    return volume


def recon(
    projections: NDArray[typing.Any],
    P: NDArray[typing.Any],
    volume: NDArray[typing.Any],
    pixel_size: float,
    axis: tuple[float, float, float],
    axis_origin: tuple[float, float, float],
    num_iterations: int,
    device: str,
):
    """
    Do the reconstruction

    """
    # Get the image size
    image_size = projections.shape[::2]

    # Prepare the geometry vector description
    vectors = _prepare_astra_geometry(P, pixel_size, image_size, axis, axis_origin)

    # Do the reconstruction with astra
    return _reconstruct_with_astra(projections, vectors, volume, num_iterations, device)


def _reconstruct(
    projections_filename: str | PathLike[str],
    model_filename: str | PathLike[str],
    volume_filename: str | PathLike[str],
    initial_volume_filename: str | PathLike[str] | None = None,
    volume_shape: tuple | None = None,
    pixel_size: float = 1,
    num_iterations: int = 1,
    device: str = "gpu",
) -> None:
    """
    Do the reconstruction

    Params:
        projections_filename: The filename of the projections
        model_filename: The filename of the geometry model
        volume_filename: The filename of the reconstructed volume
        initial_volume_filename: The filename of the initial volume
        volume_shape: The shape of the output volume
        pixel_size: The pixel size on the images relative to the voxel size
        num_iterations: The number of iterations to use
        device: The device to do the reconstruction on

    """

    def read_model(filename: str | PathLike[str]) -> typing.Any:
        print("Reading model from %s" % filename)
        return yaml.safe_load(open(filename))

    def read_projections(filename: str | PathLike[str]) -> NDArray[typing.Any]:
        print("Reading projections from %s" % filename)
        data = mrcfile.mmap(filename).data
        if data is None:
            raise ValueError(f"No data in {filename}")
        return data

    def init_volume(
        filename: str | PathLike[str] | None, shape: int | tuple[int, ...]
    ) -> NDArray[typing.Any | np.float32]:
        if filename:
            print("Reading initial volume from %s" % filename)
            data = mrcfile.open(filename).data
            if data is None:
                raise ValueError(f"No data in {filename}")
            return np.asarray(data).copy()
        elif shape:
            print("Initialising volume with shape: (%d, %d, %d)" % shape)
            return np.zeros(shape, dtype=np.float32)
        raise ValueError("Failed to initialise volume, no filename or shape given")

    def write_volume(
        filename: str | PathLike[str], volume: NDArray[typing.Any]
    ) -> None:
        print("Writing volume to %s" % filename)
        outfile = mrcfile.new(filename, overwrite=True)
        outfile.set_data(volume)

    def normalise(v):
        return v / np.linalg.norm(v)

    def volume_shape_from_projections_shape(
        shape: NDArray[np.integer],
    ) -> tuple[int, int, int]:
        return (
            shape[0],
            shape[2],
            shape[2],
        )

    # Read the model
    model = read_model(model_filename)

    # Read the projections data
    projections_data = read_projections(projections_filename)

    # Get the transform from the model
    P = np.array(model["transform"], dtype=float)

    # Check the input is consistent
    assert P.shape[0] == projections_data.shape[0]

    # Get the vector to align to
    axis = normalise(model.get("axis", (0, 1, 0)))[::-1]
    axis_origin = model.get("axis_origin", (0, 0, 0))[::-1]

    # Put the projections in sinogram order
    projections = np.swapaxes(projections_data, 0, 1)

    # Initialise the volume shape if not provided
    if volume_shape is None:
        volume_shape = volume_shape_from_projections_shape(
            np.asarray(projections.shape)
        )

    # Initialise the volume. If a file is given, that is used as the volume.
    # Otherwise, initialise a volume of zeros of the desired share
    volume = init_volume(initial_volume_filename, volume_shape)

    # Do the reconstruction
    volume = recon(
        projections,
        P,
        volume,
        pixel_size,
        (axis[0], axis[1], axis[2]),
        (axis_origin[0, axis_origin[1], axis_origin[2]]),
        num_iterations,
        device,
    )

    # Create a new file with the reconstructed volume
    write_volume(volume_filename, volume)
