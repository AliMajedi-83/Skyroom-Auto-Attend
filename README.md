# 🎓 Skyroom Auto-Attend Bot

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-blue.svg)
![License](https://img.shields.io/badge/License-GPLv3-blue.svg)

An advanced, automated Python application designed to automatically join scheduled Skyroom virtual classes, monitor audio activity (silence detection), and record class sessions efficiently. 

This repository contains two dedicated versions optimized for **Linux (PulseAudio)** and **Windows (WASAPI)**.

---

## 📂 Project Structure
- **`/Linux`**: The native Linux version using `sounddevice`, `PulseAudio`, and a `Makefile` for zero-config setup. Features a Dual GUI/CLI architecture.
- **`/Windows`**: The native Windows version using `pyaudiowpatch` and `WASAPI` loopback. Includes `.bat` scripts for a seamless, click-and-run experience.

---

## 🐧 Linux Edition Guide

### 🛠️ Setup & Installation
Thanks to the integrated `Makefile`, setting up the project takes only one command:
```bash
git clone https://github.com/AliMajedi-83/Skyroom-Auto-Attend.git
cd Skyroom-Auto-Attend/Linux
make setup
```
### 🚀 Usage

GUI Mode:
```Bash

make run
```
![Skyroom Bot GUI](assets/1.png)


CLI Mode:
```Bash

./venv/bin/python3 cli.py -h
```
![Skyroom Bot GUI](assets/3.png)

## 🪟 Windows Edition Guide

### 🚀 Setup & Usage
```Bash
Open the Windows folder.
```
```Bash
Double-click install.bat to install Python dependencies.
```
```Bash
Double-click run.bat to launch the GUI bot in the background.
```
### ⚠️ ChromeDriver Troubleshooting

Due to filtering, chromedriver.exe is pre-included in Windows/core/bin/. If the bot crashes, your Chrome browser version doesn't match the driver.

Fix: First update your **Chrome Browser**. Then download **chromedriver-win64** from https://googlechromelabs.github.io/chrome-for-testing/ and replace the file in core/bin/.
