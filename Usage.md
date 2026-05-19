# dragonET Command Line Programs User Guide

This document describes the usage of all command line programs available in the dragonET package.

## Table of Contents

- [Installation](#installation)
- [Command Line Program Reference](#command-line-program-reference)
    - [dragonET.new](#dragonetnew)
    - [dragonET.align](#dragonetalign)
    - [dragonET.project](#dragonetproject)
    - [dragonET.refine](#dragonetrefine)
    - [dragonET.reconstruct](#dragonetreconstruct)
    - [dragonET.track](#dragonettrack)
    - [dragonET.contours.extend](#dragonetcontoursextend)
    - [dragonET.contours.pick](#dragonetcontourspick)
    - [dragonET.contours.refine](#dragonetcontoursrefine)
    - [dragonET.contours.triangulate](#dragonetcontourstriangulate)
    - [dragonET.stack.edit](#dragonetstackedit)
    - [dragonET.stack.predict](#dragonetstackpredict)
    - [dragonET.stack.rebin](#dragonetstackrebin)
    - [dragonET.stack.rot90](#dragonetstackrot90)
    - [dragonET.stack.transform](#dragonetstacktransform)
    - [dragonET.volume.rebin](#dragonetvolumerebin)
    - [dragonET.volume.select_sample_axis](#dragonetvolumeselectsampleaxis)

## Installation

To install dragonET, you can need to clone the repository and install as follows:

```bash
git clone https://github.com/rosalindfranklininstitute/dragonET.git
cd dragonET
uv venv
uv pip install .
```

## Workflow

The typical workflow for electron tomography reconstruction with dragonET follows these steps:


## Command Line Reference

All dragonET command line programs follow a similar naming convention:

- **Main workflow programs**: `dragonET.new`, `dragonET.align`, `dragonET.refine`, `dragonET.reconstruct`
- **Contour operations**: `dragonET.contours.*` (pick, refine, extend, triangulate)
- **Stack operations**: `dragonET.stack.*` (edit, predict, rebin, rot90, transform)
- **Volume operations**: `dragonET.volume.*` (rebin, select_sample_axis)

Each program accepts command line arguments and typically reads input files and writes output files. Use the `--help` flag with any program to see detailed usage information:

```bash
dragonET.program_name --help
```

### dragonET.new

**Description:** Import experimental description

**Usage:**
```bash
dragonET.new -p PROJECTIONS -a ANGLES [-m MODEL] [-r GLOBAL_ROTATION]
```

**Arguments:**
- `-p, --projections`: The projection images (required)
- `-a, --angles`: The angles in the rawtlt file (required)
- `-m, --model`: A YAML file describing the initial model (default: "initial_model.yaml")
- `-r, --global_rotation`: The global in plane rotation (degrees) (default: 0)

### dragonET.align

**Description:** Do a rough alignment of the projection images

**Usage:**
```bash
dragonET.align -p PROJECTIONS --model_in MODEL_IN [--model_out MODEL_OUT] [--reference_image REFERENCE_IMAGE] [--max_shift MAX_SHIFT] [--max_iter MAX_ITER] [--max_images MAX_IMAGES] [--device DEVICE]
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

### dragonET.project

**Description:** Do the projection

**Usage:**
```bash
dragonET.project -m MODEL -v VOLUME [-p PROJECTIONS]
```

**Arguments:**
- `-m, --model`: A file describing the initial model (required)
- `-v, --volume`: The volume to project from (required)
- `-p, --projections`: The output projection images (default: "projections.mrc")

### dragonET.refine

**Description:** Refine a model to align the projection images

**Usage:**
```bash
dragonET.refine --contours CONTOURS --model_in MODEL_IN [--model_out MODEL_OUT] [--fix FIX] [--max_iter MAX_ITER] [--smoothness SMOOTHNESS] [--reference_image REFERENCE_IMAGE]
```

**Arguments:**
- `--contours`: A YAML file containing contour information (required)
- `--model_in`: A file describing the initial model (required)
- `--model_out`: A YAML file describing the refined model (default: "refined_model.yaml")
- `--fix`: Fix parameters in refinement (choices: "bc", "c", "none") (default: "c")
- `--max_iter`: The maximum number of iterations to perform (default: 100)
- `--smoothness`: The smoothness regularisation parameter for angle refinement (default: 10)
- `--reference_image`: The reference image to use

### dragonET.reconstruct

**Description:** Do the reconstruction

**Usage:**
```bash
dragonET.reconstruct -p PROJECTIONS -m MODEL [-v VOLUME]
```

**Arguments:**
- `-p, --projections`: The projection images (required)
- `-m, --model`: A file describing the initial model (required)
- `-v, --volume`: The output volume (default: "volume.mrc")

### dragonET.track

**Description:** Do a rough alignment of the projection images

**Usage:**
```bash
dragonET.track -p PROJECTIONS --model_in MODEL_IN [--model_out MODEL_OUT] [--contours CONTOURS]
```

**Arguments:**
- `-p`: The filename for the projection images (required)
- `--model_in`: A file describing the initial model (required)
- `--model_out`: A file describing the output model (default: "tracked_model.yaml")
- `--contours`: A binary file describing the contours (default: "contours.npz")

### dragonET.contours.extend

**Description:** Refine a model to align the projection images

**Usage:**
```bash
dragonET.contours.extend -p PROJECTIONS --contours_in CONTOURS_IN --model_in MODEL_IN [--contours_out CONTOURS_OUT]
```

**Arguments:**
- `-p`: The filename for the projection images (required)
- `--contours_in`: A YAML file containing contour information (required)
- `--model_in`: A file describing the initial model (required)
- `--contours_out`: A YAML file describing the extended contours (default: "extended_contours.yaml")

### dragonET.contours.pick

**Description:** Manually pick fiduccials

**Usage:**
```bash
dragonET.contours.pick -p PROJECTIONS -o CONTOURS_OUT [-i CONTOURS_IN]
```

**Arguments:**
- `-p, --projections`: The projection images (required)
- `-o, --contours_out`: A YAML file describing the picked point coordinates (default: "contours.npz")
- `-i, --contours_in`: Input contours file

### dragonET.contours.refine

**Description:** Refine the contours to match features better across images

**Usage:**
```bash
dragonET.contours.refine -p PROJECTIONS --contours_in CONTOURS_IN --model_in MODEL_IN [--contours_out CONTOURS_OUT]
```

**Arguments:**
- `-p`: The filename for the projection images (required)
- `--contours_in`: A YAML file containing contour information (required)
- `--model_in`: A file describing the initial model (required)
- `--contours_out`: A YAML file describing the refined contours (default: "refined_contours.yaml")

### dragonET.contours.triangulate

**Description:** Refine a model to align the projection images

**Usage:**
```bash
dragonET.contours.triangulate --contours_in CONTOURS_IN --model_in MODEL_IN [--points_out POINTS_OUT]
```

**Arguments:**
- `--contours_in`: A YAML file containing contour information (required)
- `--model_in`: A file describing the initial model (required)
- `--points_out`: Output file for triangulated points (default: "triangulated.npz")

### dragonET.stack.edit

**Description:** Rebin the stack

**Usage:**
```bash
dragonET.stack.edit -i PROJECTIONS_IN -o PROJECTIONS_OUT [--exclude EXCLUDE]
```

**Arguments:**
- `-i`: The filename for the input projection images (required)
- `-o`: The filename for the output projection images (default: "edited.mrc")
- `--exclude`: Comma-separated list of image indices to exclude

### dragonET.stack.predict

**Description:** Predict the stack images

**Usage:**
```bash
dragonET.stack.predict -i PROJECTIONS_IN -o PROJECTIONS_OUT --model_in MODEL_IN
```

**Arguments:**
- `-i`: The filename for the input projection images (required)
- `-o`: The filename for the output projection images (default: "predicted.mrc")
- `--model_in`: A file describing the input model (required)

### dragonET.stack.rebin

**Description:** Rebin the stack

**Usage:**
```bash
dragonET.stack.rebin -i PROJECTIONS_IN -o PROJECTIONS_OUT -f FACTOR
```

**Arguments:**
- `-i`: The filename for the input projection images (required)
- `-o`: The filename for the output projection images (default: "rebinned.mrc")
- `-f, --factor`: The rebinning factor (default: 1)

### dragonET.stack.rot90

**Description:** Rotate the stack

**Usage:**
```bash
dragonET.stack.rot90 -i PROJECTIONS_IN -o PROJECTIONS_OUT -n NUMBER
```

**Arguments:**
- `-i`: The filename for the input projection images (required)
- `-o`: The filename for the output projection images (default: "rotated.mrc")
- `-n, --number`: The number of 90-degree rotations to apply (default: 1)

### dragonET.stack.transform

**Description:** Transform the stack

**Usage:**
```bash
dragonET.stack.transform -i PROJECTIONS_IN -o PROJECTIONS_OUT -m MODEL_IN
```

**Arguments:**
- `-i`: The filename for the input projection images (required)
- `-o`: The filename for the output projection images (default: "transformed.mrc")
- `-m, --model`: A file describing the input model (required)

### dragonET.volume.rebin

**Description:** Rebin the volume

**Usage:**
```bash
dragonET.volume.rebin -i VOLUME_IN -o VOLUME_OUT -f FACTOR
```

**Arguments:**
- `-i`: The filename for the input projection images (required)
- `-o`: The filename for the output projection images (default: "rebinned.mrc")
- `-f, --factor`: The rebinning factor (default: 1)

### dragonET.volume.select_sample_axis

**Description:** Select the sample axis

**Usage:**
```bash
dragonET.volume.select_sample_axis -v VOLUME -i MODEL_IN -o MODEL_OUT
```

**Arguments:**
- `-v, --volume`: The volume (required)
- `-i, --model_in`: A YAML file describing the geometry model (required)
- `-o, --model_out`: A YAML file describing the output model (default: "aligned_model.yaml")
