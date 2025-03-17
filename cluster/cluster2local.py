import os
from tqdm import tqdm
import argparse
import tempfile
import shutil
from cluster.login import login2ssh
import time

# Color constants
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

# Add these global variables at the top of your file
global_ssh = None
global_scp = None

def get_ssh_connection(username=None, password=None, hostname=None):
    """Get an SSH connection, reusing an existing one if available."""
    global global_ssh, global_scp
    
    # Check if we already have an active connection
    if global_ssh is not None:
        try:
            # Test if the connection is still active
            global_ssh.exec_command('echo test', timeout=5)
            print(f"{GREEN}Using existing SSH connection{RESET}")
            return global_ssh, global_scp
        except Exception:
            # Connection is no longer active, close it and create a new one
            try:
                global_scp.close()
                global_ssh.close()
            except:
                pass
            global_ssh = None
            global_scp = None
    
    # Create a new connection
    global_ssh, global_scp = login2ssh(username, password, hostname)
    return global_ssh, global_scp

def download_file(scp, localDIR, clusterDIR, filename):
    file_path_local = os.path.join(localDIR, filename)
    file_path_cluster = os.path.join(clusterDIR, filename)

    # Ensuring the local directory exists
    os.makedirs(os.path.dirname(file_path_local), exist_ok=True)

    print(f"Remote file path: {file_path_cluster}")
    print(f"Local file path: {file_path_local}")
    
    print(f"{YELLOW}Downloading {filename}...{RESET}")
    scp.get(file_path_cluster, file_path_local)
    
    print(f'{GREEN}File {filename} download complete.{RESET}')

def download_folder(ssh, scp, localDIR, clusterDIR):
    # Create a temporary directory for receiving the tgz file
    temp_dir = tempfile.mkdtemp()
    temp_archive = os.path.join(temp_dir, "archive.tgz")
    
    try:
        # Get the last folder name from the path
        folder_name = os.path.basename(clusterDIR.rstrip('/'))
        print(f"{YELLOW}Preparing remote folder for download...{RESET}")
        
        # Check directory size first to estimate progress
        size_cmd = f"du -sb {clusterDIR} | cut -f1"
        stdin, stdout, stderr = ssh.exec_command(size_cmd)
        dir_size_output = stdout.read().decode().strip()
        try:
            dir_size = int(dir_size_output)
            print(f"Remote directory size: {round(dir_size / (1024*1024), 2)} MB")
        except ValueError:
            print(f"Could not determine directory size: {dir_size_output}")
            dir_size = 0
        
        # Create tar archive on remote server with progress indication
        print(f"{YELLOW}Creating archive of {folder_name}...{RESET}")
        tar_command = f"cd {os.path.dirname(clusterDIR)} && tar -czf /tmp/temp_archive.tgz {folder_name}"
        
        # Use a progress spinner while tar is running
        stdin, stdout, stderr = ssh.exec_command(tar_command)
        
        with tqdm(total=100, desc="Creating archive", bar_format='{desc}: |{bar}| {percentage:3.0f}%') as pbar:
            while not stdout.channel.exit_status_ready():
                time.sleep(0.5)
                pbar.update(5)  # Update by a small amount to show activity
                pbar.refresh()
            
            exit_status = stdout.channel.recv_exit_status()
        
        if exit_status != 0:
            error = stderr.read().decode()
            print(f"{RED}Error creating archive: {error}{RESET}")
            raise Exception(f"Failed to create archive: {error}")
        
        # Get archive size
        stdin, stdout, stderr = ssh.exec_command("stat -c %s /tmp/temp_archive.tgz")
        archive_size = int(stdout.read().decode().strip())
        print(f"Archive size: {round(archive_size / (1024*1024), 2)} MB")
        
        # Download the archive - the progress bar is handled by our login.py progress function
        print(f"{YELLOW}Downloading archive...{RESET}")
        scp.get("/tmp/temp_archive.tgz", temp_archive)
        
        # Clean up remote temp file
        ssh.exec_command("rm /tmp/temp_archive.tgz")
        
        # Extract archive to destination with progress bar
        dest_dir = os.path.join(localDIR, folder_name)
        os.makedirs(dest_dir, exist_ok=True)
        
        print(f"{YELLOW}Extracting archive to {dest_dir}...{RESET}")
        import tarfile
        
        with tarfile.open(temp_archive, "r:gz") as tar:
            members = tar.getmembers()
            with tqdm(total=len(members), desc="Extracting files") as pbar:
                for member in members:
                    tar.extract(member, path=localDIR)
                    pbar.update(1)
        
        print(f'{GREEN}Folder {folder_name} download complete.{RESET}')
        
    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir)

def cluster2local(localDIR, clusterDIR, filename=None, username=None, password=None, hostname=None):
    # Use get_ssh_connection instead of login2ssh
    ssh, scp = get_ssh_connection(username, password, hostname)
    try:
        if filename:
            download_file(scp, localDIR, clusterDIR, filename)
        else:
            download_folder(ssh, scp, localDIR, clusterDIR)
    finally:
        # Don't close the connection here, just print completion message
        print(f'{GREEN}Operation complete.{RESET}')

# Add a new function to explicitly close the connection when needed
def close_ssh_connection():
    """Close the global SSH connection if it exists."""
    global global_ssh, global_scp
    if global_ssh is not None:
        try:
            global_scp.close()
            global_ssh.close()
            print(f"{GREEN}SSH connection closed{RESET}")
        except Exception as e:
            print(f"{RED}Error closing SSH connection: {str(e)}{RESET}")
        finally:
            global_ssh = None
            global_scp = None

def main():
    parser = argparse.ArgumentParser(description='Transfer files/folders from cluster server to local machine')
    parser.add_argument('-l', '--local_dir', required=True, help='Local directory path')
    parser.add_argument('-c', '--cluster_dir', required=True, help='Source directory path on cluster')
    parser.add_argument('-f', '--filename', help='Specific file to transfer (optional)', default=None)
    parser.add_argument('--username', help='Username for FMRIB cluster', default=None)
    parser.add_argument('--password', help='Password for FMRIB cluster', default=None)
    parser.add_argument('--host', help='Destination hostname', default='clint.fmrib.ox.ac.uk')
    
    args = parser.parse_args()
    
    try:
        cluster2local(args.local_dir, args.cluster_dir, args.filename, args.username, args.password, args.host)
    finally:
        close_ssh_connection()

if __name__ == "__main__":
    main()


