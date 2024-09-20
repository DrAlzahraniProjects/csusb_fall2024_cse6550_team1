# Use Miniforge base image
FROM condaforge/mambaforge:latest

# Set environment variables
ENV LANG=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt /app/requirements.txt

# Install necessary packages through requirements.txt
RUN mamba install --yes --file requirements.txt && mamba clean --all -f -y

# Install NGINX
RUN apt-get update && apt-get install -y nginx

# Copy NGINX config
COPY config/nginx.conf /etc/nginx/nginx.conf

# Copy application files
COPY . /app

# Expose ports
# NGINX typically listens on port 80 for HTTP traffic
EXPOSE 80
# Streamlit app that runs on port 5001
EXPOSE 5001
# For Jupyter Notebook
EXPOSE 8888

# Run the Streamlit application
#ENTRYPOINT ["python"]

# shell form (/bin/bash -c) to run both service nginx start and streamlit run.
# This allows both services to start in the same container
CMD /bin/bash -c "service nginx start && streamlit run app.py --server.port=5001 --server.address=0.0.0.0"
