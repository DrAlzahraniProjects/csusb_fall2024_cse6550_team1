# Use the official Ubuntu image as a parent image
FROM ubuntu:latest

# Set environment variables
ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies including Python, pip, and Git
RUN apt-get update && apt-get install -y \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python3 -m venv /opt/venv

# Install Python packages within the virtual environment
RUN /opt/venv/bin/pip install --upgrade pip

# List of packages to install
RUN /opt/venv/bin/pip install --no-cache-dir \
    streamlit \
    langchain \
    faiss-cpu \
    mistral \
    milvus \
	nemo-toolkit \
	nemoguardrails

# Set the working directory
WORKDIR /app

# Copy the rest of the application code
COPY . /app

# Set environment variable to use the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Expose ports
EXPOSE 5001

# Set the default command to run Streamlit
CMD ["streamlit", "run", "app.py"]
