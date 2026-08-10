# 🎓 Skyroom Auto-Attend Bot (Windows Edition)

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-blue.svg)

An automated Python application for Windows users to automatically join scheduled Skyroom virtual classes, detect silence, and record screen/audio without microphone noise.

---

## ⚠️ CRITICAL WINDOWS SETUP

Unlike Linux, Windows mixes all audio inputs by default. To make this bot capture internal audio (and detect silence properly without background microphone noise), you **MUST** enable "Stereo Mix":

1. Right-click the Speaker icon in your Windows taskbar -> **Sounds** (or open Sound Control Panel).
2. Go to the **Recording** tab.
3. Right-click on empty space and check **"Show Disabled Devices"**.
4. Right-click **Stereo Mix** -> **Enable**.
5. Right-click **Stereo Mix** -> **Set as Default Device**.
*(If Stereo Mix is missing, you may need to update your Realtek Audio Drivers).*

---

## 🛠️ Prerequisites

1. **Python 3.9+** (Make sure to check **"Add Python to PATH"** during the Python installation).
2. **FFmpeg for Windows** (Download the `.zip`, extract it, and add the `bin` folder to your System Environment PATH).

---

## 🚀 Installation & Usage

Thanks to the provided batch scripts, running the bot is incredibly simple:

1. **Install Dependencies:** 
   Double-click the `install.bat` file. This will automatically install all required Python libraries. You only need to do this once.
   
2. **Run the Bot:** 
   Double-click the `run.bat` file. The application will launch in the background without keeping an annoying console window open.

---

## ⚠️ Troubleshooting ChromeDriver (Browser Crashes)

Due to network restrictions, the `chromedriver.exe` file has been pre-downloaded and placed directly in the `core/bin/` directory. 

If the bot fails to launch the browser or crashes immediately, your laptop's installed Google Chrome version likely does not match the provided driver. 

**To fix this:**
1. Check your laptop's main Google Chrome version (`Settings > About Chrome`).
2. Go to the official [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/) page.
3. Download the `chromedriver-win64` version that exactly matches your browser.
4. Extract the `.zip` file and replace the existing `chromedriver.exe` inside the `core/bin/` folder with the new one.
