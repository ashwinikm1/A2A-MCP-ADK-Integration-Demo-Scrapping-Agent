# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies, including Node.js for 'npx'
RUN apt-get update && \
    apt-get install -y nodejs npm && \
    # Clean up the apt cache to keep the image size down
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container at /app
# This more robustly copies the entire project context into the container.
COPY . /app

# Define environment variable to ensure logs are sent straight to Cloud Logging
ENV PYTHONUNBUFFERED 1

# Run the application when the container launches
# This command runs your agent as a Python module.
CMD ["python", "-m", "agents.search_agent"]