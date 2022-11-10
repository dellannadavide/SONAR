
from spade.behaviour import OneShotBehaviour
from spade.message import Message
from sar.agent.workeragent import WorkerAgent
from utils.mqttclient import MQTTClient

import utils.utils as utils
import utils.constants as Constants

import logging
logger = logging.getLogger("nosar.sar.agent.worker.systemhandler")

class SystemHandler(WorkerAgent):
    async def setup(self):
        self.mqtt_client = MQTTClient(Constants.MQTT_BROKER_ADDRESS, "NAO_SystemHandler_Publisher",
                                         Constants.MQTT_CLIENT_TYPE_PUBLISHER, None, None)
        await super().setup()

    async def do_work(self, work_info_dict):
        if work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_SHUT_DOWN:
            self.mqtt_client.publish(Constants.TOPIC_DIRECTIVE, Constants.DIRECTIVE_SHUT_DOWN)
        if work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_EXEC_BEHAVIOR:
            logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "sending directive to execute behavior")
            self.mqtt_client.publish(Constants.TOPIC_BEHAVIOR, Constants.DIRECTIVE_EXEC_BEHAVIOR)