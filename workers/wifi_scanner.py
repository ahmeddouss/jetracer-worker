from pyzbar.pyzbar import decode
import subprocess
import re
from jetcam.csi_camera import CSICamera
import cv2
SOUND_CONNECTED = "jetracer_worker/sounds/connected.wav"
SOUND_ERROR = "jetracer_worker/sounds/error.wav"
SOUND_SCAN = "jetracer_worker/sounds/scan.wav"

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

def connect_to_wifi(ssid, password):
    try:
        print(f"Connecting to Wi-Fi SSID: {ssid}")
        subprocess.run(["nmcli", "dev", "wifi", "connect", ssid, "password", password], check=True)

    except subprocess.CalledProcessError as e:
        print(f"Error connecting to Wi-Fi: {e}")
        subprocess.run(["aplay",SOUND_SCAN])


def start_wifi_scanning():
    cap = CSICamera(width=640, height=480, capture_fps=21)
    print("Camera accessed successfully!")
    subprocess.run(["aplay",SOUND_SCAN])

    try:
        while True:
            frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            decoded_objects = decode(gray)
            if decoded_objects:
                for obj in decoded_objects:
                    qr_data = obj.data.decode('utf-8')
                    print(f"QR Code Detected! Data: {qr_data}")

                    ssid, password = parse_wifi_qr(qr_data)
                    if ssid and password:
                        connect_to_wifi(ssid, password)
                        return
                    else:
                        print("Failed to parse Wi-Fi credentials.")
    finally:
        cap.cap.release()  # Properly release GStreamer resource


if __name__ == "__main__":
    start_wifi_scanning()