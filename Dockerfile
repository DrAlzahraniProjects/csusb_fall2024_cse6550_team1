# Use the official Ubuntu image as a parent image
FROM ubuntu:latest

# Set environment variables
ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies including wget, curl, and bzip2
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    wget \
    bzip2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Miniconda and Mamba
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /miniconda.sh && \
    bash /miniconda.sh -b -p /opt/conda && \
    rm /miniconda.sh && \
    /opt/conda/bin/conda install -n base -c conda-forge mamba -y && \
    /opt/conda/bin/conda clean -a -y

# Add Conda to the PATH environment variable
ENV PATH="/opt/conda/bin:$PATH"

# Set the working directory
WORKDIR /app

# Copy the environment.yml and requirements.txt files to the working directory
COPY enviroment.yml /app/enviroment.yml
COPY requirements.txt /app/requirements.txt

# Create a Conda environment using Mamba and install Python packages from environment.yml
RUN mamba env create -f /app/enviroment.yml

# Activate the environment for subsequent commands
SHELL ["conda", "run", "-n", "myenv", "/bin/bash", "-c"]

# Install pip packages from requirements.txt
RUN pip install -r /app/requirements.txt

# Copy the rest of the application code
COPY . /app

# Expose ports
EXPOSE 5001

# Set the default command to run Streamlit
CMD ["conda", "run", "-n", "myenv", "streamlit", "run", "app.py", "--server.port=5001"]
