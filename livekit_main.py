# main.py
import logging
from livekit.agents import cli, WorkerOptions, JobRequest, AutoSubscribe
from workers.jet_robot import JetRobot
from agent.vision_assistant import VisionAssistant
from dotenv import load_dotenv
from workers.speaker import play_sound
import os
load_dotenv(dotenv_path=".env")
DOCUMENT_ID = os.getenv("DOCUMENT_ID")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


robot = JetRobot()

async def entrypoint(ctx):
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    if ctx.room.name.startswith(DOCUMENT_ID):
        await robot.start(ctx)

    if ctx.room.name.endswith("explore"):
        vision_assistant = VisionAssistant()
        vision_assistant._video_track = robot.video_track
        await vision_assistant.start(ctx)

async def request_fnc(req: JobRequest):
    await req.accept(name="robot", identity="robot")

if __name__ == "__main__":
    play_sound("sounds/ready.wav")
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        shutdown_process_timeout=15.0,
        request_fnc=request_fnc,
        agent_name="robot",
    ))