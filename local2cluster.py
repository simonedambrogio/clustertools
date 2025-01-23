import paramiko
import os
import getpass
from tqdm import tqdm

# You can define color constants at the top of your file
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def login2ssh(hostname='jalapeno.fmrib.ox.ac.uk'):
    # username = input("Enter your username: ")
    # password = getpass.getpass("Enter your password: ")
    
    username = 'jdf650'
    password = 'judiciary-SELECTED-ISOLATION-GUY'
    print(f"Logging in to {hostname} as {username}...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(hostname=hostname, username=username, password=password)
        print(f"{GREEN}Logged in to server successfully{RESET}")
        sftp = ssh.open_sftp()
        return ssh, sftp
    except paramiko.AuthenticationException:
        print(f"{RED}Authentication failed. Please check your username and password.{RESET}")
        raise
    except Exception as e:
        print(f"{RED}Connection failed: {str(e)}{RESET}")
        raise

def send_file(sftp, localDIR, clusterDIR, filename):
    file_path_local    = f"{localDIR}{'' if localDIR.endswith('/') else '/'}{filename}"
    file_path_cluster = f"{clusterDIR}{'' if clusterDIR.endswith('/') else '/'}{filename}"

    print(f"Local file path: {file_path_local}")
    print(f"Cluster file path: {file_path_cluster}")
    file_size = os.path.getsize(file_path_local)
    print(f"Local file size: {round(file_size / 1024, 1)} KB")

    with open(file_path_local, "rb") as local_file:
        data = local_file.read()
        with sftp.open(file_path_cluster, "wb") as remote_file:
            with tqdm(total=file_size, unit='B', unit_scale=True, desc=filename) as pbar:
                remote_file.write(data)
                pbar.update(file_size)

    print(f'{GREEN}File {filename} transfer complete.{RESET}')

def send_folder(sftp, localDIR, clusterDIR, skip_dots=True):
    
    # Create on cluster the last folder from localDIR.
    last_folder_name = os.path.basename(os.path.normpath(localDIR)) # Extract the last folder name from localDIR
    cluster_last_folder_name = os.path.basename(os.path.normpath(clusterDIR)) # Extract the intended last folder name in clusterDIR for comparison
    if last_folder_name != cluster_last_folder_name: # Check if the last folder names are different
        clusterDIR = os.path.join(clusterDIR, last_folder_name) # If different, update clusterDIR to include the last folder name from localDIR
        try:
            sftp.mkdir(clusterDIR) # Attempt to create the new directory on the remote server
            print(f"Created new directory on remote server: {clusterDIR}")
        except IOError:
            pass  # Ignore if the directory already exists

    # Walk through the local directory
    for dirpath, dirnames, filenames in os.walk(localDIR):
        rel_path = os.path.relpath(dirpath, localDIR)
        remote_path = os.path.join(clusterDIR, rel_path).replace("\\","/")

        try:
            sftp.mkdir(remote_path)
            print(f"Created remote directory: {remote_path}")
        except IOError:
            pass  # Remote directory already exists

        for filename in filenames:
            if skip_dots and filename.startswith("._"):
                print(f"Skipping {filename} as it starts with '._'")
                continue

            local_file_path = os.path.join(dirpath, filename)
            remote_file_path = os.path.join(remote_path, filename).replace("\\","/")

            print(f"{YELLOW}Transferring {local_file_path} to {remote_file_path}{RESET}")
            file_size = os.path.getsize(local_file_path)
            print(f"Local file size: {round(file_size / 1024, 1)} KB")
            
            with tqdm(total=file_size, unit='B', unit_scale=True, desc=filename) as pbar:
                def callback(transferred, to_be_transferred):
                    pbar.update(transferred - pbar.n)
                sftp.put(local_file_path, remote_file_path, callback=callback)

    foldername = os.path.basename(os.path.normpath(localDIR))
    print(f'{GREEN}Folder {foldername} transfer complete.{RESET}')

def local2cluster(localDIR, clusterDIR, filename=None, skip_dots=True):
    ssh, sftp = login2ssh()    
    try:
        if filename:
            send_file(sftp, localDIR, clusterDIR, filename)
        else:
            send_folder(sftp, localDIR, clusterDIR, skip_dots)
    finally:
        sftp.close()
        ssh.close()
        print('Operation complete.')

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Transfer files/folders from local machine to cluster server')
    parser.add_argument('-l', '--local_dir', required=True, help='Local directory path')
    parser.add_argument('-c', '--cluster_dir', required=True, help='Destination directory path on cluster')
    parser.add_argument('-f', '--filename', help='Specific file to transfer (optional)', default=None)
    parser.add_argument('--skip-dots', default=True, help='Skip files starting with "._"')
    parser.add_argument('--host', default='jalapeno.fmrib.ox.ac.uk', help='Hostname (default: jalapeno.fmrib.ox.ac.uk)')
    
    args = parser.parse_args()
    
    local2cluster(args.local_dir, args.cluster_dir, args.filename, args.skip_dots)
