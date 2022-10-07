
from spade.behaviour import OneShotBehaviour
from spade.message import Message
from sar.agent.workeragent import WorkerAgent
from utils.mqttclient import MQTTClient

import utils.utils as utils
import utils.constants as Constants

class SystemHandler(WorkerAgent):
    async def setup(self):
        self.mqtt_client = MQTTClient(Constants.MQTT_BROKER_ADDRESS, "NAO_SystemHandler_Publisher",
                                         Constants.MQTT_CLIENT_TYPE_PUBLISHER, None, None)
        await super().setup()

    async def do_work(self, work_info):
        work_info_list = utils.splitStringToList(work_info)
        print(work_info_list)
        if work_info_list[0] == Constants.DIRECTIVE_SHUT_DOWN:
            self.mqtt_client.publish(Constants.TOPIC_DIRECTIVE, Constants.DIRECTIVE_SHUT_DOWN)
        if work_info_list[0] == Constants.DIRECTIVE_EXEC_BEHAVIOR:
            print("sending directive to execute behavior")
            self.mqtt_client.publish(Constants.TOPIC_BEHAVIOR, Constants.DIRECTIVE_EXEC_BEHAVIOR)