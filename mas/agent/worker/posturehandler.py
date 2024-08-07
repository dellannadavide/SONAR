from spade.behaviour import OneShotBehaviour
from spade.message import Message
from mas.agent.workeragent import WorkerAgent
from utils.mqttclient import MQTTClient

import utils.utils as utils
import utils.constants as Constants

import logging
logger = logging.getLogger("sonar.mas.agent.worker.posturehandler")

class PostureHandler(WorkerAgent):
    """ Worker agent that can handle posture-related tasks (e.g., looking up)"""
    async def setup(self):
        self.mqtt_client = MQTTClient(Constants.MQTT_BROKER_ADDRESS, "NAO_PostureHandler_Publisher",
                                         Constants.MQTT_CLIENT_TYPE_PUBLISHER, None, None)
        await super().setup()
    async def do_work(self, work_info_dict):
        # work_info_list = utils.splitStringToList(work_info)
        # print(work_info_list)
        if work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_GOTOPOSTURE:
            self.mqtt_client.publish(Constants.TOPIC_POSTURE,
                                     Constants.DIRECTIVE_GOTOPOSTURE + Constants.STRING_SEPARATOR + str(
                                         work_info_dict[Constants.SPADE_MSG_POSTURE]))
        if work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_PLAYANIMATION:
            self.mqtt_client.publish(Constants.TOPIC_POSTURE, Constants.DIRECTIVE_PLAYANIMATION + Constants.STRING_SEPARATOR + str(work_info_dict[Constants.SPADE_MSG_POSTURE]))
        if work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_MOVEHEAD:
            person_is_looking = work_info_dict[Constants.SPADE_MSG_POSTURE]

            animation = "look" + \
                        ("_bottom" if Constants.ASL_FLUENT_BOTTOM_DIRECTION in person_is_looking else ("_top" if Constants.ASL_FLUENT_TOP_DIRECTION in person_is_looking else "_bottom")) +  \
                        ("_left" if Constants.ASL_FLUENT_RIGHT_DIRECTION in person_is_looking else ("_right" if Constants.ASL_FLUENT_LEFT_DIRECTION in person_is_looking else ""))
            if animation=="look":
                logging.warning("!!!FOR SOME REASON i got no direction, only animation=='look'")
            else:
                self.mqtt_client.publish(Constants.TOPIC_POSTURE,
                                         utils.joinStrings([Constants.DIRECTIVE_PLAYANIMATION, animation]))


        # self.mqtt_client.publish(Constants.TOPIC_LEDS,
        #                             utils.joinStrings(
        #                                 [Constants.DIRECTIVE_LED_SET_COLOR, Constants.COLORS_WHITE]))

