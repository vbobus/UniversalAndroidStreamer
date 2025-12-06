import sys
import subprocess
import os
import signal
import re
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, QRadioButton, QComboBox, QCheckBox)
from PyQt5.QtCore import Qt
import time

class ScrCpyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'scrcpy Streaming App'
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)

        self.layout = QVBoxLayout()
        self.deviceDropdown = QComboBox(self)
        self.deviceLabel = QLabel("Device: ")
        self.ipLabel = QLabel("IP: ")

        self.usbButton = QRadioButton("USB")
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
        device_list = self.get_device_list()
        self.deviceDropdown.addItems(device_list)

    def get_device_list(self):
        device_output = subprocess.check_output(['adb', 'devices']).decode('utf-8').split('\n')
        device_output = [x.split('\t')[0] for x in device_output if x.split('\t')[0]]
        devices = device_output[1:]   # first element is a description
        return devices

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
            print("Please select a device!")
            return
        device_ip = self.get_ip(selected_device)
        bitrate = str(self.rateSlider.value())+'M'
        scrcpy_cmd = self.set_cmd(selected_device, bitrate, device_ip, task)
        proc = subprocess.Popen(scrcpy_cmd)
        self.subprocesses.append(proc)
        setattr(self, task, True)

    def set_cmd(self, device, bitrate, ip, task):
        type_ = 'usb' if self.usbButton.isChecked() else 'wifi'
        include_audio = self.audioCheck.isChecked() 
        monoscopic_view = self.monoCheck.isChecked()

        cmd = ['scrcpy']

        if type_ == 'wifi':
            subprocess.run(['adb', '-s', device, 'tcpip', '5555'])
            subprocess.run(['adb', 'connect', f"{ip}:5555"])      
        
            cmd.extend(['-s', f"{ip}:5555"])
        else:
            cmd.extend(['-s', device])

        if task == 'recording':
            cmd.extend(['-r', f"recording_{time.strftime('%Y%m%d-%H%M%S')}.mp4", '--no-playback'])

        if include_audio:
            cmd.append('-a')

        if monoscopic_view:
            cmd.extend(['--crop', '1832:1500:1832:0'])

        cmd.extend(['-b', bitrate, '--max-size', '800'])

        return cmd

    def end_recording_or_streaming(self, task):
        for proc in self.subprocesses:
            if proc.poll() is None:
                if task == 'recording':
                    os.kill(proc.pid, signal.CTRL_C_EVENT)  # send Ctrl+C signal to save the file properly
                proc.terminate()
        self.subprocesses = []
        setattr(self, task, False)

    def get_ip(self, device):
        ip_info = subprocess.check_output(['adb', '-s', device, 'shell', 'ip', 'route']).decode('utf-8').rstrip().split(' ')
        src_index = ip_info.index('src')
        ip_address = ip_info[src_index+1]  # the ip is item after 'src'
        self.ipLabel.setText(f"IP: {ip_address}")
        return ip_address
    
app = QApplication(sys.argv)
window = ScrCpyApp()
sys.exit(app.exec_())