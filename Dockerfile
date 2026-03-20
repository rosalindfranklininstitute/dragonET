FROM nvidia/cuda:12.6.0-devel-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app
COPY . .

RUN apt update
RUN apt install -y \
  git \
  libfftw3-dev \
  g++ \
  python3 \
  python3-pip \
  python-is-python3 \
  python3-venv \
  automake \
  libtool \
  fontconfig \
  mesa-utils \
  qt6-base-dev \
  libc6 \
  libxcb-cursor0 \
  libxcb-xinerama0

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install \
  numpy \
  cython \
  six \
  scipy \
  torch

WORKDIR /app
RUN export CXX=$(which g++)
RUN export CUDACXX=$(which nvcc)
RUN git submodule update --init --recursive
RUN pip install --upgrade pip
RUN pip install .
