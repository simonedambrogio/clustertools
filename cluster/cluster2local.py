import os
import paramiko
import getpass
from stat import S_ISDIR
from tqdm import tqdm
import argparse

# Color constants
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def login2ssh(hostname='clint.fmrib.ox.ac.uk'):
    username = input("Enter your username: ")
    password = getpass.getpass("Enter your password: ")
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

def download_file(sftp, localDIR, jalapenoDIR, filename):
    file_path_local = os.path.join(localDIR, filename)
    file_path_jalapeno = os.path.join(jalapenoDIR, filename)

    # Ensuring the local directory exists
    os.makedirs(os.path.dirname(file_path_local), exist_ok=True)

    print(f"Remote file path: {file_path_jalapeno}")
    print(f"Local file path: {file_path_local}")
    
    # Get file size for progress bar
    file_size = sftp.stat(file_path_jalapeno).st_size
    print(f"Remote file size: {round(file_size / 1024, 1)} KB")

    print(f"{YELLOW}Downloading {filename}...{RESET}")
    with tqdm(total=file_size, unit='B', unit_scale=True, desc=filename) as pbar:
        def callback(transferred, to_be_transferred):
            pbar.update(transferred - pbar.n)
        sftp.get(file_path_jalapeno, file_path_local, callback=callback)
    
    print(f'{GREEN}File {filename} download complete.{RESET}')

def download_folder(sftp, localDIR, jalapenoDIR, is_top_level=True):
    # Adjust the local directory path only on the top-level call
    if is_top_level:
        name_folder = os.path.basename(jalapenoDIR.rstrip('/'))
        localDIR = os.path.join(localDIR, name_folder)
        os.makedirs(localDIR, exist_ok=True)

    print(f"{YELLOW}Downloading folder contents from {jalapenoDIR}...{RESET}")

    for entry in sftp.listdir_attr(jalapenoDIR):
        if not entry.filename.startswith('.'):
            remote_file_path = os.path.join(jalapenoDIR, entry.filename)
            local_file_path = os.path.join(localDIR, entry.filename)

            if S_ISDIR(entry.st_mode):
                # Ensure the local directory for nested content exists
                if not os.path.exists(local_file_path):
                    os.makedirs(local_file_path)
                # Recursive call without appending the base directory name again
                download_folder(sftp, local_file_path, remote_file_path, is_top_level=False)
            else:
                # Download file with progress bar
                file_size = entry.st_size
                print(f"\nRemote file size: {round(file_size / 1024, 1)} KB")
                with tqdm(total=file_size, unit='B', unit_scale=True, desc=entry.filename) as pbar:
                    def callback(transferred, to_be_transferred):
                        pbar.update(transferred - pbar.n)
                    sftp.get(remote_file_path, local_file_path, callback=callback)

def jalapeno2local(localDIR, jalapenoDIR, filename=None):
    ssh, sftp = login2ssh()
    try:
        if filename:
            download_file(sftp, localDIR, jalapenoDIR, filename)
        else:
            download_folder(sftp, localDIR, jalapenoDIR)
    finally:
        sftp.close()
        ssh.close()
        print(f'{GREEN}Operation complete.{RESET}')

def main():
    parser = argparse.ArgumentParser(description='Transfer files/folders from cluster server to local machine')
    parser.add_argument('-l', '--local_dir', required=True, help='Local directory path')
    parser.add_argument('-c', '--cluster_dir', required=True, help='Source directory path on cluster')
    parser.add_argument('-f', '--filename', help='Specific file to transfer (optional)', default=None)
    parser.add_argument('--skip-dots', default=True, help='Skip files starting with "._"')
    parser.add_argument('--host', default='clint.fmrib.ox.ac.uk', help='Hostname (default: clint.fmrib.ox.ac.uk)')
    
    args = parser.parse_args()
    
    jalapeno2local(args.local_dir, args.cluster_dir, args.filename)

if __name__ == "__main__":
    main()


