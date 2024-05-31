import subprocess
import json
import os
import sys
import csv
import time

def run_fio(job_file, output_csv):
    try:
        # Check if the script is run as root
        if os.geteuid() != 0:
            print("This script must be run as root.")
            sys.exit(1)

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
                                print(f"Timestamp: {timestamp}, Sequential Read Speed: {read_speed_mb:.2f} MB/s, Completion Latency: {completion_latency:.2f} ms")
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
    job_file = '../../Downloads/fio_job.fio'  # Path to your existing FIO job file
    output_csv = 'fio_output.csv'  # Path to the output CSV file
    run_fio(job_file, output_csv)

