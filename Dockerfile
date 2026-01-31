# Use the official Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /opt/dagster/app

# Install system dependencies (git is often needed for libraries)
RUN apt-get update && apt-get install -y git

# Copy your requirements file first (to cache dependencies)
COPY requirements.txt .

# Install the Python libraries (This is the critical step!)
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the rest of your code
COPY . .

# Set the entrypoint
CMD ["dagster-daemon", "run"]
