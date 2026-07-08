# dragonET: Pillar Reconstruction Pipeline

This document provides a usage guide for the dragonET command line programs to perform pillar reconstruction.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Detailed Workflow](#detailed-workflow)
- [Command Line Programs](#command-line-programs)
  - [Main Workflow Programs](#main-workflow-programs)
  - [Contour Operations](#contour-operations)
  - [Stack Operations](#stack-operations)
  - [Volume Operations](#volume-operations)
- [Troubleshooting](#troubleshooting)

## Installation

In order to install dragonET first ensure that uv is installed by running `uv` in the terminal. If it is not, please install uv by following these
instructions [here](https://docs.astral.sh/uv/getting-started/installation/).

Now clone the repository from github and install as follows:

```bash
# First clone the repository onto your machine
git clone https://github.com/rosalindfranklininstitute/dragonET.git

# Change directory into the dragonET repository
cd dragonET

# Now we setup a virtual environment with uv
uv venv

# Now source the virtual environment to access the dragonET commands
source .venv/bin/activate

# We can now install the package as follows
uv pip install .[napari] --torch-backend auto

# Verify that the dragonET commands are now accessible
dragonET new --help
```

## Quick Start

To quickly process your data, here is a minimal workflow:

```bash
# 1. Import your data
dragonET new -p projections.mrc -a angles.rawtlt

# 2. Track features automatically
dragonET track -p projections.mrc --model_in initial_model.yaml

# 3. Refine the geometry model
dragonET refine --contours contours.npz --model_in initial_model.yaml --fix bc

# 4. Reconstruct the volume
dragonET reconstruct -p projections.mrc -m refined_model.yaml
```

This will produce a reconstructed volume in `volume.mrc`.

## Automated Workflow

```bash
# Run the complete pipeline with a single command
dragonET run -p projections.mrc -a angles.rawtlt -f 8
```

This single command performs all the necessary steps:
- Data import and initial model creation
- Feature tracking across images
- Geometric model refinement (two passes)
- Stack rebinning and alignment
- Tomographic reconstruction
- Creates an `output` directory with all results

This will create an `output` directory containing:
- `initial_model.yaml`: Initial geometric model
- `tracked_model.yaml` and `tracked_contours.npz`: Results from feature tracking
- `refined_model_fix_bc.yaml` and `refined_model_fix_c.yaml`: Refined geometric models
- `volume_fix_bc.mrc` and `volume_fix_c.mrc`: Reconstructed volumes
- Various aligned stacks for inspection
- The output will be binned by 8 to enable faster output. Set this to 1 or omit for highest resolution.

If you don't have an angles.rawtlt file, you can also omit this argument and
the angles will be calculated for you. by inferring from the projections by
reading the projections header, if available, or by assuming a ±90 tilt range

## Typical Workflow

The typical workflow for pillar reconstruction with dragonET follows these steps:

1. `dragonET new` - Import the initial model
2. `dragonET track` - Find features across images
3. `dragonET refine` - Refine the geometric model
4. `dragonET stack rebin` - Rebin the stack prior to performing reconstruction
5. `dragonET stack transform` - Create an aligned stack for inspection
6. `dragonET reconstruct` - Reconstuct the initial volume
7. `dragonET volume select_sample_axis` - Align the pillar axis with the volume
8. `dragonET reconstruct` - Reconstruct the volume with the aligned pillar axis

If the automated alignment does not work well, it may be necessary to perform
manual feature picking. This can be done as follows:

9. `dragonET contours pick` - Manually pick features across images
10. `dragonET refine` - Refine the geometric model.

Then the same reconstruction steps can be applied to the manually picked model.

## Detailed Workflow

This section provides a step-by-step guide through the complete pillar reconstruction workflow, matching the steps outlined above.

### Step 1: Import Experimental Data

**Command:** `dragonET new`

The first step imports your projection images and tilt angles into the dragonET workflow:

```bash
dragonET new -p /path/to/projections.mrc -a angles.rawtlt
```

**Output:** `initial_model.yaml`

**Details:**
- Creates an initial geometric model describing your experimental setup
- The model contains no offsets or rotations unless a global rotation is specified
- If you know that the tilt axis is offset by a certain amount (for example 90 degrees) you should set the global rotation here
- This YAML file serves as the foundation for all subsequent processing steps

**Notes:**
- You may not have an angles.rawtlt file available so you may need to generate
  one yourself. This can be done using the `dragonET generate_angles -p
  /path/to/projections.mrc` command.

### Step 2: Feature Tracking

**Command:** `dragonET track`

Automatically extract and track features across all projection images:

```bash
dragonET track -p /path/to/projections.mrc --model_in initial_model.yaml
```

**Output:** `contours.npz` and `tracked_model.yaml`

**Details:**
- Uses SIFT feature detection to identify distinctive points in each image
- Matches features between adjacent images using RANSAC-based outlier rejection
- Calculates transformations between images and filters inconsistent features
- `contours.npz`: Contains extracted feature positions and correspondences
- `tracked_model.yaml`: Initial geometric model with x/y translations and in-plane rotations

**Note:** The tracked model is useful for visualization but typically requires refinement before reconstruction.

### Step 3: Model Refinement

**Command:** `dragonET refine`

Refine the geometric model using the tracked features:

```bash
# First refinement pass - refine translations and in-plane rotations
dragonET refine --contours contours.npz --model_in initial_model.yaml --fix bc
```

**Output:** `refined_model.yaml`

**Details:**
- Uses non-linear least squares optimization to refine the geometric model
- `--fix bc`: Fixes out-of-plane rotations (b) and tilt angles (c), refining only translations and in-plane rotations
- It is often better to use the `initial_model.yaml` file than the `tracked_model.yaml` file

For improved accuracy, run a second refinement allowing optimisation of out-of-plane rotations:

```bash
# Second refinement pass - allow refinement of out-of-plane rotations
dragonET refine --contours contours.npz --model_in refined_model.yaml --fix c --model_out refined_model_c.yaml
```

**Output:** `refined_model_c.yaml`

**Details:**
- `--fix c`: Only fixes tilt angles, allowing out-of-plane rotations to be refined
- Specify `--model_out` to preserve the intermediate `refined_model.yaml`

### Step 4: Tomographic Reconstruction

**Command:** `dragonET reconstruct`

Perform the tomographic reconstruction:

```bash
dragonET reconstruct -p /path/to/projections.mrc -m refined_model_c.yaml
```

**Output:** `volume.mrc`

**Details:**
- Uses the refined geometric model to reconstruct the 3D volume
- Default output size matches input projection dimensions (e.g., 4096×4096×4096 for 4096×4096 images)
- Supports GPU acceleration for faster computation

### Step 5: Pillar Axis Alignment (Optional)

**Command:** `dragonET volume select_sample_axis`

Interactively align the pillar axis with volume axes:

```bash
dragonET volume select_sample_axis -v volume.mrc -i refined_model_c.yaml -o realigned_model.yaml
```

**Output:** `realigned_model.yaml`

**Interactive Process:**
1. Napari viewer opens with your reconstructed volume
2. Create a new points layer
3. Navigate to the first slice where the pillar is visible
4. Add a point at the center of the pillar cross-section
5. Navigate to the last slice where the pillar is visible
6. Add a second point at the center of the pillar cross-section
7. The line connecting these points defines the pillar axis
8. Save to create a rotation that aligns this axis with the volume axes

### Step 6: Final Reconstruction (Optional)

**Command:** `dragonET reconstruct`

Reconstruct with the aligned pillar axis:

```bash
dragonET reconstruct -p /path/to/projections.mrc -m realigned_model.yaml -v realigned_volume.mrc
```

**Output:** `realigned_volume.mrc`

**Optimization Tip:**
Reduce volume size to improve signal-to-noise ratio by focusing on the pillar region:

```bash
dragonET reconstruct -p /path/to/projections.mrc -m realigned_model.yaml -v realigned_volume.mrc --volume_shape=2048,4096,2048
```

This creates a tighter bounding box around the pillar, excluding vacuum regions.

### Alternative Workflow: Manual Feature Picking

If the automated feature tracking (Step 2) does not produce satisfactory results, you can manually pick features using the following alternative workflow:

#### Step 2-Alt: Manual Feature Picking

**Command:** `dragonET contours pick`

Manually select fiducial markers across projection images:

```bash
dragonET contours pick -p /path/to/projections.mrc -o manually_picked_contours.npz
```

**Output:** `manually_picked_contours.npz`

**Interactive Process:**
1. Napari viewer opens with your projection stack
2. Navigate through images and identify distinctive features (e.g., spots of redeposition)
3. Click to place markers at feature locations
4. Features should be visible in multiple consecutive images for best results
5. Save when complete - this creates a contours file with your manual picks

**Tips for Manual Picking:**
- Pick 10-20 well-distributed features per image
- Choose high-contrast features that are easy to identify
- Features should be spread across the field of view
- Avoid picking features near image edges

#### Step 3-Alt: Refinement with Manual Contours

**Command:** `dragonET refine`

Refine the geometric model using manually picked features:

```bash
# First refinement pass with manual contours
dragonET refine --contours manually_picked_contours.npz --model_in initial_model.yaml --fix bc --model_out manually_refined_model.yaml
```

**Output:** `manually_refined_model.yaml`

**Details:**
- Uses the same refinement algorithm as the automated workflow
- Typically produces more accurate results when automated tracking fails
- May require fewer refinement iterations than automated tracking

For improved accuracy, run a second refinement:

```bash
# Second refinement pass allowing tilt angle optimization
dragonET refine --contours manually_picked_contours.npz --model_in manually_refined_model.yaml --fix c --model_out manually_refined_model_c.yaml
```

**Output:** `manually_refined_model_c.yaml`

#### Step 4-Alt: Reconstruction with Manual Alignment

**Command:** `dragonET reconstruct`

Perform reconstruction using the manually refined model:

```bash
dragonET reconstruct -p /path/to/projections.mrc -m manually_refined_model_c.yaml -v manual_reconstruction.mrc
```

**Output:** `manual_reconstruction.mrc`

**When to Use Manual Picking:**
- Low-contrast samples where automated feature detection fails
- Samples with distinctive fiducial markers (e.g., gold beads)
- Cases where automated tracking produces inconsistent results
- When higher precision alignment is required

### Step 7: Stack Rebinning (Optional)

**Command:** `dragonET stack rebin`

Reduce projection stack resolution for faster processing or memory constraints:

```bash
dragonET stack rebin -i /path/to/projections.mrc -o rebinned_projections.mrc -f 2
```

**Output:** `rebinned_projections.mrc` (half resolution)

**Use Cases:**
- Quick preliminary reconstruction
- Memory-limited systems
- Testing workflow parameters
- Large datasets where full resolution isn't needed

### Step 8: Stack Transformation (Optional)

**Command:** `dragonET stack transform`

Apply geometric transformations to create an aligned stack for inspection:

```bash
dragonET stack transform -i /path/to/projections.mrc -o aligned_stack.mrc -m refined_model_c.yaml
```

**Output:** `aligned_stack.mrc`

**Purposes:**
- Visual quality control of alignment
- Manual inspection of feature tracking results
- Debugging alignment issues
- Creating aligned stacks for other analysis tools

## Complete Workflow Summary

### Automated Workflow

```
Projections + Angles
        ↓
        dragonET new → Initial Model
        ↓
        dragonET track → Tracked Model + Contours
        ↓
        dragonET refine → Refined Model
        ↓
        dragonET stack rebin → Rebinned Stack (optional)
        ↓
        dragonET stack transform → Aligned Stack (optional)
        ↓
        dragonET reconstruct → Volume
        ↓
        dragonET volume select_sample_axis → Aligned Model
        ↓
        dragonET reconstruct → Final Volume
```

### Manual Workflow (Alternative)

```
Projections + Angles
        ↓
        dragonET new → Initial Model
        ↓
        dragonET contours pick → Manual Contours
        ↓
        dragonET refine → Manually Refined Model
        ↓
        dragonET stack rebin → Rebinned Stack (optional)
        ↓
        dragonET stack transform → Aligned Stack (optional)
        ↓
        dragonET reconstruct → Manual Reconstruction
```

# Command Line Programs

All dragonET command line programs follow a similar naming convention and can be accessed using the `dragonET --help` syntax for list of available commands and command groups. You can use the `--help` command to get further information about any subcommands too, for example `dragonET contours --help` will list the available contours commands and `dragonET contours pick --help` will list the available arguments.

## Main Workflow Programs

These are the core programs used in the typical reconstruction workflow:

### dragonET run

**Description:** Run the complete automated pipeline from data import to reconstruction

**Usage:**
```bash
dragonET run -p PROJECTIONS [-a ANGLES] [-r GLOBAL_ROTATION] [-f REBIN_FACTOR] [--device DEVICE] [--processes PROCESSES]
```

**Arguments:**
- `-p, --projections`: The projection images (required)
- `-a, --angles`: The angles in the rawtlt file (optional, will be generated if not provided)
- `-r, --global-rotation`: The global in plane rotation (degrees) (default: 0)
- `-f, --rebin-factor`: The rebin factor (must be a power of 2) (default: 1)
- `--device`: The device settings to use (choices: "gpu", "gpu_and_host", "host") (default: "gpu")
- `--processes`: Number of processes to perform tracking with (default: 1)

**Details:**
- Automates the complete workflow: data import, feature tracking, model refinement, and reconstruction
- Creates an `output` directory with all intermediate and final results
- Generates angles if not provided using `dragonET generate_angles`
- Performs two refinement passes (fix=bc and fix=c)
- Creates aligned stacks and volumes for both refinement levels
- Useful for quick processing and testing of new datasets

### dragonET new

**Description:** Import experimental description and create initial model

**Usage:**
```bash
dragonET new -p PROJECTIONS -a ANGLES [-m MODEL] [-r GLOBAL_ROTATION]
```

**Arguments:**
- `-p, --projections`: The projection images (required)
- `-a, --angles`: The angles in the rawtlt file (required)
- `-m, --model`: A YAML file describing the initial model (default: "initial_model.yaml")
- `-r, --global-rotation`: The global in plane rotation (degrees) (default: 0)

### dragonET track

**Description:** Automatically track features across projection images using SIFT

**Usage:**
```bash
dragonET track -p PROJECTIONS --model_in MODEL_IN [--model_out MODEL_OUT] [--contours CONTOURS] [--processes PROCESSES]
```

**Arguments:**
- `-p`: The filename for the projection images (required)
- `--model_in`: A file describing the initial model (required)
- `--model_out`: A file describing the output model (default: "tracked_model.yaml")
- `--contours`: A binary file describing the contours (default: "contours.npz")
- `--processes`: Number of processes to perform tracking with (default: 1)

### dragonET align

**Description:** Perform rough alignment of projection images using multiple correlation

**Usage:**
```bash
dragonET align -p PROJECTIONS --model_in MODEL_IN [--model_out MODEL_OUT] [--reference_image REFERENCE_IMAGE] [--max_shift MAX_SHIFT] [--max_iter MAX_ITER] [--max_images MAX_IMAGES] [--device DEVICE]
```

**Arguments:**
- `-p`: The filename for the projection images (required)
- `--model_in`: A file describing the initial model (required)
- `--model_out`: A YAML file describing the refined model (default: "aligned_model.yaml")
- `--reference_image`: Set the reference image, if not set the angle closest to zero will be chosen
- `--max_shift`: Maximum normalised image shift (between 0 and 1) (default: 0.25)
- `--max_iter`: Maximum number of iterations (> 0) (default: 10)
- `--max_images`: Maximum number of images to use in multiple correlation (> 0) (default: 3)
- `--device`: The device settings to use (choices: "gpu", "cpu") (default: "gpu")

### dragonET refine

**Description:** Refine alignment model using contour information

**Usage:**
```bash
dragonET refine --contours CONTOURS --model_in MODEL_IN [--model_out MODEL_OUT] [--fix FIX] [--max_iter MAX_ITER] [--smoothness SMOOTHNESS] [--reference_image REFERENCE_IMAGE] [--plots_out PLOTS_OUT] [--info_out INFO_OUT] [-v]
```

**Arguments:**
- `--contours`: A YAML file containing contour information (required)
- `--model_in`: A file describing the initial model (required)
- `--model_out`: A YAML file describing the refined model (default: "refined_model.yaml")
- `--fix`: Fix parameters in refinement (choices: "bc", "c", "none") (default: "c")
- `--max_iter`: The maximum number of iterations to perform (default: 100)
- `--smoothness`: The smoothness regularisation parameter for angle refinement (default: 10)
- `--reference_image`: Set the reference image, if not set the angle closest to zero will be chosen
- `--plots_out`: The directory to write some plots (default: "plots")
- `--info_out`: A YAML file containing refinement information
- `-v`: Set verbose output

### dragonET project

**Description:** Generate projection images from a volume using the geometric model

**Usage:**
```bash
dragonET project -m MODEL -v VOLUME [-p PROJECTIONS] [--pixel_size PIXEL_SIZE] [--device DEVICE]
```

**Arguments:**
- `-m, --model`: A file describing the initial model (required)
- `-v, --volume`: The volume to project from (required)
- `-p, --projections`: The output projection images (default: "projections.mrc")
- `--pixel_size`: The pixel size relative to the voxel size (default: 1)
- `--device`: The device settings to use (choices: "gpu", "gpu_and_host", "host") (default: "gpu")

### dragonET reconstruct

**Description:** Perform tomographic reconstruction from aligned projections

**Usage:**
```bash
dragonET reconstruct -p PROJECTIONS -m MODEL [-v VOLUME] [-i INITIAL_VOLUME] [--volume_shape SHAPE] [--pixel_size PIXEL_SIZE] [-n NUM_ITERATIONS] [--device DEVICE]
```

**Arguments:**
- `-p, --projections`: The projection images (required)
- `-m, --model`: A file describing the initial model (required)
- `-v, --volume`: The reconstructed volume (default: "volume.mrc")
- `-i, --initial_volume`: The initial volume for reconstruction
- `--volume_shape`: The shape of the volume (format: W,H,D)
- `--pixel_size`: The pixel size relative to the voxel size (default: 1)
- `-n, --num_iterations`: The number of iterations (default: 1)
- `--device`: The device settings to use (choices: "gpu", "gpu_and_host", "host") (default: "gpu")

## Contour Operations

Programs for working with contours and fiducial markers:

### dragonET contours pick

**Description:** Manually pick fiducials from projection images

**Usage:**
```bash
dragonET contours pick -p PROJECTIONS -o CONTOURS_OUT [-i CONTOURS_IN] [-m MODEL]
```

**Arguments:**
- `-p, --projections`: The projection images (required)
- `-o, --contours_out`: Output file for picked contours (default: "contours.npz")
- `-i, --contours_in`: Input contours file
- `-m, --model`: A YAML file describing the geometry model

### dragonET contours extend

**Description:** Extend contours to additional images based on existing contour information

**Usage:**
```bash
dragonET contours extend -p PROJECTIONS --contours_in CONTOURS_IN --model_in MODEL_IN [--contours_out CONTOURS_OUT] [-s SUBSET_SIZE]
```

**Arguments:**
- `-p`: The filename for the projection images (required)
- `--contours_in`: A YAML file containing contour information (required)
- `--model_in`: A file describing the initial model (required)
- `--contours_out`: A YAML file describing the extended contours (default: "extended.npz")
- `-s, --subset_size`: The subset size for contour extension (default: 1)

### dragonET contours refine

**Description:** Refine contour positions to match features better across images

**Usage:**
```bash
dragonET contours refine -p PROJECTIONS --contours_in CONTOURS_IN --model_in MODEL_IN [--model_out MODEL_OUT] [--contours_out CONTOURS_OUT] [--num_macro_cycles NUM_MACRO_CYCLES]
```

**Arguments:**
- `-p`: The filename for the projection images (required)
- `--contours_in`: A YAML file containing contour information (required)
- `--model_in`: A file describing the initial model (required)
- `--model_out`: A file describing the output model (default: "refined_model.yaml")
- `--contours_out`: A YAML file describing the refined contours (default: "refined.npz")
- `--num_macro_cycles`: The number of macro cycles in the refinement (default: 1)

### dragonET contours triangulate

**Description:** Triangulate contour points to create 3D model points

**Usage:**
```bash
dragonET contours triangulate --contours_in CONTOURS_IN --model_in MODEL_IN [--points_out POINTS_OUT]
```

**Arguments:**
- `--contours_in`: A YAML file containing contour information (required)
- `--model_in`: A file describing the initial model (required)
- `--points_out`: Output file for triangulated points (default: "triangulated.npz")

## Stack Operations

Programs for manipulating projection stacks:

### dragonET stack rebin

**Description:** Rebin projection stack to reduce resolution

**Usage:**
```bash
dragonET stack rebin -i PROJECTIONS_IN -o PROJECTIONS_OUT -f FACTOR
```

**Arguments:**
- `-i`: The filename for the input projection images (required)
- `-o`: The filename for the output projection images (default: "rebinned.mrc")
- `-f, --factor`: The rebinning factor (default: 1)

### dragonET stack edit

**Description:** Edit projection stack by excluding specific images

**Usage:**
```bash
dragonET stack edit -i PROJECTIONS_IN -o PROJECTIONS_OUT [--exclude EXCLUDE]
```

**Arguments:**
- `-i`: The filename for the input projection images (required)
- `-o`: The filename for the output projection images (default: "edited.mrc")
- `--exclude`: Comma-separated list of image indices (zero-indexed) to exclude

### dragonET stack predict

**Description:** Predict projection images using the geometric model

**Usage:**
```bash
dragonET stack predict -i PROJECTIONS_IN -o PROJECTIONS_OUT --model_in MODEL_IN [-s SUBSET_SIZE]
```

**Arguments:**
- `-i`: The filename for the input projection images (required)
- `-o`: The filename for the output projection images (default: "predicted.mrc")
- `--model_in`: A file describing the input model (required)
- `-s, --subset_size`: The size of the subset to use to predict adjacent images (default: 1)

### dragonET stack transform

**Description:** Transform projection stack using the geometric model

**Usage:**
```bash
dragonET stack transform -i PROJECTIONS_IN -o PROJECTIONS_OUT -m MODEL_IN
```

**Arguments:**
- `-i`: The filename for the input projection images (required)
- `-o`: The filename for the output projection images (default: "transformed.mrc")
- `-m, --model`: A file describing the input model (required)

### dragonET stack rot90

**Description:** Rotate projection stack by 90 degree increments

**Usage:**
```bash
dragonET stack rot90 -i PROJECTIONS_IN -o PROJECTIONS_OUT -n NUMBER
```

**Arguments:**
- `-i`: The filename for the input projection images (required)
- `-o`: The filename for the output projection images (default: "rotated.mrc")
- `-n, --number`: The number of 90-degree rotations to apply (default: 1)

## Volume Operations

Programs for post-processing reconstructed volumes:

### dragonET volume rebin

**Description:** Rebin volume to reduce resolution

**Usage:**
```bash
dragonET volume rebin -i VOLUME_IN -o VOLUME_OUT -f FACTOR
```

**Arguments:**
- `-i`: The filename for the input volume (required)
- `-o`: The filename for the output volume (default: "rebinned.mrc")
- `-f, --factor`: The rebinning factor (default: 1)

### dragonET volume select_sample_axis

**Description:** Align pillar axis with volume axes using interactive selection

**Usage:**
```bash
dragonET volume select_sample_axis -v VOLUME -i MODEL_IN -o MODEL_OUT
```

**Arguments:**
- `-v, --volume`: The volume (required)
- `-i, --model_in`: A YAML file describing the geometry model (required)
- `-o, --model_out`: A YAML file describing the output model (default: "aligned_model.yaml")

## Troubleshooting

### Common Issues

**CUDA/GPU Issues:**
- If you encounter CUDA-related errors, try running with `--device cpu` instead of GPU.
- Make sure you have the correct PyTorch version installed for your CUDA version.

**Memory Issues:**
- Rebinning data with `dragonET stack rebin` can reduce memory requirements.

**File Format Issues:**
- Ensure input files are in the correct format (MRC for images, YAML for models).
- Check that file paths are correct and accessible.

**Napari Issues:**
- If `dragonET volume select_sample_axis` or `dragonET contours pick` fail to open Napari, make sure you have Napari installed.
- Try running with `napari --info` to check your Napari installation.

### Getting Help

For additional help:
- Use `--help` flag with any command for detailed usage.
- Check the [GitHub repository](https://github.com/rosalindfranklininstitute/dragonET) for issues and documentation.
- Report bugs and feature requests on the GitHub issue tracker.
