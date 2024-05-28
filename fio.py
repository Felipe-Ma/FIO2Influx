#!/usr/bin/env python3

import sys
import os
import time
from datetime import datetime
import textwrap
import argparse
import platform
from influxdb_client import InfluxDBClient, Point


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

def fioinput(ip, port, database, org, token, hostname):
    client = InfluxDBClient(url=f"http://{ip}:{port}", token=token, org=org)
    write_api = client.write_api()

    # Create the bucket if it doesn't exist
    create_bucket(client, database, org)

    # minimal format found here: https://www.andypeace.com/fio_minimal.html
    for line in sys.stdin:
        fullfio_data = line.split(",")
        fullfio_data = fullfio_data[0].split(";")

        # Run info
        terseversion = fullfio_data[0]
        fioversion = fullfio_data[1]
        jobname = fullfio_data[2]

        # Read IO info
        readtotalio = float(int(fullfio_data[5]) / 1024)
        readbandwidthio = float(int(fullfio_data[6]) / 1024)
        readiopsio = float(fullfio_data[7])
        readpercent = float(fullfio_data[43].strip('%'))

        # Read Submission Latency info
        rdsubmissionmin = float(fullfio_data[9])
        rdsubmissionmax = float(fullfio_data[10])
        rdsubmissionmean = float(fullfio_data[11])
        rdsubmissiondeviation = float(fullfio_data[12])

        # Read Completion Latency info
        rdcompletionmin = float(fullfio_data[13])
        rdcompletionmax = float(fullfio_data[14])
        rdcompletionmean = float(fullfio_data[15])
        rdcompletiondeviation = float(fullfio_data[16])

        # Read Total Latency info
        rdtotalmin = float(fullfio_data[37])
        rdtotalmax = float(fullfio_data[38])
        rdtotalmean = float(fullfio_data[39])
        rdtotaldeviation = float(fullfio_data[40])

        # Write IO info
        writetotalio = float(int(fullfio_data[46]) / 1024)
        writebandwidthio = float(int(fullfio_data[47]) / 1024)
        writeiopsio = float(fullfio_data[48])
        writepercent = float(fullfio_data[84].strip('%'))

        # Write Submission Latency info
        wrsubmissionmin = float(fullfio_data[50])
        wrsubmissionmax = float(fullfio_data[51])
        wrsubmissionmean = float(fullfio_data[52])
        wrsubmissiondeviation = float(fullfio_data[53])

        # Write Completion Latency info
        wrcompletionmin = float(fullfio_data[54])
        wrcompletionmax = float(fullfio_data[55])
        wrcompletionmean = float(fullfio_data[56])
        wrcompletiondeviation = float(fullfio_data[57])

        # Write Total Latency info
        wrtotalmin = float(fullfio_data[78])
        wrtotalmax = float(fullfio_data[79])
        wrtotalmean = float(fullfio_data[80])
        wrtotaldeviation = float(fullfio_data[81])

        # IO depth distribution
        iodepth01 = float(fullfio_data[92].strip('%'))
        iodepth02 = float(fullfio_data[93].strip('%'))
        iodepth04 = float(fullfio_data[94].strip('%'))
        iodepth08 = float(fullfio_data[95].strip('%'))
        iodepth16 = float(fullfio_data[96].strip('%'))
        iodepth32 = float(fullfio_data[97].strip('%'))
        iodepth64 = float(fullfio_data[98].strip('%'))

        # Block size 
        # Bandwidth / IOPS
        readblocksize = round((readbandwidthio / readiopsio) * 1024, 1) if readiopsio != 0 else 0.0
        writeblocksize = round((writebandwidthio / writeiopsio) * 1024, 1) if writeiopsio != 0 else 0.0

        # Calculate percentage of read vs write IOPS
        totaliops = readiopsio + writeiopsio
        readiopspercentage = readiopsio / totaliops
        writeiopspercentage = writeiopsio / totaliops

        # CPU Usage
        cpuuser = float(fullfio_data[87].strip('%'))
        cpusystem = float(fullfio_data[88].strip('%'))

        current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        print(f"{current_time} | Job Name: {jobname} | Read IOPS: {readiopsio} | Write IOPS: {writeiopsio} | Block(read/write): {readblocksize} / {writeblocksize}", end='\r')

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
                    "Read_IOPS": readiopsio,
                    "Read_Percentage": readpercent,
                    "Read_Total_I/O_(MB)": readtotalio,
                    "Read_bandwidth_(MB/s)": readbandwidthio,
                    "Read_Latency_Submission_min": rdsubmissionmin,
                    "Read_Latency_Submission_max": rdsubmissionmax,
                    "Read_Latency_Submission_mean": rdsubmissionmean,
                    "Read_Latency_Submission_deviation": rdsubmissiondeviation,
                    "Read_Latency_Completion_min": rdcompletionmin,
                    "Read_Latency_Completion_max": rdcompletionmax,
                    "Read_Latency_Completion_mean": rdcompletionmean,
                    "Read_Latency_Completion_deviation": rdcompletiondeviation,
                    "Read_Latency_Total_min": rdtotalmin,
                    "Read_Latency_Total_max": rdtotalmax,
                    "Read_Latency_Total_mean": rdtotalmean,
                    "Read_Latency_Total_deviation": rdtotaldeviation,
                    "Write_IOPS": writeiopsio,
                    "Write_Percentage": writepercent,
                    "Write_Latency_Submission_min": wrsubmissionmin,
                    "Write_Latency_Submission_max": wrsubmissionmax,
                    "Write_Latency_Submission_mean": wrsubmissionmean,
                    "Write_Latency_Submission_deviation": wrsubmissiondeviation,
                    "Write_Latency_Completion_min": wrcompletionmin,
                    "Write_Latency_Completion_max": wrcompletionmax,
                    "Write_Latency_Completion_mean": wrcompletionmean,
                    "Write_Latency_Completion_deviation": wrcompletiondeviation,
                    "Write_Latency_Total_min": wrtotalmin,
                    "Write_Latency_Total_max": wrtotalmax,
                    "Write_Latency_Total_mean": wrtotalmean,
                    "Write_Latency_Total_deviation": wrtotaldeviation,
                    "Write_Total_I/O_(MB)": writetotalio,
                    "Write_bandwidth_(MB/s)": writebandwidthio,
                    "Read Block Size (KB)": readblocksize,
                    "Write Block Size (KB)": writeblocksize,
                    "CPU User": cpuuser,
                    "CPU System": cpusystem,
                    "IOdepthdist01": iodepth01,
                    "IOdepthdist02": iodepth02,
                    "IOdepthdist04": iodepth04,
                    "IOdepthdist08": iodepth08,
                    "IOdepthdist16": iodepth16,
                    "IOdepthdist32": iodepth32,
                    "IOdepthdist64": iodepth64,
                    "Read_IOPS_Percentage": readiopspercentage,
                    "Write_IOPS_Percentage": writeiopspercentage
                }
            }
        ]

        write_api.write(bucket=database, record=json_body)

def main():
    parser = argparse.ArgumentParser(
        prog='fio_to_influxdb',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''\
            The following options must be added to the fio command for this script to function
                --status-interval=1
                --minimal
            Example usage:
            fio instructionfile.fio --status-interval=1 --minimal | fio_to_influxdb.py
            --
        '''))
    parser.add_argument("-ip", default='localhost', help="IP or DNS name of host running influxdb. Default is localhost", type=str)
    parser.add_argument("-port", default='8086', help="Port used to connect to influxdb. Default is 8086", type=int)
    parser.add_argument("-database", default='fio', help="Name of database created in influxdb. Default is fio", type=str)
    parser.add_argument("-org", default='Solidigm', help="Name of the InfluxDB organization. Default is solidigm", type=str)
    parser.add_argument("-token", required=True, help="InfluxDB authentication token", type=str)
    args = parser.parse_args()

    print(f"\nConnecting to influx database with the following parameters\n\
        \tIP/DNS:   {args.ip}\n\
        \tPort:     {args.port}\n\
        \tDatabase: {args.database}\n\
        \tOrg:      {args.org}\n\
        \tToken:    {args.token}\n\
        ")

    # Get OS host name
    hostname = platform.uname()[1]

    fioinput(args.ip, args.port, args.database, args.org, args.token, hostname)

    print("\n\nJob complete\n")

if __name__ == "__main__":
    main()
