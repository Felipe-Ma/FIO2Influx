import subprocess
import json
from influxdb_client import InfluxDBClient, Point, WritePrecision

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
    #write_api = client.write_api(write_options=WritePrecision.NS)
    write_api = client.write_api(write_options=WriteOptions(batch_size=1))


    for job in fio_result['jobs']:
        point = Point("fio") \
            .tag("jobname", job['jobname']) \
            .field("read_bw", job['read']['bw']) \
            .field("read_iops", job['read']['iops']) \
            .field("write_bw", job['write']['bw']) \
            .field("write_iops", job['write']['iops'])

        write_api.write(bucket=db_name, org=org, record=point)

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
