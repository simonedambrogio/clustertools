# Cluster File Transfer Utility

A Python package for easily transferring files and folders between local machines and remote clusters.

## Installation

You can install the package directly from GitHub using pip:

```bash
pip install git+https://github.com/simonedambrogio/clustertools.git
```

## Features

- Secure file transfer using SSH/SFTP
- Support for both single file and entire folder transfers
- Bidirectional transfer (local to cluster and cluster to local)
- Progress bars for file transfers
- Command-line interface for easy usage

## Usage

### Python API

```python
# Import the functions
from cluster import local2cluster, cluster2local

# Transfer from local to cluster
local2cluster(
    localDIR="/path/to/local/directory",
    clusterDIR="/path/to/cluster/directory",
    filename="example.txt"  # Optional: if not provided, transfers entire folder
)

# Transfer from cluster to local
cluster2local(
    localDIR="/path/to/local/directory",
    jalapenoDIR="/path/to/cluster/directory",
    filename="example.txt"  # Optional: if not provided, transfers entire folder
)
```

### Command Line Interface

Transfer files/folders from local to cluster:
```bash
python local2cluster.py -l /path/to/local/directory -c /path/to/cluster/directory [-f filename] [--skip-dots True/False] [--host hostname]
```

Transfer files/folders from cluster to local:
```bash
python cluster2local.py -l /path/to/local/directory -j /path/to/cluster/directory [-f filename] [--host hostname]
```

Arguments:
- `-l, --local_dir`: Local directory path
- `-c, --cluster_dir`: Destination directory path on cluster (for local2cluster)
- `-j, --jalapeno_dir`: Source directory path on cluster (for cluster2local)
- `-f, --filename`: Optional specific file to transfer
- `--host`: Optional hostname (default: clint.fmrib.ox.ac.uk)
- `--skip-dots`: Optional flag to skip files starting with "._" (local2cluster only)

## Functions

- `login2ssh(hostname='clint.fmrib.ox.ac.uk')`: Establishes SSH connection to the remote cluster
- `local2cluster(localDIR, clusterDIR, filename=None)`: Transfers files/folders from local machine to cluster
  - Supports single file or entire folder transfer
  - Shows progress bar during transfer
  - Can skip dot files (._*) optionally

- `cluster2local(localDIR, jalapenoDIR, filename=None)`: Transfers files/folders from cluster to local machine
  - Supports single file or entire folder transfer
  - Shows progress bar during transfer
  - Preserves directory structure when downloading folders

## Note

- Make sure to configure your SSH credentials properly before using this utility
- The utility will prompt for your username and password when establishing connections
- Progress bars show transfer progress for each file
- Directory structures are preserved during transfers
