# jet_robot.py
import asyncio
import cv2
import logging
from livekit import rtc
from workers.camera_motors import  send_frames, observe_camera, unobserve_camera


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


    async def handle_data(self, data: rtc.DataPacket):
        try:
            x, y = [float(part.split(": ")[1]) for part in data.data.decode().split(", ")]
            self.car.steering, self.car.throttle = x, -y
            logger.info(f"Steering: {x:.3f}, Throttle: {-y:.3f}")
        except Exception as e:
            logger.error(f"Failed to parse data: {e}")

    async def on_shutdown(self, reason=None):
        logger.info("🔻 Shutting down...")
        unobserve_camera()
        logger.info("✅ Shutdown complete.")

    async def start(self, ctx):
        observe_camera(lambda change: send_frames(change, self._video_source, self.width, self.height))

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
        asyncio.create_task(self.send_frames_loop(self._video_source))
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