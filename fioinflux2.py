import subprocess
import json
from influxdb_client import InfluxDBClient
from datetime import datetime


# Function to run FIO and get the result as JSON
def run_fio(fio_job_file):
    try:
        result = subprocess.run(['fio', '--output-format=json', fio_job_file], capture_output=True, text=True)
        result.check_returncode()
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running FIO: {e}")
        return None


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
def write_to_influxdb(db_name, org, token, fio_result):
    client = InfluxDBClient(url="http://localhost:8086", token=token, org=org)
    create_bucket(client, db_name, org)
    write_api = client.write_api()

    for job in fio_result['jobs']:
        hostname = job.get('hostname', 'unknown')
        jobname = job['jobname']
        current_time = datetime.utcnow().isoformat()
        #
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

    write_api.__del__()  # Explicitly call the destructor to flush all pending writes
    client.close()
    print("FIO result written to InfluxDB.")


# Main script
if __name__ == "__main__":
    db_name = input("Enter the database name: ")
    token = input("Enter the InfluxDB token: ")
    org = input("Enter the organization: ")
    fio_job_file = input("Enter the FIO job file path: ")

    fio_result = run_fio(fio_job_file)

    if fio_result:
        write_to_influxdb(db_name, org, token, fio_result)
    else:
        print("Failed to run FIO or get the result.")
