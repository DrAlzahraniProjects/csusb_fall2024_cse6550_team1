# Use the official Ubuntu image as a parent image
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

# Install Miniforge
RUN curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh" && \
    bash Miniforge3-$(uname)-$(uname -m).sh -b -p /opt/conda && \
    rm Miniforge3-$(uname)-$(uname -m).sh

# Add Conda to the PATH environment variable
ENV PATH="/opt/conda/bin:$PATH"

# Set the working directory
WORKDIR /app

# Copy the environment.yml and requirements.txt files to the working directory
COPY environment.yml /app/environment.yml
COPY requirements.txt /app/requirements.txt

# Create a Conda environment using Mamba and install Python packages from environment.yml
RUN mamba env create -f /app/environment.yml

# Activate the environment for subsequent commands
SHELL ["mamba", "run", "-n", "myenv", "/bin/bash", "-c"]

# Install pip packages from requirements.txt
# RUN pip install -r /app/requirements.txt

# Copy the rest of the application code
COPY . /app

# Expose ports
EXPOSE 5001

# Set the default command to run Streamlit
CMD ["mamba", "run", "-n", "myenv", "streamlit", "run", "app.py", "--server.port=5001"]
