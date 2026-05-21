#
# track.py
#
# Copyright (C) 2024 Diamond Light Source and Rosalind Franklin Institute
#
# Author: James Parkhurst
#
from collections import defaultdict
import typing

import mrcfile  # type: ignore[import-untyped]
import numpy as np
import yaml

from multiprocessing import Pool
from scipy.spatial.transform import Rotation
from skimage.feature import SIFT, match_descriptors  # , plot_matches
from skimage.measure import ransac
from skimage.transform import EuclideanTransform


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
        shape = (
            shape[0],
            shape[1],
            factor,
            shape[2],
            factor,
        )
        data = data.reshape(shape).sum(-1).sum(2)
    return data


def _detect_and_extract(projection, descriptor_extractor):  #ndarray, int
    descriptor_extractor.detect_and_extract(projection)
    # where is detector extractor
    print("making feature dict")
    feature_dict = {
        "keypoints": descriptor_extractor.positions[:, ::-1]
        / image_size[None, ::-1],
        "descriptors": descriptor_extractor.descriptors,
        "octaves": descriptor_extractor.octaves,  # + rebin_factor_octave,
        "scales": descriptor_extractor.scales,  # + rebin_factor_octave,
        "orientations": descriptor_extractor.orientations,
        }
    print("features made")

    print(
        "Extracted %d features from image %d / %d"
        % (len(descriptor_extractor.positions), i + 1, projections.shape[0])
    )

    return feature_dict


def extract_features(projections, rebin_factor, threads) -> list[dict[str, typing.Any]]:
    # Get the rebin factor octave
    np.log2(rebin_factor).astype(int)

    # Get the image size
    image_size = np.array(projections.shape[1:])

    # Initialise the list of SIFT objects
    SIFTs = [
        SIFT(upsampling=1, n_scales=32, n_octaves=32, n_hist=32, n_ori=32)
        for _ in range(threads)
        ]

    # projections are mapped to an index of each SIFT in tuples for starmap
    # projection_indexes = [i for i in range(projections.shape[0])]
    SIFT_indexes = [i % len(SIFTs) for i in range(projections.shape[0])]
    projection_SIFT_pairs = [(projections[i], SIFTs[SIFT_item]) for i, SIFT_item in enumerate(SIFT_indexes)]

    features = []

    # pool aatempt
    with Pool(processes=threads) as p:
        features = p.starmap(_detect_and_extract, projection_SIFT_pairs)

    assert features != []
    return features


def find_matching_features(features, min_samples=4):
    # Initialise the transformation matrix for each image
    matrix = np.full((len(features), 3, 3), np.eye(3))

    # Initialise the list of matches
    match_list = {}

    # Match features across adjacent images
    for i, j in enumerate(range(1, len(features))):
        # Match the features
        matches = match_descriptors(
            features[i]["descriptors"],
            features[j]["descriptors"],
            max_ratio=0.95,
            cross_check=True,
        )

        # Get the octaves
        octaves_i, octaves_j = (
            features[i]["octaves"][matches[:, 0]],
            features[j]["octaves"][matches[:, 1]],
        )

        # Select only those points which have matching octaves
        matches = matches[octaves_i == octaves_j, :]

        # Get the orientations
        orientations_i, orientations_j = (
            features[i]["orientations"][matches[:, 0]],
            features[j]["orientations"][matches[:, 1]],
        )

        # Compute the angular difference and select those with an angular
        # difference less than the number of divisions used to find the
        # orientation
        zn = np.exp(1j * (orientations_i - orientations_j))
        angle_diff = np.abs(np.angle(zn) - np.angle(np.median(zn)))
        select_orientation = angle_diff < (2 * np.pi / 16)

        # Select only those with matching orientations
        matches = matches[select_orientation, :]

        # Get the positions
        positions_i, positions_j = (
            features[i]["keypoints"][matches[:, 0]],
            features[j]["keypoints"][matches[:, 1]],
        )

        # Only bother if we have enough samples
        try:
            assert len(positions_i) >= min_samples

            # Compute the Euclidean transform
            transform, inliers = ransac(
                (positions_i, positions_j),
                EuclideanTransform,
                min_samples=min_samples,
                residual_threshold=0.009765625,  # 0.01,
                max_trials=1000,
            )

            # Check the number of inliers
            assert np.count_nonzero(inliers) >= min_samples

            # Add the list of matches to a dictionary.
            for index in np.where(inliers)[0]:
                key_i = (i, matches[index, 0])
                key_j = (j, matches[index, 1])
                match_list[key_i] = key_j

            # Update the matrix
            matrix[j] = transform.params @ matrix[j - 1]
        except Exception:
            inliers = np.zeros(positions_i.shape[0], dtype=bool)

        print(
            "Matching images (%d, %d): fitted %d points out of %d matches from (%d, %d) features"
            % (
                i + 1,
                j + 1,
                np.count_nonzero(inliers),
                matches.shape[0],
                len(features[i]["keypoints"]),
                len(features[j]["keypoints"]),
            )
        )

    return matrix, match_list


def construct_data_matrix(features, match_list):
    # Check if the point is already part of an existing contour
    def find(key_i):
        for key, value in contours.items():
            if key_i in value:
                return key
        return None

    # Construct the contours
    contours = defaultdict(set)
    for key_i, key_j in match_list.items():
        key = find(key_i)
        if key is not None:
            contours[key].add(key_j)
        else:
            contours[key_i].add(key_j)

    # Compute the number of frames and points
    num_frames = len(features)
    num_points = len(contours)

    # Construct the data matrix and mask
    data = np.zeros((num_frames, num_points, 2))
    mask = np.zeros((num_frames, num_points), dtype=bool)
    octave = np.zeros(num_points, dtype=int)
    for index, key in enumerate(contours):
        octave[index] = features[key[0]]["octaves"][key[1]]
        for frame, feature_index in [key] + list(contours[key]):
            mask[frame, index] = True
            data[frame, index] = features[frame]["keypoints"][feature_index]
            assert octave[index] == features[frame]["octaves"][feature_index]

    # Select only those points which have 3 or more observations which is a
    # requirement to ensure that the point can be triangulated in 3D.
    # select = np.count_nonzero(mask, axis=0) >= 3
    # data = data[:, select]
    # mask = mask[:, select]

    # print(
    #     "Selected %d / %d points with >= 3 observations"
    #     % (np.count_nonzero(select), select.size)
    # )

    # Return the data matrix and mask
    return data, mask, octave


def recentre_points(data, mask, matrix, origin=(0, 0)):
    # Compute the initial translation which brings the points on each image
    # closest to the origin
    Ox, Oy = origin
    A = []
    B = []
    for j in range(data.shape[0]):
        for i in range(data.shape[1]):
            if mask[j, i]:
                M00, M01, M02 = matrix[j, 0, :]
                M10, M11, M12 = matrix[j, 1, :]
                Rx = data[j, i, 0] - M00 * Ox - M01 * Oy - M02
                Ry = data[j, i, 1] - M10 * Ox - M11 * Oy - M12
                B.append(Rx * M00 + Ry * M01)
                B.append(Rx * M10 + Ry * M11)
                A.append((M00**2 + M10 * M01, M01 * M00 + M11 * M01))
                A.append((M00 * M10 + M10 * M11, M01 * M10 + M11**2))
    A = np.array(A)
    B = np.array(B)
    t0 = np.linalg.inv(A.T @ A) @ A.T @ B

    # Construct the translation matrix
    translation = np.array([[1, 0, t0[0]], [0, 1, t0[1]], [0, 0, 1]])

    # Apply the translation
    matrix = matrix @ translation

    # Return the matrix
    return matrix


def construct_model(matrix, P0):
    # Get the initial angle
    a = np.radians(P0[0, 2])

    # Create the rotation matrix
    R = Rotation.from_euler("z", a).as_matrix()

    # Rotate the matrices
    matrix = matrix @ R

    # Get the translations
    dx = matrix[:, 0, 2]
    dy = matrix[:, 1, 2]

    # Get the rotation component
    a = np.degrees(np.arctan2(matrix[:, 1, 0], matrix[:, 0, 0]))
    b = P0[:, 3]
    c = P0[:, 4]

    # Return the model
    return np.stack([dx, dy, a, b, c], axis=1)


def track_first_and_last(projections, data, mask, octave, rebin_factor, min_samples):
    """
    Track features across the first and last images if they are around 180 degrees apart

    """

    # Function to flip coordinates
    def flip_coordinate(x):
        return np.array((1 - x[0], x[1]))

    # Get the image size (reversed to be X, Y)
    image_size = np.array(projections.shape[1:])[None, ::-1]

    # Get the first image and flipped last image
    first_and_last_images = np.zeros((2, projections.shape[1], projections.shape[1]))
    first_and_last_images[0] = projections[0]
    first_and_last_images[1] = np.flip(projections[-1], axis=1)

    # Extract the image features
    features = extract_features(first_and_last_images, rebin_factor, threads=1)

    # Find matching features and compute initial transform between images
    _, match_list = find_matching_features(features, min_samples)

    # Creat th new data matrix
    data2, mask2, octave2 = construct_data_matrix(features, match_list)

    # Loop through all the found features
    for j in range(data2.shape[1]):
        # Get the coordinates on the first and last images
        x_0 = data2[0, j]
        x_n = flip_coordinate(data2[1, j])

        # Compute the distance from the current point to each point on the
        # first and last images in the data matrix. We scale by the image size
        # because we want to match the points as being closer than 1 pixel
        d_0 = np.sqrt(
            np.sum(((x_0[None, :] - data[0, :, :]) * image_size) ** 2, axis=1)
        )
        d_n = np.sqrt(
            np.sum(((x_n[None, :] - data[-1, :, :]) * image_size) ** 2, axis=1)
        )

        # Select the points on the first and last images closest to the current point
        octave_mask = octave == octave2[j]
        select_0 = mask[0, :] & octave_mask & (d_0 < 1)  # Closer than 1 pixel
        select_n = mask[-1, :] & octave_mask & (d_n < 1)  # Closer than 1 pixel
        index_0 = np.where(select_0)[0][:1]
        index_n = np.where(select_n)[0][:1]

        # Assign the point on the last image
        data[-1, index_0] = x_n
        mask[-1, index_0] = 1

        # Assign the point on the first image
        data[0, index_n] = x_0
        mask[0, index_n] = 1

    # Count how many we have set
    print(
        "Matched %d features on first and last image"
        % (np.count_nonzero(mask[0, :] & mask[-1, :]))
    )

    # Return the data matrix, mask and octave data
    return data, mask, octave


def track_stack(
    projections,
    P,
    rebin_factor=8,
    min_samples=4,
    threads=1,
):
    """
    Do the alignment

    """

    def rescale(a):
        s1 = 1 / (np.max(a) - np.min(a))
        s0 = -s1 * a.min()
        return s0 + s1 * a

    def angular_difference_180(a, b):
        return np.abs(
            np.degrees(np.arccos(np.cos(np.radians(a) - np.radians(b)))) - 180
        )

    # Rebin the projections to a smaller size. We do this for two reasons.
    # First of all, the SIFT algorithm picks out too much noise if we do at at
    # full size. Experience shows that rebinning 8 times works better.
    # Secondly, it is much faster for the initial rounds of alignment to rebin
    # in this way. We also rescale the data so that the pixel values are
    # floating point values between 0 and 1 because the SIFT algorithm expects
    # the data like this and will not work well otherwise.
    rebinned_projections = rescale(rebin_stack(projections, rebin_factor))

    # Get indexes for swapping between angle and projection orderings
    angle_ordered_indexes = np.argsort(P[:, 4])
    reverted_order_indexes = np.argsort(angle_ordered_indexes)

    # Reorder rebinned projections and the transforms by angle
    rebinned_projections = rebinned_projections[angle_ordered_indexes]
    P = P[angle_ordered_indexes, ...]

    # Extract the image features
    print("entering critical region")
    features = extract_features(rebinned_projections, rebin_factor, threads=threads)
    print("leaving critical region")

    # Find matching features and compute initial transform between images
    matrix, match_list = find_matching_features(features, min_samples)

    # Construct data matrix. This is a FxPx2 matrix containing the coordinates
    # of all points on all frames. The mask is a FxP matrix showing whether the
    # point has been measured on that frame. This is a more convenient
    # representation for performing the refinement.
    data, mask, octave = construct_data_matrix(features, match_list)

    # Try to track features across the end of the scan
    if len(P) > 2 and angular_difference_180(P[0, 4], P[-1, 4]) < 10:
        data, mask, octave = track_first_and_last(
            rebinned_projections, data, mask, octave, rebin_factor, min_samples
        )

    # Recentre the points around the origin. This calculates the optimal matrix
    # that puts the points around the origin on each image.
    matrix = recentre_points(data, mask, matrix, origin=(0.5, 0.5))

    # Construct the model parameters
    P = construct_model(matrix, P)

    # Return contours and the model parameters in the original order
    return (
        data[reverted_order_indexes, ...],
        mask[reverted_order_indexes, ...],
        octave,
        P[reverted_order_indexes, ...],
    )


def _track(
    projections_in: str,
    model_in: str,
    model_out: str,
    contours_out: str,
    threads: int,
):
    """
    Do the alignment

    """

    def read_projections(filename):
        print("Reading projections from %s" % filename)
        return mrcfile.mmap(filename).data

    def read_model(filename) -> dict:
        print("Reading model from %s" % filename)
        return yaml.safe_load(open(filename, "r"))

    def write_model(model, filename):
        print("Writing model to %s" % filename)
        yaml.safe_dump(model, open(filename, "w"), default_flow_style=None)

    def write_contours(filename, data, mask, octave):
        print("Writing contours to %s" % filename)
        np.savez(open(filename, "wb"), data=data, mask=mask, octave=octave)

    # Set random seed
    np.random.seed(0)

    # Read the projections
    projections = read_projections(projections_in)

    # Read the model
    model = read_model(model_in)

    # Read the initial model and convert degrees to radians for use here
    P = np.array(model["transform"], dtype=float)

    # Extract some contours
    data, mask, octave, P = track_stack(projections, P, threads=threads)

    # Update the model and convert back to degrees
    model["transform"] = P.tolist()

    # Write the model to file
    write_model(model, model_out)

    # Write the contours to file
    write_contours(contours_out, data, mask, octave)
