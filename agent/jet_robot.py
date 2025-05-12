# jet_robot.py
import asyncio
import cv2
import logging
from livekit import rtc
from jetcam.csi_camera import CSICamera
from jetracer.nvidia_racecar import NvidiaRacecar
WIDTH = 1920
HEIGHT = 1080


logger = logging.getLogger(__name__)


class JetRobot:
    def __init__(self, width=1920, height=1080):
        self.width = width
        self.height = height
        self.camera = None
        self.car = None
        self.background_tasks = []
        self._video_source = None
        self._video_track = None

    def send_camera_frames(self, change):
        bgr_frame = change['new']
        rgba_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGBA)
        frame_bytes = bytearray(rgba_frame.flatten())
        frame = rtc.VideoFrame(self.width, self.height, rtc.VideoBufferType.RGBA, frame_bytes)
        self._video_source.capture_frame(frame)

    def initOnce(self):
        if not self.car:
            self.car = NvidiaRacecar()
            self.camera = CSICamera(width=self.width, height=self.height)
            self.camera.running = True
            self.camera.observe(self.send_camera_frames, names='value')
            logger.info("   ^=^o^n      ^o  Racecar initialized.")
        return self.car
    

    async def handle_data(self, data: rtc.DataPacket):
        try:
            x, y = [float(part.split(": ")[1]) for part in data.data.decode().split(", ")]
            self.car.steering, self.car.throttle = x, -y
            logger.info(f"Steering: {x:.3f}, Throttle: {-y:.3f}")
        except Exception as e:
            logger.error(f"Failed to parse data: {e}")



    async def start(self, ctx):

        self.initOnce()
        # Setup video source
        self._video_source = rtc.VideoSource(self.width, self.height)
        self._video_track = rtc.LocalVideoTrack.create_video_track("jetson-camera", self._video_source)
        await ctx.agent.publish_track(self._video_track, rtc.TrackPublishOptions(
            source=rtc.TrackSource.SOURCE_CAMERA,
            simulcast=True,
            video_encoding=rtc.VideoEncoding(max_framerate=20, max_bitrate=3_000_000),
            video_codec=rtc.VideoCodec.H264,
        ))
        

        
        # Start frame loop
        
        
        @ctx.room.on("data_received")
        def on_data(data: rtc.DataPacket):
            asyncio.create_task(self.handle_data(data))

    @property
    def video_track(self):
        return self._video_track

    @property
    def video_source(self):
        return self._video_source