import subprocess
import json
import os
import sys
import csv
import time
from influxdb_client import InfluxDBClient
from datetime import datetime


# Function to create a bucket if it doesn't exist
def create_bucket(client, bucket_name, org):
    try:
        buckets_api = client.buckets_api()
        org_id = client.organizations_api().find_organizations(org=org)[0].id
        bucket = buckets_api.create_bucket(bucket_name=bucket_name, org_id=org_id)
        print(f"Bucket {bucket_name} created successfully.")
    except Exception as e:
        if 'bucket already exists' in str(e).lower():
            print(f"Bucket {bucket_name} already exists.")
        else:
            raise e


def run_fio(job_file, output_csv):
    try:
        # Check if the script is run as root
        if os.geteuid() != 0:
            print("This script must be run as root.")
            sys.exit(1)

        # Create a bucket in InfluxDB
        client = InfluxDBClient(url="http://localhost:8086", token="my-token", org="Solidigm")
        create_bucket(client, "fio_results", "Solidigm")
        write_api = client.write_api()

        # Environment variable to disable output buffering
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        # Open CSV file for writing
        with open(output_csv, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'Sequential Read Speed (MB/s)', 'Completion Latency (ms)'])

            # Run the FIO job using subprocess, expecting periodic JSON output
            process = subprocess.Popen(
                ['fio', '--output-format=json', '--status-interval=1', job_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )

            # Variable to store incomplete JSON lines
            buffer = ""

            while True:
                output_line = process.stdout.readline()
                if output_line == '' and process.poll() is not None:
                    break
                if output_line:
                    buffer += output_line.strip()
                    if buffer.startswith('{') and buffer.endswith('}'):
                        try:
                            # Parse the JSON output from FIO
                            fio_output = json.loads(buffer)
                            buffer = ""  # Clear the buffer after successful JSON parsing

                            if 'jobs' in fio_output and len(fio_output['jobs']) > 0:
                                job = fio_output['jobs'][0]

                                # Extract the sequential read speeds
                                read_speed = job['read'].get('bw', 0)  # in KiB/s

                                # Extract the completion latency
                                clat = job['read'].get('clat', {})
                                completion_latency = clat.get('mean', 0) / 1000  # Convert to ms

                                # Convert to MB/s
                                read_speed_mb = read_speed / 1024

                                # Get the current timestamp
                                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

                                # Write to CSV
                                writer.writerow([timestamp, f"{read_speed_mb:.2f}", f"{completion_latency:.2f}"])

                                # Print to terminal
                                print(
                                    f"Timestamp: {timestamp}, Sequential Read Speed: {read_speed_mb:.2f} MB/s, Completion Latency: {completion_latency:.2f} ms")

                                # Write to InfluxDB
                                current_time = datetime.utcnow().isoformat()
                                json_body = [
                                    {
                                        "measurement": "FIO",
                                        "tags": {
                                            "runId": job['jobname'],
                                            "hostname": job.get('hostname', 'unknown')
                                        },
                                        "time": current_time,
                                        "fields": {
                                            "Read_Speed": read_speed_mb,
                                            "Completion_Latency": completion_latency
                                        }
                                    }
                                ]
                                write_api.write(bucket="fio_results", record=json_body)


                        except json.JSONDecodeError:
                            # Skip this line if it's not a complete JSON object
                            pass

            # Check if the process ended with an error
            if process.returncode != 0:
                stderr_output = process.stderr.read()
                print("Error running FIO job:")
                print(stderr_output)
    except Exception as e:
        print("An unexpected error occurred:")
        print(e)


if __name__ == "__main__":
    job_file = 'fio_job.fio'  # Path to your existing FIO job file
    output_csv = 'fio_output.csv'  # Path to the output CSV file
    # Create a new bucket in InfluxDB

    run_fio(job_file, output_csv)

