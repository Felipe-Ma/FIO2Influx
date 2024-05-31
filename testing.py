import subprocess
import json
import os
import sys
import time
from datetime import datetime
from influxdb_client import InfluxDBClient


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


def write_to_influxdb(db_name, org, token, job):
    client = InfluxDBClient(url="http://localhost:8086", token=token, org=org)
    create_bucket(client, db_name, org)
    write_api = client.write_api()

    hostname = job.get('hostname', 'unknown')
    jobname = job['jobname']
    current_time = datetime.utcnow().isoformat()
    read = job['read']

    clat_mean = read.get('clat', {}).get('mean', None)
    if clat_mean is not None:
        clat_mean /= 1000  # Convert to ms

    json_body = [
        {
            "measurement": "FIO",
            "tags": {
                "runId": jobname,
                "hostname": hostname
            },
            "time": current_time,
            "fields": {
                "Read_IOPS": read['iops'],
                "Read_bandwidth_(MB/s)": read['bw'],
                "Completion_Latency_ms": clat_mean if clat_mean is not None else "N/A"
            }
        }
    ]

    write_api.write(bucket=db_name, record=json_body)
    write_api.__del__()  # Explicitly call the destructor to flush all pending writes
    client.close()


def run_fio(job_file, db_name, org, token):
    try:
        if os.geteuid() != 0:
            print("This script must be run as root.")
            sys.exit(1)

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        process = subprocess.Popen(
            ['fio', '--output-format=json', '--status-interval=1', job_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )

        buffer = ""

        while True:
            output_line = process.stdout.readline()
            if output_line == '' and process.poll() is not None:
                break
            if output_line:
                buffer += output_line.strip()
                if buffer.startswith('{') and buffer.endswith('}'):
                    try:
                        fio_output = json.loads(buffer)
                        buffer = ""

                        if 'jobs' in fio_output and len(fio_output['jobs']) > 0:
                            job = fio_output['jobs'][0]

                            read_speed = job['read'].get('bw', 0)
                            clat = job['read'].get('clat', {})
                            completion_latency = clat.get('mean', 0) / 1000 if 'mean' in clat else None

                            read_speed_mb = read_speed / 1024
                            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

                            print(
                                f"Timestamp: {timestamp}, Sequential Read Speed: {read_speed_mb:.2f} MB/s, Completion Latency: {completion_latency:.2f} ms" if completion_latency is not None else f"Timestamp: {timestamp}, Sequential Read Speed: {read_speed_mb:.2f} MB/s")

                            write_to_influxdb(db_name, org, token, job)
                    except json.JSONDecodeError:
                        pass

        if process.returncode != 0:
            stderr_output = process.stderr.read()
            print("Error running FIO job:")
            print(stderr_output)
    except Exception as e:
        print("An unexpected error occurred:")
        print(e)


if __name__ == "__main__":
    db_name = input("Enter the database name: ")
    token = input("Enter the InfluxDB token: ")
    org = input("Enter the organization: ")
    fio_job_file = input("Enter the FIO job file path: ")
    run_fio(fio_job_file, db_name, org, token)
