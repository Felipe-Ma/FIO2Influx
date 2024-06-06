
# FIOInsight

This project is used to run FIO tests and visually see performances with graphs.




## Table of Contents

1. [Deployment](#Deployment)

## Demo

Insert gif or link to demo


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

### Step7: Build the Docker Image
```bash
  docker build -t fio-insight-app .
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

#### Windows
```sh
docker run --name fio-influxdb-container --network my_network -v D:\\testfile:/testfile fio-influxdb-app

```
## FAQ

#### Question 1

Answer 1

#### Question 2

Answer 2


## Features

- Light/dark mode toggle
- Live previews
- Fullscreen mode
- Cross platform


## Installation

Install my-project with npm

```bash
  npm install my-project
  cd my-project
```
    