import os
import argparse
import time
from clustertools.login import login2ssh
from tqdm import tqdm

# Color constants
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

# Add these global variables for connection reuse
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

def upload_file(ssh, scp, localDIR, clusterDIR, filename):
    """Upload a single file to the cluster."""
    file_path_local = os.path.join(localDIR, filename)
    file_path_cluster = os.path.join(clusterDIR, filename)

    # Check if file exists
    if not os.path.exists(file_path_local):
        print(f"{RED}Error: Local file {file_path_local} does not exist{RESET}")
        return False

    print(f"Local file path: {file_path_local}")
    print(f"Remote file path: {file_path_cluster}")
    
    file_size = os.path.getsize(file_path_local)
    print(f"File size: {round(file_size / (1024*1024), 2)} MB")
    
    print(f"{YELLOW}Uploading {filename}...{RESET}")
    
    # Ensure the remote directory exists
    remote_dir = os.path.dirname(file_path_cluster)
    try:
        ssh.exec_command(f"mkdir -p {remote_dir}")
    except Exception as e:
        print(f"{YELLOW}Warning creating remote directory: {str(e)}{RESET}")
    
    # Upload the file (progress bar handled by SCPClient)
    scp.put(file_path_local, file_path_cluster)
    
    print(f'{GREEN}File {filename} upload complete.{RESET}')
    return True

def upload_folder(ssh, scp, localDIR, clusterDIR, skip_dots=True):
    """Upload a folder to the cluster."""
    # Get local folder name
    folder_name = os.path.basename(os.path.normpath(localDIR))
    target_dir = os.path.join(clusterDIR, folder_name)
    
    print(f"{YELLOW}Preparing to upload folder {folder_name} to {clusterDIR}...{RESET}")
    
    # Create the target directory on the remote server - WAIT FOR COMPLETION
    stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {target_dir}")
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        error = stderr.read().decode()
        print(f"{RED}Error creating directory: {error}{RESET}")
        raise Exception(f"Failed to create directory {target_dir}: {error}")
    
    # Calculate total upload size for reporting
    total_size = 0
    file_count = 0
    file_list = []
    
    # Walk through the local directory and collect file information
    for dirpath, dirnames, filenames in os.walk(localDIR):
        for filename in filenames:
            if skip_dots and filename.startswith("._"):
                continue
                
            local_file_path = os.path.join(dirpath, filename)
            # Use a cleaner relative path construction
            rel_path = os.path.relpath(dirpath, localDIR)
            remote_dir = os.path.normpath(os.path.join(target_dir, rel_path)).replace("\\", "/")
            
            # Avoid using "./" in paths
            if rel_path == ".":
                remote_file_path = os.path.join(target_dir, filename).replace("\\", "/")
            else:
                remote_file_path = os.path.join(remote_dir, filename).replace("\\", "/")
            
            file_size = os.path.getsize(local_file_path)
            total_size += file_size
            file_count += 1
            file_list.append((local_file_path, remote_dir, remote_file_path, file_size))
    
    print(f"Found {file_count} files to upload, total size: {round(total_size / (1024*1024), 2)} MB")
    
    # Create all needed directories first in a single operation
    all_dirs = set(item[1] for item in file_list)
    remote_dirs_str = " ".join(all_dirs)
    stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {remote_dirs_str}")
    exit_status = stdout.channel.recv_exit_status()
    
    if exit_status != 0:
        error = stderr.read().decode()
        print(f"{RED}Error creating directories: {error}{RESET}")
        # Continue anyway - we'll try to create directories individually
    
    # Upload files with progress tracking
    uploaded_size = 0
    start_time = time.time()
    
    for i, (local_file_path, remote_dir, remote_file_path, file_size) in enumerate(file_list, 1):
        # Make sure the remote directory exists - wait for completion this time
        stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {remote_dir}")
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status != 0:
            error = stderr.read().decode()
            print(f"{RED}Error creating directory {remote_dir}: {error}{RESET}")
            continue
            
        # Calculate overall progress
        percent = int((uploaded_size / total_size) * 100) if total_size > 0 else 0
        elapsed = time.time() - start_time
        speed = uploaded_size / elapsed / (1024*1024) if elapsed > 0 else 0
        eta = (total_size - uploaded_size) / (speed * 1024 * 1024) if speed > 0 else 0
        eta_str = f"{int(eta / 60)}m {int(eta % 60)}s" if eta > 0 else "calculating..."
        
        # Display overall progress
        print(f"\rUploading: {i}/{file_count} files ({percent}%, {speed:.2f} MB/s, ETA: {eta_str})", end="", flush=True)
        
        try:
            # Upload the file
            filename = os.path.basename(local_file_path)
            scp.put(local_file_path, remote_file_path)
            
            # Update progress
            uploaded_size += file_size
        except Exception as e:
            print(f"\n{RED}Error uploading {local_file_path}: {str(e)}{RESET}")
            # Continue with next file
    
    # Final progress update
    elapsed = time.time() - start_time
    speed = total_size / elapsed / (1024*1024) if elapsed > 0 and uploaded_size > 0 else 0
    print(f"\r{GREEN}Upload complete: {file_count} files ({round(total_size/(1024*1024), 2)} MB) at {speed:.2f} MB/s{RESET}")
    
    return True

def local2cluster(localDIR, clusterDIR, filename=None, username=None, password=None, hostname='sftp.fmrib.ox.ac.uk', skip_dots=True):
    """Transfer files from local machine to cluster server."""
    # Use get_ssh_connection to reuse existing connections
    ssh, scp = get_ssh_connection(username, password, hostname)
    
    try:
        if filename:
            upload_file(ssh, scp, localDIR, clusterDIR, filename)
        else:
            upload_folder(ssh, scp, localDIR, clusterDIR, skip_dots)
    finally:
        # Don't close the connection here, just print completion message
        print(f'{GREEN}Operation complete.{RESET}')

# Add a function to explicitly close the connection when needed
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
    parser = argparse.ArgumentParser(description='Transfer files/folders from local machine to cluster server')
    parser.add_argument('-l', '--local_dir', required=True, help='Local directory path')
    parser.add_argument('-c', '--cluster_dir', required=True, help='Destination directory path on cluster')
    parser.add_argument('-f', '--filename', help='Specific file to transfer (optional)', default=None)
    parser.add_argument('--skip-dots', action='store_true', default=True, help='Skip files starting with "._"')
    parser.add_argument('--username', help='Username for cluster', default=None)
    parser.add_argument('--password', help='Password for cluster', default=None)
    parser.add_argument('--host', help='Hostname', default='sftp.fmrib.ox.ac.uk')
    
    args = parser.parse_args()
    
    try:
        local2cluster(args.local_dir, args.cluster_dir, args.filename, args.username, args.password, args.host, args.skip_dots)
    finally:
        close_ssh_connection()

if __name__ == "__main__":
    main()
