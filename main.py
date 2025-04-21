import threading
import time
import socket
import signal
import sys
from workers.speaker import play_sound
from livekit_room import start_robot_room
from workers.camera_motors import camera, car

started_camera = camera
started_camera.running = True  # Start the camera
started_car = car

first_disconnect = True
should_exit = False  # Used to control main loop and threads


def on_disconnect():
    global first_disconnect
    if first_disconnect:
        play_sound("jetracer_worker/sounds/failed.wav")
        first_disconnect = False
    else:
        play_sound("jetracer_worker/sounds/lost.wav")


def on_connect():
    global first_disconnect
    first_disconnect = False
    play_sound("jetracer_worker/sounds/connected.wav")


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

        while not should_exit:
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
    return thread


def cleanup():
    print("Cleaning up...")
    started_camera.running = False
    # Add any other cleanup logic here (e.g., stopping motors, saving logs, etc.)
    sys.exit(0)


def signal_handler(sig, frame):
    global should_exit
    print("\nReceived Ctrl+C, exiting...")
    should_exit = True
    cleanup()


# Attach the signal handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Start Internet monitor
monitor_internet(on_disconnect, on_connect)

start_robot_room()


# Main loop
try:
    while not should_exit:
        time.sleep(1)
except KeyboardInterrupt:
    signal_handler(None, None)