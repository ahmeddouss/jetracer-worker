import logging
from livekit.agents import cli, WorkerOptions, JobRequest, AutoSubscribe
from agent.jet_robot import JetRobot
from agent.vision_assistant import VisionAssistant
from dotenv import load_dotenv
from workers.speaker import play_sound
import os

load_dotenv(dotenv_path=".env")
DOCUMENT_ID = os.getenv("DOCUMENT_ID")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Globals to avoid passing unpickleable objects
async def entrypoint(ctx):
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    if ctx.room.name.startswith(DOCUMENT_ID):
        robot = JetRobot()
        await robot.start(ctx)
    play_sound("jetracer_worker/sounds/start.wav")
    if ctx.room.name.endswith("explore"):
        vision_assistant = VisionAssistant()
        vision_assistant._video_track = robot.video_track
        await vision_assistant.start(ctx)

async def request_fnc(req: JobRequest):
    await req.accept(name="robot", identity="robot")

def start_robot_room():
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        shutdown_process_timeout=15.0,
        request_fnc=request_fnc,
        agent_name="robot",
    ))