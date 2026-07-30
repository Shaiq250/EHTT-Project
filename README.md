# Python Remote Access Tool & Keylogger

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![Security](https://img.shields.io/badge/Security-Red%20Team-red?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Educational-yellow?style=for-the-badge)

> [!CAUTION]
> **LEGAL & ETHICAL WARNING**
>
> This software was developed solely for **educational purposes** as part of the **Ethical Hacking and Threat Technologies (EHTT)** university course.
>
> *   **Do not use this tool on systems you do not own or do not have explicit permission to test.**
> *   Unauthorized use of keyloggers, remote access tools (RATs), or network scanners is illegal and punishable by law (e.g., CFAA in the US, various Cybercrime Acts globally).
> *   The authors and the university assume **no liability** for misuse of this code. It is provided for research to understand how malware operates and how to defend against it.

---

## 🔍 Project Overview

This project is a sophisticated **Remote Access Tool (RAT)** and **Keylogger** developed to demonstrate the capabilities of modern malware and the importance of endpoint security. It functions as a spyware agent that captures sensitive user data and exfiltrates it to remote servers, controlled via a covert Command & Control (C2) channel.

## ⚙️ Capabilities

The tool implements a wide range of surveillance features commonly found in APTs (Advanced Persistent Threats):

### 🕵️ Surveillance & Data Theft
*   **Keylogging**: Captures every keystroke typed by the user.
*   **Clipboard Hijacking**: Monitors and logs all text copied to the clipboard.
*   **Screen Recording**: Continuously records the victim's screen and saves it as video.
*   **Webcam Recording**: Can be remotely triggered to record video from the front camera.
*   **Wi-Fi Enumeration**: Extracts and dumps saved Wi-Fi SSIDs and cleartext passwords.
*   **System Profiling**: Gathers Hostname, Private IP, and Public IP (via external APIs).

### 📡 Command & Control (C2)
*   **Remote Execution**: Polls a **cryptic text file hosted on Google Drive** to receive commands, bypassing traditional firewall blocks.
    *   `start_front_camera`: Activates webcam recording.
    *   `lock_screen`: Forces the workstation to lock.
    *   `stop`: Terminates the malware and performs cleanup.

### 📤 Exfiltration
*   **Dual-Channel Exfiltration**:
    *   **SMTP (Email)**: Sends lightweight text logs (keystrokes, clipboard, system info) via email.
    *   **Mega.nz Cloud**: Uploads heavy media files (screen recordings, webcam footage) to encrypted cloud storage to avoid email attachment limits.

## 🛡️ Defensive Mechanisms (Blue Team)

*To balance the offensive nature of this tool, here are ways to detect and block it:*

1.  **Network Monitoring**: Monitor traffic for unusual outbound SMTP connections or connections to `mega.nz` and `drive.google.com` from non-user processes.
2.  **Behavioral Analysis**: Alert on processes that register Global Key Hooks (using `SetWindowsHookEx` or `pynput`).
3.  **Process Monitoring**: Watch for unauthorized calls to `netsh wlan show profiles` (often used to steal Wi-Fi keys).
4.  **File Integrity**: Monitor the creation of hidden directories or files in user temp folders (e.g., `logs/`).

## 🚀 Usage (Lab Environment Only)

### Prerequisites
*   Python 3.x
*   A "burner" Gmail account (with App Password enabled)
*   A Mega.nz account
*   A text file hosted on Google Drive (Publicly accessible)

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-repo/EHTT-RAT.git
    cd EHTT-RAT
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuration**:
    Open `FINAL_CODE.py` and configure the C2 settings:
    ```python
    EMAIL_SENDER = "attacker@gmail.com"
    EMAIL_RECEIVER = "attacker@gmail.com"
    EMAIL_PASS = "your_app_password"
    MEGA_EMAIL = "attacker@gmail.com"
    MEGA_PASS = "mega_password"
    COMMAND_FILE_URL = "https://drive.google.com/uc?id=YOUR_FILE_ID"
    ```

### Running the Agent
```bash
python FINAL_CODE.py
```
*The script will run silently, creating a `logs/` directory and beginning surveillance.*

## 📂 Project Structure

*   **`FINAL_CODE.py`**: The primary payload containing all malware logic.
*   **`project report.pdf`**: Detailed academic report on the tool's architecture.
*   **`commandsneeded.txt`**: List of commands understood by the C2.

## 🤝 Contributing

This project is closed for active development to prevent misuse. Educational forks for defensive research (building AV signatures, detection rules) are encouraged.
