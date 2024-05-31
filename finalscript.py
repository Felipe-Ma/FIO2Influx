import subprocess
import json
from influxdb_client import InfluxDBClient, Point, WritePrecision
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

# Function to write FIO result to InfluxDB
def write_fio_result_to_influxdb(write_api, db_name, fio_result):
    for job in fio_result['jobs']:
        hostname = job.get('hostname', 'unknown')
        jobname = job['jobname']
        current_time = datetime.utcnow().isoformat()

        read = job['read']

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
                    "Read_bandwidth_(MB/s)": read['bw']
                }
            }
        ]

        write_api.write(bucket=db_name, record=json_body)

# Function to run FIO and process output in real-time
def run_fio_and_stream_results(fio_job_file, db_name, token, org):
    client = InfluxDBClient(url="http://localhost:8086", token=token, org=org)
    create_bucket(client, db_name, org)
    write_api = client.write_api(write_options=WritePrecision.NS)

    process = subprocess.Popen(['fio', '--output-format=json', '--output=-', fio_job_file], stdout=subprocess.PIPE, text=True)

    buffer = ""
    while True:
        output = process.stdout.read(1)
        if output == '' and process.poll() is not None:
            break
        if output:
            buffer += output
            if buffer.endswith('}\n'):
                try:
                    fio_result = json.loads(buffer)
                    write_fio_result_to_influxdb(write_api, db_name, fio_result)
                    buffer = ""
                except json.JSONDecodeError:
                    continue

    write_api.__del__()  # Ensure all pending writes are flushed
    client.close()
    print("FIO result written to InfluxDB.")

# Main script
if __name__ == "__main__":
    db_name = input("Enter the database name: ")
    token = input("Enter the InfluxDB token: ")
    org = input("Enter the organization: ")
    fio_job_file = input("Enter the FIO job file path: ")

    run_fio_and_stream_results(fio_job_file, db_name, token, org)
