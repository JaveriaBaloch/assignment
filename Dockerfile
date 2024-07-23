# Use a base image with Python and essential build tools
FROM python:3.11-slim

# Set environment variables to avoid buffering issues with Python
ENV PYTHONUNBUFFERED=1

# Install system dependencies required by mysqlclient and other build tools
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    pkg-config \
    libmariadb-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Ensure gunicorn is installed
RUN pip install gunicorn

# Specify the command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:1234", "app:app"]
