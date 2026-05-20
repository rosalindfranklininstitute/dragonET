# Install uv
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_SYSTEM_PYTHON=1

# Omit development dependencies
ENV UV_NO_DEV=1

# Configure the Python directory so it is consistent
ENV UV_PYTHON_INSTALL_DIR=/python

# Only use the managed Python version
ENV UV_PYTHON_PREFERENCE=only-managed

COPY . /app

WORKDIR /app

RUN apt-get update && apt-get install git --assume-yes

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  uv sync --locked --no-install-project --no-editable

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --locked --no-editable

RUN bash -c "if [ ! -d '/app/.venv' ]; then; exit 5; fi"

FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# Setup a non-root
RUN groupadd --system --gid 999 nonroot \
  && useradd --system --gid 999 --uid 999 --create-home nonrootpo

RUN mkdir /app

# Copy the Python version
COPY --from=builder /python /python

# Copy the environment, but not the source code
COPY --from=builder --chown=nonroot:nonroot /app/.venv /app/.venv

# Place executables in the environment at the front of the path
ENV PATH=/app/venv/bin:$PATH

# Use the non-root user to run our application
USER nonroot

WORKDIR /app
