FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm

RUN apt-get update \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install --yes --no-install-recommends \
        build-essential \
        libgl-dev \
        libsdl2-dev \
        pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
