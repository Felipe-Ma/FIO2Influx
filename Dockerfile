# Use the official python image from the dockerhub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install -r requirements.txt

# Copy run_demo.py into the container
COPY run_demo.py .
# Copy golden_fio.file into the container
COPY fio_job.fio .

# Install fio
RUN apt-get update && apt-get install -y fio

# Command to run the script
CMD ["python", "run_demo.py"]

# Build the image
# docker build -t fio-demo .
# Run the container
# docker run --name fio-demo --rm fio-demo
# The rm flag is used to remove the container after it stops running


