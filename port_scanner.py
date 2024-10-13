# Import necessary libraries
import socket  # For handling the connections
import threading  # For creating multiple threads to speed up the scan
from queue import Queue  # To manage the queue of ports
from datetime import datetime  # To track the time
import sys  # To handle system-specific parameters and exit cleanly

# Defining the target (IP or Domain)
target = input("Enter the target IP or domain: ")

# Prompt for the port range to scan
start_port = int(input("Enter the starting port (e.g., 1): "))
end_port = int(input("Enter the ending port (e.g., 65535): "))

# Create a queue to manage port scanning tasks
port_queue = Queue()

# Thread lock to avoid multiple threads printing simultaneously
print_lock = threading.Lock()

# Function to get banner information from open ports
def grab_banner(sock):
    try:
        sock.settimeout(2)
        banner = sock.recv(1024).decode().strip()  # Receive up to 1024 bytes of data
        return banner
    except Exception as e:
        return "Banner not available"

# Function to scan a single port
def scan_port(port):
    try:
        # Create a socket object
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)  # Timeout of 1 second per connection
        result = sock.connect_ex((target, port))  # Try to connect to the port
        if result == 0:  # If the result is 0, the port is open
            with print_lock:
                print(f"[+] Port {port} is open")
                # Attempt to grab banner information
                banner = grab_banner(sock)
                print(f"    Banner: {banner}")
        sock.close()  # Close the socket connection
    except KeyboardInterrupt:
        print("\n[!] User Interrupted")
        sys.exit(0)
    except socket.gaierror:
        print("[!] Could not resolve hostname")
        sys.exit(0)
    except socket.error:
        print("[!] Could not connect to server")
        sys.exit(0)

# Function for worker threads that pulls a port from the queue
def threader():
    while True:
        worker = port_queue.get()  # Get a port from the queue
        scan_port(worker)  # Call the scan_port function
        port_queue.task_done()  # Mark the task as done

# Main scanning function
def main():
    print(f"\n[+] Starting scan on: {target}")
    print(f"Time started: {datetime.now()}")
    print(f"Scanning ports {start_port} to {end_port}\n")

    # Start 100 threads to work in parallel
    for _ in range(100):
        thread = threading.Thread(target=threader)
        thread.daemon = True  # Daemon threads die when the main thread exits
        thread.start()

    # Populate the queue with the range of ports to scan
    for port in range(start_port, end_port + 1):
        port_queue.put(port)

    port_queue.join()  # Wait for all threads to finish scanning

    print(f"\n[+] Scan completed at: {datetime.now()}")

if __name__ == "__main__":
    main()
