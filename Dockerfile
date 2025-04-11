FROM apache/airflow:2.7.2

USER root

# Install required system packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Install Python dependencies
COPY ./app/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy application files
COPY ./app /opt/airflow/app
COPY ./dags /opt/airflow/dags

# Set environment variable so Airflow can find the app modules
ENV PYTHONPATH=/opt/airflow
