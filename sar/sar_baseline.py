import argparse
import logging
import time
import asyncio


from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade_bdi.bdi import BDIAgent

from sar.agent.worker.datacollector import DataColletor
from sar.agent.bdicore import BDICore
from sar.agent.worker.chatter import Chatter
from sar.agent.worker.normadapter import NormAdapter
from sar.agent.worker.normadapter2 import NormAdapter2
from sar.agent.worker.normadapter2SIMnoagent_AGENTIFIED import NormAdapter2SIMnoagent_AGENTIFIED
from sar.agent.worker.normadapterMOEA import NormAdapterMOEA
from sar.agent.worker.positionhandler import PositionHandler
from sar.agent.worker.positionhandlerSIM import PositionHandlerSim
from sar.agent.worker.posturehandler import PostureHandler
from sar.agent.worker.systemhandler import SystemHandler

import utils.constants as Constants
from sar.agent.worker.visionhandler import VisionHandler
from sar.agent.worker.visionhandlerSIM import VisionHandlerSim
# from sar.gui.gui_normadaptivity import GUI_NormAdaptivity
from sar.norm.fuzzysocialinterpreter import FuzzySocialInterpreter
from sar.norm.fuzzysocialqualifier import FuzzySocialQualifier

logger = logging.getLogger("nosar.sar.sar")

spade_agent_logger = logging.getLogger("spade.Agent")
spade_agent_logger.setLevel(logging.WARNING)
spade_behaviour_logger = logging.getLogger("spade.behaviour")
spade_behaviour_logger.setLevel(logging.WARNING)
aiosasl_scram_logger = logging.getLogger("aiosasl.scram")
aiosasl_scram_logger.setLevel(logging.WARNING)

class SARBDIAgent_BASELINE(Agent):

    def __init__(self, jid: str, password: str, verify_security: bool = False, gui_queue = None, workers_to_start : list = []):
        super().__init__(jid, password, verify_security)
        self.gui_queue = gui_queue
        self.workers_to_start = workers_to_start


    class MyBehav(CyclicBehaviour):
        async def on_start(self):
            logger.info("Starting behaviour . . .")
            self.counter = 0

        async def run(self):
            # print("Counter: {}".format(self.counter))
            self.counter += 1
            # r = random()
            # if r>=0.9:
            #     print("person at social distance")
            #     self.agent.bdi_core.bdi.set_belief("distance", "person", "social")
            # else:
            #     print("person at public distance")
            #     self.agent.bdi_core.bdi.set_belief("distance", "person", "public")
            # if self.counter > 3:
            #     # self.kill(exit_code=10)
            #     # return
            #     self.agent.bdi_core.bdi.set_belief("distance", "person", "public")
            #     await asyncio.sleep(1)
            #     self.agent.bdi_core.bdi.print_beliefs()
            # if self.counter > 5:
            #     self.agent.bdi_core.bdi.set_belief("distance", "person", "social")
            #     await asyncio.sleep(1)
            #     self.agent.bdi_core.bdi.print_beliefs()
            await asyncio.sleep(1)

        async def on_end(self):
            logger.info("Behaviour finished with exit code {}.".format(self.exit_code))

    async def setup(self):
        logger.info("Agent starting . . .")
        self.my_behav = self.MyBehav()
        self.add_behaviour(self.my_behav)

        # fuzzy_sets_file = "data/fuzzy_rules/social_interpretation3/fuzzy_sets_multiple_ref.xlsx"
        # ling_vars_file = "data/fuzzy_rules/social_interpretation3/ling_var_multiple_ref2.xlsx"
        # rules_file = "data/fuzzy_rules/social_interpretation3/rules.xlsx"
        # self.fsi = FuzzySocialInterpreter(fuzzy_sets_file, ling_vars_file, rules_file, 0.0) #this is an intraagent element, sort of a database
        # self.fsq = {}
        # for a in Constants.ACTUATION_ASPECTS:
        #     self.fsq[a] = FuzzySocialQualifier(a, fuzzy_sets_file, ling_vars_file, rules_file)

        simulation = False #todo to remove this simulation stuff

        logger.info("Starting all the worker agents...")

        if Constants.SYSTEM_HANDLER_NAME in self.workers_to_start:
            time.sleep(1)
            logger.info("Starting the agent's System Handler ...")
            self.sys_handler = SystemHandler(Constants.SYSTEM_HANDLER_JID, Constants.SYSTEM_HANDLER_PWD)
            await self.sys_handler.start(auto_register=True)

        if Constants.CHATTER_NAME in self.workers_to_start:
            time.sleep(1)
            logger.info("Starting the agent's Chatter ...")
            if simulation:
                self.chatter = Chatter(Constants.CHATTER_JID, Constants.CHATTER_PWD, gui_queue=self.gui_queue)
            else:
                self.chatter = Chatter(Constants.CHATTER_JID, Constants.CHATTER_PWD)
            await self.chatter.start(auto_register=True)

        if Constants.POSITION_HANDLER_NAME in self.workers_to_start:
            time.sleep(1)
            logger.info("Starting the agent's Position Handler ...")
            if simulation:
                self.position_handler = PositionHandlerSim(Constants.POSITION_HANDLER_JID, Constants.POSITION_HANDLER_PWD,
                                                        gui_queue=self.gui_queue)
                await self.position_handler.start(auto_register=True)
            else:
                self.position_handler = PositionHandler(Constants.POSITION_HANDLER_JID, Constants.POSITION_HANDLER_PWD)
                await self.position_handler.start(auto_register=True)

        if Constants.VISION_HANDLER_NAME in self.workers_to_start:
            time.sleep(1)
            logger.info("Starting the agent's Vision Handler ...")
            if simulation:
                self.vision_handler = VisionHandlerSim(Constants.VISION_HANDLER_JID, Constants.VISION_HANDLER_PWD,
                                                        gui_queue=self.gui_queue)
                await self.vision_handler.start(auto_register=True)
            else:
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
            # self.norm_adapter = NormAdapter2SIMnoagent_AGENTIFIED(Constants.NORM_ADAPTER_JID, Constants.NORM_ADAPTER_PWD)
            # await self.norm_adapter.start(auto_register=True)

        logger.info("Starting the agent's BDI core ...")
        bdicore_asl = "sar/basic_baseline.asl"
        self.bdi_core = BDICore(Constants.BDI_CORE_JID, Constants.BDI_CORE_PWD, bdicore_asl)
        await self.bdi_core.start()

