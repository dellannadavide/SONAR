import datetime
import getpass
import os
import time
from random import random

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

import simpful as sf
from simpful import *


import paho.mqtt.client as mqtt
import time

# from chatterbot import ChatBot
# from chatterbot.trainers import ChatterBotCorpusTrainer
# from chatterbot.trainers import UbuntuCorpusTrainer
# from chatterbot import filters

import utils.constants as Constants
from sar.norm.fuzzysocialinterpreter import FuzzySocialInterpreter
from utils.mqttclient import MQTTClient

from abc import abstractmethod
import utils.utils as utils
import json

import logging
logger = logging.getLogger("nosar.sar.agent.workeragent")

class WorkerAgent(Agent):

    def __init__(self, jid: str, password: str, verify_security: bool = False, fsi=None, fsq=None, gui_queue=None):
        super().__init__(jid, password, verify_security)
        self.fsi = fsi #fuzzy social interpreter (None if not needed by the particular worker)
        self.fsq = fsq #fuzzy social qualifier (None if not needed, otherwise a list of fuzzy systems)
        self.gui_queue = gui_queue

    class ListenBehavior(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)  # wait for a message for 10 seconds
            if msg:
                performative = msg.get_metadata(Constants.SPADE_MSG_METADATA_PERFORMATIVE)
                if performative == Constants.PERFORMATIVE_REQUEST:
                    await self.agent.send_msg_to(str(msg.sender), metadata=msg.metadata)
                elif performative == Constants.PERFORMATIVE_INFORM:
                    await self.agent.do_work(utils.readMessage(msg.body, msg.metadata))
                else:
                    logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, str(msg.sender)+", you are telling me something I don't understand...")
                    logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, msg.body)


        # async def on_end(self):
        #     # stop agent from behaviour
        #     print("Stopping ListenToBDIBehavior...")
        #     await self.agent.stop()

    async def setup(self):
        b = self.ListenBehavior()
        self.add_behaviour(b)

    @abstractmethod
    async def send_msg_to(self, receiver, metadata=None, content=None):
        pass

    @abstractmethod
    async def do_work(self, work_info_dict):
        pass


