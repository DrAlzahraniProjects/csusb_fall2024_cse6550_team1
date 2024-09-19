# Use Miniforge base image
FROM condaforge/mambaforge:latest

# Set environment variables
ENV LANG=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Copy application files
COPY . /app

# Install necessary packages through requirements.txt
RUN mamba install --yes --file requirements.txt && mamba clean --all -f -y

# Expose port
EXPOSE 5001

# Run the Streamlit application
ENTRYPOINT ["python"]
CMD ["app.py"]