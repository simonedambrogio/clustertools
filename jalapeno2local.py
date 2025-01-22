import os
import paramiko
from stat import S_ISDIR

def progress_callback(transferred, total):
    print(f"Transferred: {transferred}/{total} bytes ({100 * transferred // total}% complete)", end="\r")

def download_directory_or_file(sftp, localDIR, jalapenoDIR, filename=None, is_top_level=True):

    if filename:
        # Handling file download
        file_path_local = os.path.join(localDIR, filename)
        file_path_jalapeno = os.path.join(jalapenoDIR, filename)

        # Ensuring the local directory exists
        os.makedirs(os.path.dirname(file_path_local), exist_ok=True)

        print(f"Downloading file {filename}...")
        sftp.get(file_path_jalapeno, file_path_local, callback=progress_callback)
    else:
        # Adjust the local directory path only on the top-level call
        if is_top_level:
            name_folder = os.path.basename(jalapenoDIR.rstrip('/'))
            localDIR = os.path.join(localDIR, name_folder)
            os.makedirs(localDIR, exist_ok=True)

        print("Downloading folder...")

        for entry in sftp.listdir_attr(jalapenoDIR):
            if not entry.filename.startswith('.'):
                remote_file_path = os.path.join(jalapenoDIR, entry.filename)
                local_file_path = os.path.join(localDIR, entry.filename)

                if S_ISDIR(entry.st_mode):
                    # Ensure the local directory for nested content exists
                    if not os.path.exists(local_file_path):
                        os.makedirs(local_file_path)
                    # Recursive call without appending the base directory name again
                    download_directory_or_file(sftp, local_file_path, remote_file_path, is_top_level=False)
                else:
                    # Download file
                    print(f"Downloading {entry.filename}...")
                    sftp.get(remote_file_path, local_file_path, callback=progress_callback)
                    print(f"Downloaded {entry.filename} to {local_file_path}")

def jalapeno2local(localDIR, jalapenoDIR, filename=None):
    hostname = 'jalapeno.fmrib.ox.ac.uk'
    username = 'jdf650'
    password = 'judiciary-SELECTED-ISOLATION-GUY'

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=hostname, username=username, password=password)
    print("Logged in to server ;)")
    sftp = ssh.open_sftp()

    try:
        download_directory_or_file(sftp, localDIR, jalapenoDIR, filename)
    finally:
        sftp.close()
        ssh.close()
        print('File transfer complete.')


