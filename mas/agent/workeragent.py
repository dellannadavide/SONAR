import logging
from abc import abstractmethod

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour

import utils.constants as Constants
import utils.utils as utils

logger = logging.getLogger("sonar.mas.agent.workeragent")

class WorkerAgent(Agent):
    """
    A class representing a Worker Agent. A type of agent that can interact with the external world via MQTT,
    and internally with other agents via message passing.
    """

    def __init__(self, jid: str, password: str, verify_security: bool = False, fsi=None, fsq=None, gui_queue=None):
        """
        Init of the agent
        :param jid: the jid of the SPADE agent
        :param password: the pwd of the SPADE agent
        :param verify_security:
        :param fsi: an instance of FuzzySocialInterpreter used by the agent to attribute social interpretation to physical inputs
        :param fsq: an instance of FuzzySocialQualifier used by the agent to appropriately qualify actions
        :param gui_queue:
        """
        super().__init__(jid, password, verify_security)
        self.fsi = fsi # fuzzy social interpreter (None if not needed by the particular worker)
        self.fsq = fsq # fuzzy social qualifier (None if not needed, otherwise a list of fuzzy systems)
        self.gui_queue = gui_queue

    class ListenBehavior(CyclicBehaviour):
        """
        Every worker agent has at least one listenbehavior
        this behavior cyclically waits for a message
        - if the message is a REQUEST, then the agent calls function send_msg_to
        - if the message is an INFORM, the agent calls function do_work
        both send_msg_to and do_work functions are worker-specific.
        Typically, REQUEST is used by other agents to request info from the agent,
        while INFORM is used mainly by the BDI agent to give directives to the agent
        """
        async def run(self):
            msg = await self.receive(timeout=10)  # wait for a message for 10 seconds
            if msg:
                performative = msg.get_metadata(Constants.SPADE_MSG_METADATA_PERFORMATIVE)
                if performative == Constants.PERFORMATIVE_REQUEST:
                    await self.agent.send_msg_to(str(msg.sender), metadata=msg.metadata)
                elif performative == Constants.PERFORMATIVE_INFORM:
                    await self.agent.do_work(utils.readMessage(msg.body, msg.metadata))
                else:
                    logger.log(Constants.LOGGING_LV_DEBUG_SONAR, str(msg.sender)+", you are telling me something I don't understand...")
                    logger.log(Constants.LOGGING_LV_DEBUG_SONAR, msg.body)

    async def setup(self):
        b = self.ListenBehavior()
        self.add_behaviour(b)

    @abstractmethod
    async def send_msg_to(self, receiver, metadata=None, content=None):
        pass

    @abstractmethod
    async def do_work(self, work_info_dict):
        pass


