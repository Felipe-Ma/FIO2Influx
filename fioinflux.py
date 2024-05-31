#!/usr/bin/env python3

import sys
import os
import time
from datetime import datetime
import textwrap
import argparse
import platform
from influxdb_client import InfluxDBClient, Point
import subprocess
import json

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

def fioinput(ip, port, database, org, token, hostname, jobfile):
    client = InfluxDBClient(url=f"http://{ip}:{port}", token=token, org=org)
    write_api = client.write_api()

    # Create the bucket if it doesn't exist
    create_bucket(client, database, org)
    env=os.environ.copy()
    env["PYTHONBUFFERED"] = "1"
    # Run the FIO job using the subprocess module
    process = subprocess.Popen(
        ["fio", "--output-format=json", "--status-interval=1", jobfile],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    # Variable to store incomplete JSON data
    buffer = ""

    while True:
        output_line = process.stdout.readline()
        if output_line == '' and process.poll() is not None:
            break
        if output_line:
            buffer += output_line
            if buffer.startswith('{') and buffer.endswith('}'):
                try:
                    # Parse the JSON data from FIO
                    fio_output = json.loads(buffer)
                    buffer = ""

                    if 'jobs' in fio_output and len(fio_output['jobs']) > 0:
                        job = fio_output['jobs'][0]
                        jobname = job['jobname']

                        # Extract Sequential Read
                        read_speed = job['read']['bw'] # in KB/s
                        #Convert to MB/s
                        read_speed = read_speed / 1024

                        # Extract Completion Latency

                        clat = job['clat_ns']['mean'] # in ns
                        # Convert to ms
                        clat = clat / 1000000

                        current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                        print(f"{current_time} | Job Name: {jobname} | Read Speed: {read_speed} MB/s | Completion Latency: {clat} ms", end='\r')
                        sys.stdout.flush()

                        json_body = [
                            {
                                "measurement": "FIO",
                                "tags": {
                                    "runId": jobname,
                                    "hostname": hostname
                                },
                                "time": current_time,
                                "fields": {
                                    "Read_Speed": read_speed,
                                    "Completion_Latency": clat
                                }
                            }
                        ]

                        write_api.write(bucket=database, record=json_body)
                except json.JSONDecodeError:
                    pass




def main():
    parser = argparse.ArgumentParser(
        prog='fio_to_influxdb',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''\
            This script runs an FIO job and sends the output to an InfluxDB database.
            The script requires the following arguments:
            -ip: IP or DNS name of host running influxdb. Default is localhost
            -port: Port used to connect to influxdb. Default is 8086
            -database: Name of database created in influxdb. Default is fio
            -org: Name of the InfluxDB organization. Default is solidigm
            -token: InfluxDB authentication token
            -jobfile: FIO job file to run
            Example usage:
            fio_to_influxdb.py -ip localhost -port 8086 -database fio -org Solidigm -token my_token -jobfile my_job.fio
            --
        '''))
    parser.add_argument("-ip", default='localhost', help="IP or DNS name of host running influxdb. Default is localhost", type=str)
    parser.add_argument("-port", default='8086', help="Port used to connect to influxdb. Default is 8086", type=int)
    parser.add_argument("-database", default='fio', help="Name of database created in influxdb. Default is fio", type=str)
    parser.add_argument("-org", default='Solidigm', help="Name of the InfluxDB organization. Default is solidigm", type=str)
    parser.add_argument("-token", required=True, help="InfluxDB authentication token", type=str)
    parser.add_argument("-jobfile", required=True, help="FIO job file to run", type=str)
    args = parser.parse_args()

    print(f"\nConnecting to influx database with the following parameters\n\
        \tIP/DNS:   {args.ip}\n\
        \tPort:     {args.port}\n\
        \tDatabase: {args.database}\n\
        \tOrg:      {args.org}\n\
        \tToken:    {args.token}\n\
        \tJob File: {args.jobfile}\n\
        ")

    # Get OS host name
    hostname = platform.uname()[1]

    fioinput(args.ip, args.port, args.database, args.org, args.token, hostname, args.jobfilei)

    print("\n\nJob complete\n")

if __name__ == "__main__":
    main()
