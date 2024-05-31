import subprocess
import json
from influxdb_client import InfluxDBClient, Point, WritePrecision
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


# Function to write FIO result to InfluxDB
def write_to_influxdb(db_name, token, org, fio_result):
    client = InfluxDBClient(url="http://localhost:8086", token=token)
    write_api = client.write_api(write_options=WritePrecision.NS)

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

        write_api.write(bucket=db_name, org=org, record=json_body)

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
        write_to_influxdb(db_name, token, org, fio_result)
    else:
        print("Failed to run FIO or get the result.")
