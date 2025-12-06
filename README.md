# Universal Android Streamer

**Universal Android Streamer** is a versatile Python-based application for effortlessly streaming video from any Android-based device onto your computer. 

This tool utilizes PyQt for a user-friendly interface, enabling users to choose between USB and Wi-Fi for connectivity, and also allowing easy adjustment of video bitrate. Ideal for gaming, app testing, or any situation where larger screen visibility is needed or if the device doesn't have an inbuilt recording feature.

## Features
* **USB & WiFi Support:** Stream via high-speed USB or wireless TCP/IP.
* **Bitrate Control:** Adjust streaming quality on the fly.
* **Recording:** Record screen capture directly to `.mp4` files.
* **VR Support:** Includes Monoscopic crop options for VR headsets.
* **Portable:** Configurable paths allow usage without modifying system Environment Variables.

## Prerequisites
1.  **Python 3.x** installed.
2.  **Scrcpy** downloaded and extracted (includes ADB).

## Installation

1.  **Install Dependencies:**
    Open your terminal in the project directory and run:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configuration (Important):**
    This application requires `scrcpy` and `adb` to function. 
    
    * Create a file named `config.ini` in the project root.
    * Add the path to your scrcpy folder (the folder containing `scrcpy.exe` and `adb.exe`).
    
    **Example `config.ini`:**
    ```ini
    [Settings]
    scrcpy_path = D:\scrcpy-win64-v3.3.3\scrcpy-win64-v3.3.3
    ```

## Usage
1.  Connect your Android device via USB.
2.  Ensure **USB Debugging** is enabled on your phone (Developer Options).
3.  Run the application:
    ```bash
    python Streamer.py
    ```
4.  Click **Refresh Devices** to see your connected phone.
5.  Select **Start Streaming** or **Start Recording**.

## Troubleshooting
* **No Devices Found?** Check your USB cable and ensure you accepted the "Allow USB Debugging" prompt on your phone screen.
* **FileNotFoundError?** Ensure your `config.ini` path is correct and points to the folder containing the `.exe` files, not just the parent folder.