
# FIOInsight

This project is used to run FIO tests and visually see performances with graphs.




## Table of Contents

1. [Demo](#Demo)
2. [Deployment](#Deployment)
3. [Usage/Examples](#Usage/Examples)
4. [Documentation](#Documentation)


## Demo

Insert gif or link to demo

### Database being updates in real-time.
![](https://github.com/Felipe-Ma/FIO2Influx/blob/main/media/demo.gif)
## Deployment

### Step1: Clone the repository
```bash
  git clone https://github.com/Felipe-Ma/FIO2Influx.git
  cd FIO2Influx
```

### Step2: Create a Test File (Windows)
```bash
  fsutil file createnew D:\testfile 104857600  # Creates a 100 MB file
```

### Step3: Create Docker Network
```bash
  docker network create my_network
```

### Step4: Pull the InfluxDB Docker Image
```bash
  docker pull influxdb:2.7.6
```

### Step5: Run the InfluxDB Container on the network created
```bash
  docker run -d --name influxdb --network my_network -p 8086:8086 influxdb:2.7.6
```

### Step6: Configure InfluxDB
1. Open your browser and go to `http://localhost:8086`
2. Follow the setup instructions to create an initial user, organization, and bucket
3. Note down the authentication token, organization name, and bucket name

### Step7: Build the Docker Image of FIOInsight
```bash
  docker build -t fio-insight-app:1.0 .
```

### Step8: Run the FIOInsight COntianer on the network created 
```bash
 docker run --name fio-insight-container --network <your_network> -v <host_directory>:/testfile \
  -e DB_NAME=<your_db_name> \
  -e INFLUXDB_TOKEN=<your_influxdb_token> \
  -e INFLUXDB_ORG=<your_influxdb_org> \
  -e FIO_JOB_FILE=<your_fio_job_file> \
  fio-insight-app:1.0
```


## Usage/Examples

### Step1: Update the FIO Job File according to the OS
#### Windows
```ini
[global]
ioengine=libaio
direct=1
runtime=60
time_based
filename=D:/testfile
size=100M

[read]
rw=read
bs=128k
numjobs=1
iodepth=256
```

#### Linux
```ini
[global]
ioengine=libaio
direct=1
runtime=432000
time_based
filename=/dev/nvme1n1

[read]
rw=read
bs=128k
numjobs=1
iodepth=256
```

### Step2: Run the Docker Container

#### Windows Usage Example
```sh
 docker run --name fio-insight-container --network my_network -v /d/testfile:/testfile \
  -e DB_NAME=Demo_Final \
  -e INFLUXDB_TOKEN=KatsyB_5cbDtXoyOn61qoTkBS-KcjdEyb32arfjI9x4DOY8kI8BWX5ex2qwPMDzcHQYu-yRDOFfwdHvzpN_c6w== \
  -e INFLUXDB_ORG=Solidigm \
  -e FIO_JOB_FILE=fio_job.fio \
  fio-insight-app:1.0
```
## Documentation

### FIO Job File
The FIO job file is used to define the parameters for the I/O test. Here is an explanation of a sample job file:

```ini
[global]
ioengine=libaio
direct=1
runtime=60
time_based
filename=dev/nvme1n1

[read]
rw=read
bs=128k
numjobs=1
iodepth=256
```

* **[global] Section:** Parameters here apply to all jobs unless overridden.
    * **ioengine=libaio:** Specifies the I/O engine. `libaio` is the Linux asynchronous I/O engine.
    * **direct=1:** Enables the direct I/O bypassomg the OS cache.
    * **runtime=64:** Sets the test duration to 64 seconds.
    * **time_based:** Ensures the test runs for the specified runtime.
    * **filename=/dev/nvme1n1:** Target device or file for the test.


* **[read] Section:** Defines a read job. 
    * **rw=read:** Specifies sequential read operations.
    * **bs=128k:** Block size for I/O operations.
    * **numjobs=1:** Number of threads/jobs.
    * **iodepth=256:** I/O depth (number of I/O operations to queue)
    
    ### Viewing Write Values
    If the job is definer with `rw=read`, only read operations will be performed, and write values will be zero. To measure write performance, you need to define a separate job or modify the existing write operations.

```ini

```
