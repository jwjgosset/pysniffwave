# pysniffwave library

Earthworm has no utility for logging time series statistics (ex: latencies) which is a key element for tracking the performance of the network and data centre infrastructure.  After exchanges with the USGS, it was determined the "latency_mon" isn't meant for such purpose and does not work with Linux systems and "sniffwave" does monitor latency but shouldn't be considered reliable for logging.

**sniffwave** is the only option at this stage for monitoring latency but needs to be converted into a more reliable utility for constant logging.  Initial manual tests showed that sniffwave can hang quite easily with any alteration of the ring it is listening too.

This project has intention of a watchdog to sniffwave with ability to do multiple tasks with the messages it is receiving (threaded).  It initiates a thread listening to sniffwave messages and one or more thread for workers which each associated queues.  At the time of writting this, workers are:

1. PrintWorker = simply print raw decoded dictionary to screen
2. SQLWorker = store information into a database.  Note, be carefull of using this for large amount streams.  This would be more meant for single station statistics.
3. HDFWorker = store information in hourly HDF5 files.  Note, HDF5 prevents reading of files being written.  In other words, the current hour can not be read.

Note: currently the only Worker being used as part of the utility is the HDFWorker.  The others were used for testing but still work and can be used/altered for other projects.

## Installation

With anaconda, you can simply install the package using:

```bash
pip install .
```

within the conda environment.

However, for prefer to run these in operation using virtualenv and ansible.  The following packages must be installed (RHEL7)

* python3-pip
* python3-devel
* python3-virtualenv
* hdf5
* hdf5-devel

And then through pip, install the required packages.

```bash
# Create a virtual environment
python3 -m virtualenv venv
# Enter the virtual environment
source venv/bin/activate
# Install libraries compatibly for HDF5
pip install numpy==1.14.5 cython pkgconfig
# Install pip package and dependencies
pip install .
```

## Sample systemd

Below is an example systemd for sniffwave.  You'll notice that it does require the earthworm environment to be installed since it sources its environment variables.

The bellow example uses the "INST_GSC" institute ID, writes log information for WAVE_RING under /data/sniffwave, and restarts the service every 30 seconds on failure up to a maximum of 5 times.

```text
[Unit]
Description=Sniffwave logging
After=network.target

[Service]
User=ew
Group=efs
Environment=EW_INSTALL_INSTALLATION=INST_GSC
ExecStart=/bin/bash -c "source /opt/earthworm/run_working/bin/ew_linux.bash && /opt/earthworm/pysniffwave/venv/bin/sniffwave_logger -d /data/sniffwave WAVE_RING"
Restart=always
RestartSec=30
StartLimitBurst=5
StartLimitInterval=200

[Install]
WantedBy=multi-user.target
```

## Utility

HDF5 logger utility

```bash
usage: sniffwave_logger [-h] [-v] [-d DIRECTORY] [-t TIMEOUT] [-m MAX_LINES]
                        [-M MAX_FAILS]
                        cmd_args [cmd_args ...]

Run create origin script

positional arguments:
  cmd_args              Command arguments to send to sniffave (ex:
                        "WAVE_RING"). See "sniffwave" for more information.

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Verbosity
  -d DIRECTORY, --directory DIRECTORY
                        Directory to store HDF5 archive (default: /nrn/home/NR
                        N/chblais/Documents/Projects/eew/sniffwave)
  -t TIMEOUT, --timeout TIMEOUT
                        Timeout condition (s) for the HDF queue (default: 10)
  -m MAX_LINES, --max-lines MAX_LINES
                        Max amount of line to process (-1 for infinite)
                        (default: -1)
  -M MAX_FAILS, --max-fails MAX_FAILS
                        Max amount of allowed sniffwave fails (-1 for
                        infinite) (default: 10)
```
