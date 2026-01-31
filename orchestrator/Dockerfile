FROM python:3.10-slim

WORKDIR /opt/dagster/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    dagster \
    dagster-webserver \
    dagster-postgres \
    dagster-docker \
    minio \
    pandas \
    requests

COPY . /opt/dagster/app

RUN mkdir -p /opt/dagster/app/local_data

CMD ["dagster-webserver", "-h", "0.0.0.0", "-p", "3000"]