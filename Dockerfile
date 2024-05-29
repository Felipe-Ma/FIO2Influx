# Use Rocky Linux 8 as base image
FROM rockylinux/rockylinux:8

# Install fio and nvme-cli
RUN dnf install -y epel-release && \
    dnf install -y fio nvme-cli python3 python3-pip dos2unix

# Copy the Python script to the Docker image
COPY fio.py /usr/local/bin/fio.py
COPY fio_job.fio /usr/local/bin/fio_job.fio

# Convert line endings of the Python script
RUN dos2unix /usr/local/bin/fio.py

# Install the required Python packages
RUN pip3 install influxdb-client

# Set the entrypoint to fio
ENTRYPOINT ["fio"]

LABEL authors="Felipe"

