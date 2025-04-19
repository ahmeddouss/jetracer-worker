# main.py
import logging
from livekit.agents import cli, WorkerOptions, JobRequest, AutoSubscribe
from workers.jet_robot import JetRobot
from agent.vision_assistant import VisionAssistant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

robot = JetRobot()

async def entrypoint(ctx):
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    if ctx.room.name.startswith("id-robot"):
        await robot.start(ctx)

    if ctx.room.name.endswith("explore"):
        vision_assistant = VisionAssistant()
        vision_assistant._video_track = robot.video_track
        await vision_assistant.start(ctx)

async def request_fnc(req: JobRequest):
    await req.accept(name="robot", identity="robot")

if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        shutdown_process_timeout=15.0,
        request_fnc=request_fnc,
        agent_name="robot",
    ))