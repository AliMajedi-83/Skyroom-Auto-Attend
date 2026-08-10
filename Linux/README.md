# 🎓 Skyroom Auto-Attend Bot

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![Selenium](https://img.shields.io/badge/Selenium-WebDriver-43B02A.svg)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Audio%2FVideo-green.svg)
![Platform](https://img.shields.io/badge/Platform-Linux%20Native-orange.svg)
![License](https://img.shields.io/badge/License-MIT-blue.svg)

An advanced, automated Python application designed to automatically join scheduled Skyroom virtual classes, monitor audio activity (silence detection), and record class sessions efficiently. Built with a dual GUI/CLI architecture, it captures pure internal hardware audio and outputs highly optimized media files.

## ✨ Key Features

- **Dual Interface:** Manage your schedules via a user-friendly GUI (Tkinter) or a professional interactive CLI.
- **Smart Silence Detection:** Bypasses the physical microphone and listens directly to internal PulseAudio. If the professor stops talking for a predefined time, the bot automatically gracefully terminates the session.
- **Extreme Media Optimization:** Uses advanced FFmpeg parameters (15 FPS, CRF 34, 32kbps mono audio) to ensure multi-hour classes consume minimal disk space (e.g., ~5MB/hour for audio) without sacrificing readability.
- **Browser Pulse-Check:** Instantly detects if the user manually closes the browser and cleanly stops the recording and saves the files without crashing.
- **Zero-Config Setup:** Fully automated environment setup, dependency installation, and Geckodriver configuration using a custom `Makefile`.
- **Centralized Logging:** Keeps a detailed track of class joins, audio levels, and system events in `logs/app.log`.

## 🛠️ Installation & Setup (Linux)

This bot is heavily optimized for Linux environments (X11 & PulseAudio).
Thanks to the integrated `Makefile`, setting up the project takes only one command.

**1. Clone the repository:**
```bash
git clone https://github.com/AliMajedi-83/Skyroom-Auto-Attend.git
cd Skyroom-Auto-Attend

2. Run the automated setup:
(This will install system dependencies, create a Python virtual environment, install requirements, and download the Firefox driver).
Bash

make setup

🚀 Usage

You can interact with the bot in two ways:
Method A: Graphical User Interface (GUI)

Simply run the following command to open the Tkinter dashboard:
Bash

make run

From here, you can add classes, set the schedule, choose recording modes, and manage your database.
Method B: Command Line Interface (CLI)

For a faster, terminal-based workflow (ideal for headless servers or quick edits), use the built-in CLI:
Bash

# View the help menu
./venv/bin/python3 cli.py -h

# Add a new class interactively
./venv/bin/python3 cli.py add

# List all scheduled classes
./venv/bin/python3 cli.py list

🧠 Under the Hood (Technical Details)

    Audio Routing: Dynamically queries pactl list short sources to find the system's monitor output, injects it into PULSE_SOURCE, and captures it using sounddevice and numpy (RMS calculation) to filter out base hardware noise.

    Concurrency: Utilizes Python's threading module to run the Selenium WebDriver, FFmpeg recording process, silence monitoring, and SQLite database scheduling simultaneously without blocking the main thread.

    Data Persistence: Uses sqlite3 to maintain schedules. The database is shared seamlessly between the GUI and CLI components.

🪟 Note for Windows Users

This bot heavily relies on Linux-specific audio architecture (PulseAudio) and display servers. To run this perfectly on a Windows machine, it is highly recommended to use WSL2 (Windows Subsystem for Linux - Ubuntu). Just run wsl --install in PowerShell, clone this repo inside WSL, and run make setup.

Developed by Ali Majedi — Combining Industrial Engineering system optimization with Linux automation.
