# Cluster File Transfer Utility

A Python package for easily transferring files and folders between local machines and remote clusters.

## Features

- Secure file transfer using SSH/SFTP
- Support for both single file and entire folder transfers


## Usage

```python
from cluster import local2cluster, login2ssh, send_file, send_folder

# Transfer a single file
local2cluster(
    localDIR="/path/to/local/directory",
    clusterDIR="/path/to/cluster/directory",
    filename="example.txt"
)

# Transfer an entire folder
local2cluster(
    localDIR="/path/to/local/directory",
    clusterDIR="/path/to/cluster/directory"
)
```

## Functions

- `login2ssh()`: Establishes SSH connection to the remote cluster
- `send_file()`: Transfers a single file to the remote cluster
- `send_folder()`: Recursively transfers a folder and its contents
- `local2cluster()`: Main function that handles both file and folder transfers

## Note

Make sure to configure your SSH credentials properly before using this utility.
