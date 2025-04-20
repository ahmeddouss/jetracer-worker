# jet_robot.py
import asyncio
import cv2
import logging

from jetcam.csi_camera import CSICamera
from jetracer.nvidia_racecar import NvidiaRacecar
from livekit import rtc

logger = logging.getLogger(__name__)


class JetRobot:
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        self.camera = None
        self.car = None
        self.background_tasks = []
        self._video_source = None
        self._video_track = None

    def get_car(self):
        if self.car is None:
            self.car = NvidiaRacecar()
            logger.info("🏎️  Racecar initialized.")
        return self.car

    async def handle_data(self, data: rtc.DataPacket):
        try:
            x, y = [float(part.split(": ")[1]) for part in data.data.decode().split(", ")]
            car = self.get_car()
            car.steering, car.throttle = x, -y
            logger.info(f"Steering: {x:.3f}, Throttle: {-y:.3f}")
        except Exception as e:
            logger.error(f"Failed to parse data: {e}")

    async def send_frames_loop(self, source):
        while True:
            await asyncio.sleep(0.1)
            frame_bgr = self.camera.value
            frame_rgba = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGBA)
            frame_bytes = bytearray(frame_rgba.flatten())
            frame = rtc.VideoFrame(self.width, self.height, rtc.VideoBufferType.RGBA, frame_bytes)
            source.capture_frame(frame)

    async def on_shutdown(self, reason=None):
        logger.info("🔻 Shutting down...")

        if self.camera:
            self.camera.running = False

        for task in self.background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        logger.info("✅ Shutdown complete.")

    async def start(self, ctx):
        self.get_car()
        self.camera = CSICamera(width=self.width, height=self.height)
        self.camera.running = True

        # Setup video source
        self._video_source = rtc.VideoSource(self.width, self.height)
        self._video_track = rtc.LocalVideoTrack.create_video_track("jetson-camera", self._video_source)
        await ctx.agent.publish_track(self._video_track, rtc.TrackPublishOptions(
            source=rtc.TrackSource.SOURCE_CAMERA,
            simulcast=True,
            video_encoding=rtc.VideoEncoding(max_framerate=30, max_bitrate=3_000_000),
            video_codec=rtc.VideoCodec.H264,
        ))

        # Start frame loop
        task = asyncio.create_task(self.send_frames_loop(self._video_source))
        self.background_tasks.append(task)

        ctx.add_shutdown_callback(self.on_shutdown)

        @ctx.room.on("data_received")
        def on_data(data: rtc.DataPacket):
            asyncio.create_task(self.handle_data(data))

    @property
    def video_track(self):
        return self._video_track

    @property
    def video_source(self):
        return self._video_source