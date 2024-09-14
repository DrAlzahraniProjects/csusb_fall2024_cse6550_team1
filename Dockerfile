# Use the official slim Python image as a base
FROM python:3.11-slim

# Set environment variables
ENV LANG=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/opt/conda/bin:$PATH"

# Install system dependencies and Miniforge directly without keeping cache
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    wget \
    bzip2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh" \
    && bash Miniforge3-Linux-x86_64.sh -b -p /opt/conda \
    && rm Miniforge3-Linux-x86_64.sh

# Add Conda to the PATH environment variable
ENV PATH="/opt/conda/bin:$PATH"

# Set the working directory
WORKDIR /app

# Copy the environment.yml and requirements.txt files to the working directory
COPY environment.yml /app/environment.yml

# Create a Conda environment using Mamba and install Python packages from environment.yml
RUN mamba env create -f /app/environment.yml

# Change to use Bash and activate the environment
SHELL ["/bin/bash", "-c"]

# Install pip packages from requirements.txt
# RUN pip install -r /app/requirements.txt

# Copy the rest of the application code
COPY . /app

# Expose ports
EXPOSE 5001

# Run the app using the environment's Streamlit
CMD ["bash", "-c", "source activate myenv && streamlit run app.py --server.port=5001"]
