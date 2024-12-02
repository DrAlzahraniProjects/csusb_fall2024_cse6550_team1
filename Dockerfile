# Use Python as the base image
FROM python:3.10-slim

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set the working directory in the container
WORKDIR /app

# Import ARG and save to .ENV file
ARG GROQ
RUN echo "GROQ_API_KEY=$GROQ" > /app/.env

# Update and install necessary packages
RUN apt-get update && apt-get install -y \
	wget \
	bzip2 \
	ca-certificates \
	build-essential \
    	python3-dev \
	&& rm -rf /var/lib/apt/lists/*

# Install Mambaforge for the appropriate architecture
RUN arch=$(uname -m) && \
	if [ "${arch}" = "x86_64" ]; then \
		wget -q "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh" -O miniforge.sh; \
	elif [ "${arch}" = "aarch64" ]; then \
		wget -q "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh" -O miniforge.sh; \
	else \
		echo "Unsupported architecture: ${arch}"; \
		exit 1; \
	fi && \
	bash miniforge.sh -b -p /opt/miniforge && \
	rm miniforge.sh

# Add Mambaforge to PATH
ENV PATH=/opt/miniforge/bin:$PATH

# Create a new environment with Python 3.10
RUN mamba create -n team1_env python=3.10 -y

# Activate the new environment
SHELL ["mamba", "run", "-n", "team1_env", "/bin/bash", "-c"]

# Copy requirements.txt into the container
COPY requirements.txt /app/requirements.txt

# Install Python packages from requirements.txt
RUN mamba install --yes --file requirements.txt && mamba clean --all -f -y

# Install Python packages not on Mamba DB
RUN pip install -qU langchain_milvus langchain-groq selenium

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
	sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' && \
	apt update && \
	apt install -y google-chrome-stable

# Copy the current directory contents into the container at /app
COPY . /app

# Remove old logs that persist through previous run
RUN rm /app/logs/app.log

# Set the StreamLit ENV for configuration
ENV STREAMLIT_SERVER_BASEURLPATH=/team1
ENV STREAMLIT_SERVER_PORT=5001

# Streamlit port
EXPOSE 5001
# Jupyter Notebook port
EXPOSE 6001

# Create a Jupyter config file to disable token authentication
RUN jupyter notebook --generate-config && \
    echo "c.NotebookApp.token = ''" >> /root/.jupyter/jupyter_notebook_config.py && \
    echo "c.NotebookApp.password = ''" >> /root/.jupyter/jupyter_notebook_config.py && \
    echo "c.NotebookApp.ip = '0.0.0.0'" >> /root/.jupyter/jupyter_notebook_config.py && \
    echo "c.NotebookApp.port = 6001" >> /root/.jupyter/jupyter_notebook_config.py && \
    echo "c.NotebookApp.open_browser = False" >> /root/.jupyter/jupyter_notebook_config.py && \
	echo "c.NotebookApp.notebook_dir = '/app/jupyter'" >> /root/.jupyter/jupyter_notebook_config.py && \
    echo "c.ContentsManager.hide_globs = ['milvus']" >> /root/.jupyter/jupyter_notebook_config.py 

# Add the conda environment's bin directory to PATH
ENV PATH=/opt/miniforge/envs/team1_env/bin:$PATH

ENTRYPOINT ["python"]
CMD ["app.py"]
