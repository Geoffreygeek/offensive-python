import paramiko
import socket
import sys

def grab_ssh_banner(ip_address, port=22, timeout=5):
    try:
        sock = socket.create_connection((ip_address, port), timeout=timeout)
        banner = sock.recv(1024).decode().strip()
        sock.close()
        return banner
    except socket.timeout:
        return "Connection timed out"
    except ConnectionRefusedError:
        return "Connection refused"
    except Exception as e:
        return f"An error occurred: {str(e)}"

def main():
    try:
        ip_address = input("Enter the IP address to grab the SSH banner from: ")
        
        # Validate IP address format
        try:
            socket.inet_aton(ip_address)
        except socket.error:
            print("Invalid IP address format.")
            return

        banner = grab_ssh_banner(ip_address)
        print(f"SSH Banner for {ip_address}:")
        print(banner)
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()
