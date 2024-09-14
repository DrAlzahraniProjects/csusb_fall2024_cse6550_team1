# Use the official Ubuntu image as a parent image
FROM python:3.12-slim

# Set environment variables
ENV LANG=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set the working directory
WORKDIR /app

# Install system dependencies including wget, curl, and bzip2
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    wget \
    bzip2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Miniforge
RUN curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh" && \
    bash Miniforge3-$(uname)-$(uname -m).sh -b -p /opt/conda && \
    rm Miniforge3-$(uname)-$(uname -m).sh

# Add Conda to the PATH environment variable
ENV PATH=/opt/conda/bin:$PATH

# Create a Conda environment using Mamba and install Python packages from environment.yml
RUN mamba create -n team1_env python=3.12 -y

# Copy the environment.yml and requirements.txt files to the working directory
#COPY environment.yml /app/environment.yml
COPY requirements.txt /app/requirements.txt

# Activate the environment for subsequent commands
SHELL ["mamba", "run", "-n", "team1_env", "/bin/bash", "-c"]

# Install pip packages from requirements.txt
RUN mamba install --yes --file requirements.txt && mamba clean --all -f -y

# Copy the rest of the application code
COPY . /app

# Expose ports
EXPOSE 5001

# Add the conda environment's bin directory to PATH
ENV PATH=/opt/conda/envs/team1_env/bin:$PATH

ENTRYPOINT ["python"]
CMD ["app.py"]