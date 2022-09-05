from spade.behaviour import OneShotBehaviour
from spade.message import Message
from sar.agent.workeragent import WorkerAgent
from utils.mqttclient import MQTTClient

import utils.utils as utils
import utils.constants as Constants

class PostureHandler(WorkerAgent):
    async def setup(self):
        self.mqtt_client = MQTTClient(Constants.MQTT_BROKER_ADDRESS, "NAO_PostureHandler_Publisher",
                                         Constants.MQTT_CLIENT_TYPE_PUBLISHER, None, None)
        await super().setup()

    async def do_work(self, work_info):
        work_info_list = utils.splitStringToList(work_info)
        print(work_info_list)
        if work_info_list[0] == Constants.DIRECTIVE_GOTOPOSTURE:
            self.mqtt_client.publish(Constants.TOPIC_POSTURE, Constants.DIRECTIVE_GOTOPOSTURE + Constants.STRING_SEPARATOR + str(work_info_list[1]))