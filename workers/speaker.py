import subprocess

def play_sound(file_path):
    subprocess.run(["aplay", file_path])
