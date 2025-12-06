import sys
import subprocess
import os
import signal
import time
import configparser
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSlider, QPushButton, QRadioButton, QComboBox, QCheckBox, QMessageBox)
from PyQt5.QtCore import Qt

class ScrCpyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'scrcpy Streaming App'
        
        # Initialize paths before UI
        self.adb_exec = 'adb'
        self.scrcpy_exec = 'scrcpy'
        self.load_config()

        self.initUI()
        
        # Populate devices immediately if tools are found
        if self.check_tools():
            self.populate_dropdown()

    def load_config(self):
        config = configparser.ConfigParser()
        config_file = 'config.ini'
        
        if os.path.exists(config_file):
            config.read(config_file)
            if 'Settings' in config and 'scrcpy_path' in config['Settings']:
                base_path = config['Settings']['scrcpy_path']
                # Construct absolute paths
                adb_path = os.path.join(base_path, "adb.exe")
                scrcpy_path = os.path.join(base_path, "scrcpy.exe")
                
                if os.path.exists(adb_path) and os.path.exists(scrcpy_path):
                    self.adb_exec = adb_path
                    self.scrcpy_exec = scrcpy_path
                else:
                    print(f"Warning: Tools not found at {base_path}. Falling back to system PATH.")

    def check_tools(self):
        """Quick check to ensure adb is accessible before running commands."""
        try:
            # We use startupinfo to hide the console window for the check
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.run([self.adb_exec, '--version'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL, 
                           startupinfo=startupinfo,
                           check=True)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            QMessageBox.critical(self, "Error", 
                f"Could not find ADB.\n\nCurrent Configured Path:\n{self.adb_exec}\n\n"
                "Please check your config.ini or install ADB to your System PATH.")
            return False

    def initUI(self):
        self.setWindowTitle(self.title)

        self.layout = QVBoxLayout()
        self.deviceDropdown = QComboBox(self)
        self.deviceLabel = QLabel("Device: ")
        self.ipLabel = QLabel("IP: ")

        self.usbButton = QRadioButton("USB")
        self.usbButton.setChecked(True) # Default to USB
        self.wifiButton = QRadioButton("WiFi")

        self.bitrateLabel = QLabel("Bit Rate(Mb/s): 40")
        self.rateSlider = QSlider(Qt.Horizontal)
        self.rateSlider.setRange(0, 100)
        self.rateSlider.setValue(40)
        self.rateSlider.valueChanged[int].connect(self.changeValue) 

        self.audioCheck = QCheckBox("Include audio stream", self)
        self.monoCheck = QCheckBox("Monoscopic view (VR only)", self)
        
        self.recordButton = QPushButton('Start Recording', self)
        self.recordButton.setStyleSheet("background-color: green")
        self.recordButton.clicked.connect(self.startRecording)

        self.streamButton = QPushButton('Start Streaming', self)
        self.streamButton.setStyleSheet("background-color: green")
        self.streamButton.clicked.connect(self.startStreaming)
        
        self.refreshButton = QPushButton('Refresh Devices', self)
        self.refreshButton.clicked.connect(self.populate_dropdown)
        
        self.layout.addWidget(self.refreshButton)
        self.layout.addWidget(self.deviceLabel)
        self.layout.addWidget(self.deviceDropdown)
        self.layout.addWidget(self.ipLabel)
        self.layout.addWidget(self.usbButton)
        self.layout.addWidget(self.wifiButton)
        self.layout.addWidget(self.bitrateLabel)
        self.layout.addWidget(self.rateSlider)
        self.layout.addWidget(self.audioCheck) 
        self.layout.addWidget(self.monoCheck) 
        self.layout.addWidget(self.recordButton)
        self.layout.addWidget(self.streamButton)

        self.setLayout(self.layout)
        self.show()

        # Initialize member variables for recording and streaming
        self.recording = False
        self.streaming = False
        self.subprocesses = []

    def changeValue(self, value):
        self.bitrateLabel.setText(f"Bit Rate(Mb/s): {value}")

    def populate_dropdown(self):
        self.deviceDropdown.clear()
        try:
            device_list = self.get_device_list()
            self.deviceDropdown.addItems(device_list)
        except Exception as e:
            print(f"Error populating dropdown: {e}")

    def get_device_list(self):
        # Added creationflags to hide console window popping up
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        try:
            device_output = subprocess.check_output(
                [self.adb_exec, 'devices'], 
                startupinfo=startupinfo
            ).decode('utf-8').split('\n')
            
            device_output = [x.split('\t')[0] for x in device_output if x.split('\t')[0]]
            devices = device_output[1:]   # first element is a description
            return devices
        except Exception as e:
            print(f"Failed to get devices: {e}")
            return []

    def startRecording(self):
        if self.recording:
            self.end_recording_or_streaming('recording')
            self.recordButton.setText('Start Recording')
            self.recordButton.setStyleSheet("background-color: green")
        else:
            self.init_recording_or_streaming('recording')
            self.recordButton.setText('Stop Recording')
            self.recordButton.setStyleSheet("background-color: red")

    def startStreaming(self):
        if self.streaming:
            self.end_recording_or_streaming('streaming')
            self.streamButton.setText('Start Streaming')
            self.streamButton.setStyleSheet("background-color: green")
        else:
            self.init_recording_or_streaming('streaming')
            self.streamButton.setText('Stop Streaming')
            self.streamButton.setStyleSheet("background-color: red")

    def init_recording_or_streaming(self, task):
        selected_device = self.deviceDropdown.currentText()
        if selected_device == "":
            QMessageBox.warning(self, "Warning", "Please select a device!")
            return
        
        device_ip = ""
        if self.wifiButton.isChecked():
            device_ip = self.get_ip(selected_device)
            
        bitrate = str(self.rateSlider.value())+'M'
        scrcpy_cmd = self.set_cmd(selected_device, bitrate, device_ip, task)
        
        try:
            # CHANGE HERE: Add creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            # This prevents signals sent to scrcpy from crashing your Python GUI
            proc = subprocess.Popen(
                scrcpy_cmd, 
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            self.subprocesses.append(proc)
            setattr(self, task, True)
        except FileNotFoundError:
             QMessageBox.critical(self, "Error", f"Could not find scrcpy executable at:\n{self.scrcpy_exec}")

    def set_cmd(self, device, bitrate, ip, task):
        type_ = 'usb' if self.usbButton.isChecked() else 'wifi'
        include_audio = self.audioCheck.isChecked() 
        monoscopic_view = self.monoCheck.isChecked()

        cmd = [self.scrcpy_exec]

        if type_ == 'wifi':
            # Setup TCP/IP
            subprocess.run([self.adb_exec, '-s', device, 'tcpip', '5555'])
            subprocess.run([self.adb_exec, 'connect', f"{ip}:5555"])      
            cmd.extend(['-s', f"{ip}:5555"])
        else:
            cmd.extend(['-s', device])

        if task == 'recording':
            filename = f"recording_{time.strftime('%Y%m%d-%H%M%S')}.mkv"
            cmd.extend(['-r', filename, '--no-playback'])

        if include_audio:
            cmd.append('--audio') # Note: 'scrcpy' flags often change, ensure --audio is correct for v2.0+

        if monoscopic_view:
            cmd.extend(['--crop', '1832:1500:1832:0'])

        cmd.extend(['-b', bitrate, '--max-size', '800'])

        return cmd

    def end_recording_or_streaming(self, task):
        for proc in self.subprocesses:
            if proc.poll() is None:
                if task == 'recording':
                    # Send Ctrl+C to stop recording gracefully
                    os.kill(proc.pid, signal.CTRL_C_EVENT) 
                proc.terminate()
        self.subprocesses = []
        setattr(self, task, False)

    def get_ip(self, device):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        try:
            ip_info = subprocess.check_output(
                [self.adb_exec, '-s', device, 'shell', 'ip', 'route'], 
                startupinfo=startupinfo
            ).decode('utf-8').rstrip().split(' ')
            
            src_index = ip_info.index('src')
            ip_address = ip_info[src_index+1]  # the ip is item after 'src'
            self.ipLabel.setText(f"IP: {ip_address}")
            return ip_address
        except Exception as e:
            print(f"Could not get IP: {e}")
            return "0.0.0.0"
     
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ScrCpyApp()
    sys.exit(app.exec_())