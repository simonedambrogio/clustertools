import paramiko
import getpass
import time
from scp import SCPClient
from tqdm import tqdm

# Color constants
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

# Global variable to hold progress bar
progress_bar = None

def progress(filename, size, sent):
    """Progress callback for SCP transfers."""
    global progress_bar
    
    # Initialize the progress bar if it doesn't exist yet
    if progress_bar is None:
        progress_bar = tqdm(total=size, unit='B', unit_scale=True, desc=filename)
    
    # Update the progress bar with the difference in bytes
    progress_bar.update(sent - progress_bar.n)
    
    # If we've reached the total size, close the progress bar
    if sent >= size:
        progress_bar.close()
        progress_bar = None

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
            
            # Create SCP client with progress callback
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


