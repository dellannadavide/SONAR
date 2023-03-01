import logging
import time
import asyncio


from spade.agent import Agent
from spade.behaviour import CyclicBehaviour

from mas.agent.worker.datacollector import DataColletor
from mas.agent.bdicore import BDICore
from mas.agent.worker.chatter import Chatter
from mas.agent.worker.positionhandler import PositionHandler
from mas.agent.worker.stuff.positionhandlerSIM import PositionHandlerSim
from mas.agent.worker.posturehandler import PostureHandler
from mas.agent.worker.systemhandler import SystemHandler

import utils.constants as Constants
from mas.agent.worker.visionhandler import VisionHandler
from mas.agent.worker.stuff.visionhandlerSIM import VisionHandlerSim
# from mas.gui.gui_normadaptivity import GUI_NormAdaptivity

logger = logging.getLogger("nosar.mas.mas")

spade_agent_logger = logging.getLogger("spade.Agent")
spade_agent_logger.setLevel(logging.WARNING)
spade_behaviour_logger = logging.getLogger("spade.behaviour")
spade_behaviour_logger.setLevel(logging.WARNING)
aiosasl_scram_logger = logging.getLogger("aiosasl.scram")
aiosasl_scram_logger.setLevel(logging.WARNING)

class MAS_BASELINE(Agent):
    """
    The class representing the MAS (Multi Agent System) where the BDI agent and the worker and manager agents operate.
    MAS_BASELINE is the version of the MAS for the BASELINE experiments where no social and norm reasoning happens.

    Technically the MAS is also an agent itself.
    """

    def __init__(self, jid: str, password: str, verify_security: bool = False, gui_queue = None, asl_file : str = None, workers_to_start : list = []):
        super().__init__(jid, password, verify_security)
        self.gui_queue = gui_queue
        self.asl_file = asl_file
        self.workers_to_start = workers_to_start


    class MyBehav(CyclicBehaviour):
        async def on_start(self):
            logger.info("Starting behaviour . . .")
            self.counter = 0

        async def run(self):
            self.counter += 1
            await asyncio.sleep(1)

        async def on_end(self):
            logger.info("Behaviour finished with exit code {}.".format(self.exit_code))

    async def setup(self):
        logger.info("Agent starting . . .")
        self.my_behav = self.MyBehav()
        self.add_behaviour(self.my_behav)

        logger.info("Starting all the worker agents...")

        if Constants.SYSTEM_HANDLER_NAME in self.workers_to_start:
            time.sleep(1)
            logger.info("Starting the agent's System Handler ...")
            self.sys_handler = SystemHandler(Constants.SYSTEM_HANDLER_JID, Constants.SYSTEM_HANDLER_PWD)
            await self.sys_handler.start(auto_register=True)

        if Constants.CHATTER_NAME in self.workers_to_start:
            time.sleep(1)
            logger.info("Starting the agent's Chatter ...")
            self.chatter = Chatter(Constants.CHATTER_JID, Constants.CHATTER_PWD)
            await self.chatter.start(auto_register=True)

        if Constants.POSITION_HANDLER_NAME in self.workers_to_start:
            time.sleep(1)
            logger.info("Starting the agent's Position Handler ...")
            self.position_handler = PositionHandler(Constants.POSITION_HANDLER_JID, Constants.POSITION_HANDLER_PWD)
            await self.position_handler.start(auto_register=True)

        if Constants.VISION_HANDLER_NAME in self.workers_to_start:
            time.sleep(1)
            logger.info("Starting the agent's Vision Handler ...")
            self.vision_handler = VisionHandler(Constants.VISION_HANDLER_JID, Constants.VISION_HANDLER_PWD)
            await self.vision_handler.start(auto_register=True)

        if Constants.POSTURE_HANDLER_NAME in self.workers_to_start:
            time.sleep(1)
            logger.info("Starting the agent's Posture Handler ...")
            self.posture_handler = PostureHandler(Constants.POSTURE_HANDLER_JID, Constants.POSTURE_HANDLER_PWD)
            await self.posture_handler.start(auto_register=True)

        if Constants.DATA_COLLECTOR_NAME in self.workers_to_start:
            time.sleep(1)
            logger.info("Starting the agent's Data Collector ...")
            self.collector = DataColletor(Constants.DATA_COLLECTOR_JID, Constants.DATA_COLLECTOR_PWD)
            await self.collector.start(auto_register=True)

        if Constants.NORM_ADAPTER_NAME in self.workers_to_start:
            time.sleep(1)
            # logger.info("Starting the agent's NormAdapter ...")
            # self.norm_adapter = NormAdapter(Constants.NORM_ADAPTER_JID, Constants.NORM_ADAPTER_PWD)
            # await self.norm_adapter.start(auto_register=True)

        logger.info("Starting the agent's BDI core ...")
        self.bdi_core = BDICore(Constants.BDI_CORE_JID, Constants.BDI_CORE_PWD, self.asl_file)
        await self.bdi_core.start()

