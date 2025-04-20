import threading
import time
import socket
import subprocess
from jetracer_worker.workers.wifi_watcher import watch_wifi_changes
from jetracer_worker.workers.speaker import play_sound

first_disconnect = True
sensor_process = None
livekit_process = None

def on_disconnect():
    global sensor_process, livekit_process, first_disconnect
    print("⚠️ Internet connection lost!")
    if first_disconnect:
        play_sound("jetracer_worker/sounds/failed.wav")
        first_disconnect = False
    else:
        play_sound("jetracer_worker/sounds/lost.wav")
    subprocess.Popen(["python3", "jetracer_worker/workers/wifi_scanner.py"])
    if sensor_process and sensor_process.poll() is None:
        sensor_process.terminate()
        sensor_process = None
    if livekit_process and livekit_process.poll() is None:
        livekit_process.terminate()
        livekit_process = None
    

def on_connect():
    global sensor_process, livekit_process, first_disconnect
    first_disconnect = False
    print("✅ Internet connection restored!")
    play_sound("jetracer_worker/sounds/connected.wav")
    sensor_process = subprocess.Popen(["python3", "jetracer_worker/workers/sensors.py"])
    livekit_process = subprocess.Popen(["python3", "jetracer_worker/livekit_main.py","dev"])

def check_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def monitor_internet(on_disconnect, on_connect, check_interval=5):
    def monitor():
        was_connected = check_internet()
        if was_connected:
            on_connect()
        else:
            on_disconnect()

        while True:
            time.sleep(check_interval)
            connected = check_internet()
            if connected != was_connected:
                if connected:
                    on_connect()
                else:
                    on_disconnect()
                was_connected = connected

    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()

# 🔧 Usage
monitor_internet(on_disconnect, on_connect)

# 🔂 Your main app logic here
print("🟢 Monitoring internet in the background...")
watch_wifi_changes()
while True:
    time.sleep(1)  # Simulating other work