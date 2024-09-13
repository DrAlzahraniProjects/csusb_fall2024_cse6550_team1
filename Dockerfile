# Stage 1: Mamba Stage
# Use a base image with Python and necessary dependencies
FROM python:3.12-slim AS mamba-stage

# Set environment variables
ENV LANG=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

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

# Install Miniforge (which includes Mamba)
RUN curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh" && \
    bash Miniforge3-$(uname)-$(uname -m).sh -b -p /opt/conda && \
    rm Miniforge3-$(uname)-$(uname -m).sh

# Add Conda to the PATH environment variable
ENV PATH="/opt/conda/bin:$PATH"

# Copy the environment.yml file
WORKDIR /app
COPY environment.yml /app/environment.yml

# Create a Conda environment using Mamba
RUN conda install -n base conda-libmamba-solver && conda config --set solver libmamba && \
    mamba env create -f /app/environment.yml

# Stage 2: Final Stage
FROM python:3.12-slim

# Set environment variables
ENV LANG=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

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

# Copy Conda installation from the mamba-stage
COPY --from=mamba-stage /opt/conda /opt/conda
COPY --from=mamba-stage /app /app

# Add Conda to the PATH environment variable
ENV PATH="/opt/conda/bin:$PATH"

# Activate the environment for subsequent commands
SHELL ["mamba", "run", "-n", "myenv", "/bin/bash", "-c"]

# Set the working directory
WORKDIR /app

# Copy the requirements.txt file to the working directory
COPY requirements.txt /app/requirements.txt

# Install pip packages from requirements.txt (if needed)
# RUN pip install -r /app/requirements.txt

# Copy the rest of the application code
COPY . /app

# Expose ports
EXPOSE 5001

# Set the default command to run Streamlit
CMD ["mamba", "run", "-n", "myenv", "streamlit", "run", "app.py", "--server.port=5001"]
