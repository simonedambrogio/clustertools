import paramiko
import getpass
import time
from paramiko import SSHClient
from scp import SCPClient

# Color constants
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def login2ssh(username=None, password=None, hostname=None, max_retries=3):
    if username is None:
        username = input("Enter your username: ")
    if password is None:
        password = getpass.getpass("Enter your password: ")
    
    print(f"Connecting to {hostname} as {username}...")
    
    for attempt in range(max_retries):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Get 2FA code
            two_factor_code = getpass.getpass("Enter your 2FA code: ")
            combined_password = password + two_factor_code
            
            # Connect using combined password+2FA
            ssh.connect(
                hostname=hostname,
                username=username,
                password=combined_password,
                timeout=30,
                look_for_keys=False,
                allow_agent=False
            )
            
            print(f"{GREEN}Successfully authenticated to {hostname}{RESET}")
            
            # Create SCP client instead of SFTP
            scp = SCPClient(ssh.get_transport(), progress=progress)
            
            # Return SSH and SCP client
            return ssh, scp
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"{YELLOW}Connection attempt {attempt + 1} failed: {str(e)}. Retrying...{RESET}")
                time.sleep(2)  # Wait before retry
                continue
            else:
                print(f"{RED}Connection failed after {max_retries} attempts: {str(e)}{RESET}")
                raise
    
    raise Exception(f"Failed to connect after {max_retries} attempts")

def progress(filename, size, sent):
    """Progress callback for SCP transfers."""
    # This will be used by tqdm in the main functions
    pass


