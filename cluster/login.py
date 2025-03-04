import paramiko
import getpass

# Color constants
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def login2ssh(username=None, password=None, hostname=None):
    if username is None:
        username = input("Enter your username: ")
    if password is None:
        password = getpass.getpass("Enter your password: ")
    
    print(f"Logging in to {hostname} as {username}...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Method 1: Try with combined password+2FA code
        try:
            # Get 2FA code
            two_factor_code = input("Enter your 2FA code: ")
            
            # For BMRC, combine password and 2FA code as a single entry
            combined_password = password + two_factor_code
            
            ssh.connect(hostname=hostname, username=username, password=combined_password)
            print(f"{GREEN}Logged in using combined password+2FA method{RESET}")
            sftp = ssh.open_sftp()
            return ssh, sftp
        except paramiko.AuthenticationException:
            print(f"{YELLOW}Combined password method failed, trying interactive auth...{RESET}")
            
            # Method 2: Try with interactive authentication
            transport = paramiko.Transport((hostname, 22))
            transport.start_client()
            
            # First authentication with password
            transport.auth_password(username, password)
            
            # If 2FA is required, it will prompt for the second factor
            if not transport.is_authenticated():
                two_factor_code = input("Enter your 2FA code (for interactive auth): ")
                transport.auth_interactive_dumb(username, handler=lambda title, instructions, fields: [password, two_factor_code])
            
            # Create a client from the authenticated transport
            if transport.is_authenticated():
                ssh._transport = transport
                print(f"{GREEN}Logged in using interactive authentication method{RESET}")
                sftp = ssh.open_sftp()
                return ssh, sftp
            else:
                print(f"{RED}Authentication failed.{RESET}")
                raise paramiko.AuthenticationException("Authentication failed")
    except paramiko.AuthenticationException:
        print(f"{RED}Authentication failed. Please check your credentials.{RESET}")
        raise
    except Exception as e:
        print(f"{RED}Connection failed: {str(e)}{RESET}")
        raise


