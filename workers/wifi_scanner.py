import cv2
from pyzbar.pyzbar import decode
import time
import sys
import subprocess
import re


SOUND_CONNECTED = "../sounds/connected.wav"
SOUND_ERROR = "../sounds/error.wav"
SOUND_SCAN = "../sounds/scan.wav"

def parse_wifi_qr(qr_data):
    try:
        # Custom format: "Ssid:Redmi 13C,Pass:1233211234"
        match_custom = re.match(r"Ssid:(.*?),Pass:(.*)", qr_data)
        if match_custom:
            return match_custom.group(1).strip(), match_custom.group(2).strip()

        # Standard format: "WIFI:T:WPA;P:password;S:ssid;H:false;"
        match_wifi = re.match(r"WIFI:T:(.*?);P:(.*?);S:(.*?);", qr_data)
        if match_wifi:
            return match_wifi.group(3).strip(), match_wifi.group(2).strip()
    except Exception as e:
        print(f"QR parsing error: {e}")
    
    return None, None

def play_sound(sound_file):
    try:
        subprocess.run(["aplay", sound_file], check=True)
        print(f"✅ Sound '{sound_file}' played successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to play sound '{sound_file}': {e}")

def is_connected():
    try:
        output = subprocess.check_output(['nmcli', '-t', '-f', 'STATE', 'general']).decode().strip()
        if output == 'connected':
            play_sound(SOUND_CONNECTED)
            return True
    except subprocess.CalledProcessError as e:
        print("Error checking connection:", e)
    return False

def connect_to_wifi(ssid, password):
    try:
        print(f"Connecting to Wi-Fi SSID: {ssid}")
        subprocess.run(["nmcli", "dev", "wifi", "connect", ssid, "password", password], check=True)
        play_sound(SOUND_CONNECTED)
    except subprocess.CalledProcessError as e:
        print(f"Error connecting to Wi-Fi: {e}")
        play_sound(SOUND_ERROR)

def release_and_exit(cap):
    print("Releasing camera...")
    cap.release()
    time.sleep(0.5)
    sys.exit(0)

def start_wifi_scanning():
    if is_connected():
        print("Already connected to Wi-Fi. Exiting...")
        return

    print("No Wi-Fi connection. Waiting for QR code...")
    play_sound(SOUND_SCAN)

    gst_pipeline = (
        "nvarguscamerasrc ! "
        "video/x-raw(memory:NVMM), width=(int)1280, height=(int)720, framerate=(fraction)30/1 ! "
        "nvvidconv ! video/x-raw, format=(string)BGRx ! "
        "videoconvert ! video/x-raw, format=(string)BGR ! appsink"
    )

    cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

    if not cap.isOpened():
        print("Error: Unable to access the camera!")
        sys.exit(1)

    print("Camera accessed successfully!")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            release_and_exit(cap)

        decoded_objects = decode(frame)
        if decoded_objects:
            for obj in decoded_objects:
                qr_data = obj.data.decode('utf-8')
                print(f"QR Code Detected! Data: {qr_data}")

                ssid, password = parse_wifi_qr(qr_data)
                if ssid and password:
                    connect_to_wifi(ssid, password)
                else:
                    print("Failed to parse Wi-Fi credentials.")

                cv2.imwrite("detected_frame.jpg", frame)
                release_and_exit(cap)

if __name__ == "__main__":
    start_wifi_scanning()