from jetcam.csi_camera import CSICamera
from jetracer.nvidia_racecar import NvidiaRacecar

camera = CSICamera(width=640, height=480)
car = NvidiaRacecar()