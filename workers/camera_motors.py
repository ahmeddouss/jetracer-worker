from jetcam.csi_camera import CSICamera
from jetracer.nvidia_racecar import NvidiaRacecar
import cv2
from livekit import rtc

camera = CSICamera(width=640, height=480)
car = NvidiaRacecar()

def send_frames(change, video_source, width=640, height=480):
    frame_bgr = change['new']
    frame_rgba = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGBA)
    frame_bytes = bytearray(frame_rgba.flatten())
    frame = rtc.VideoFrame(width, height, rtc.VideoBufferType.RGBA, frame_bytes)
    video_source.capture_frame(frame)

def observe_camera(callback):
    camera.running = True
    camera.observe(callback, names='value')

def unobserve_camera():
    camera.unobserve()