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

# Global variables to track progress
_last_percent = 0
_last_update_time = 0
_file_size = 0
_start_time = 0

def progress(filename, size, sent):
    """Simple progress tracking for SCP transfers."""
    global _last_percent, _last_update_time, _file_size, _start_time
    
    # Initialize tracking variables on first call
    if sent == 0:
        _file_size = size
        _last_percent = 0
        _start_time = time.time()
        _last_update_time = 0
        print(f"Downloading {filename} ({round(size / (1024*1024), 2)} MB)...")
    
    # Calculate current progress
    percent = int((sent / size) * 100)
    
    # Only update the display if percent changed or it's been more than a second
    current_time = time.time()
    if percent != _last_percent or (current_time - _last_update_time) > 1:
        _last_percent = percent
        _last_update_time = current_time
        
        # Calculate speed
        elapsed = current_time - _start_time
        if elapsed > 0:
            speed = sent / elapsed / (1024*1024)  # MB/s
            
            # Calculate ETA
            if sent > 0:
                eta = elapsed * (size - sent) / sent
                eta_str = f"{int(eta / 60)}m {int(eta % 60)}s"
            else:
                eta_str = "calculating..."
                
            # Print progress bar
            bar_length = 30
            filled_length = int(bar_length * percent // 100)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            
            print(f"\r[{bar}] {percent}% {round(sent/(1024*1024), 1)}/{round(size/(1024*1024), 1)} MB ({speed:.2f} MB/s) ETA: {eta_str}", end="", flush=True)
            
            # Print newline when complete
            if sent >= size:
                print("\nDownload complete!")

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


