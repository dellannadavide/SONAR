from spade.behaviour import OneShotBehaviour
from spade.message import Message

from sar.agent.workeragent import WorkerAgent


import utils.constants as Constants
from utils.mqttclient import MQTTClient

import utils.utils as utils

class VisionHandler(WorkerAgent):
    class SendMsgToBehaviour(OneShotBehaviour):
        """
        Sends all collected text to the BDI agent
        """

        def __init__(self, receiver):
            super().__init__()
            self.receiver = receiver

        def getVisionInfo(self):
            bel_list_from_oldest_file = []
            nr_rec_in = len(self.agent.received_inputs)
            for i in range(nr_rec_in):
                b = self.agent.received_inputs.pop()
                bel_list_from_oldest_file.append(b)
            return bel_list_from_oldest_file

        async def run(self):
            # print("chatter running the sendmsgtobdibehavior")
            s_list = self.getVisionInfo()
            # print(s_list)
            if len(s_list) > 0:
                for p in s_list:
                    if len(p) > 0:
                        msg_body = p
                        print("sending data as requested")
                        print(msg_body)
                        msg = utils.prepareMessage(self.receiver, Constants.PERFORMATIVE_INFORM, msg_body)
                        await self.send(msg)

    async def send_msg_to(self, receiver, content=None):
        b = self.SendMsgToBehaviour(receiver)
        self.add_behaviour(b)

    def on_message(self, client, userdata, message):
        print("Received message '" + str(message.payload) + "' on topic '"
              + message.topic + "' with QoS " + str(message.qos))
        rec_m = str(message.payload.decode("utf-8"))
        # print("As a VIDEO HANDLER I received data " + rec_m)

        if message.topic == Constants.TOPIC_HUMAN_DETECTION:
            split_m = utils.splitStringToList(rec_m)
            for m in split_m:
                self.received_inputs.append(utils.joinStrings([Constants.TOPIC_HUMAN_DETECTION,m], Constants.STRING_SEPARATOR_INNER))
        elif message.topic == Constants.TOPIC_HEAD_TRACKER:
            split_m = utils.splitStringToList(rec_m)
            for m in split_m:
                self.received_inputs.append(
                    utils.joinStrings([Constants.TOPIC_HEAD_TRACKER,m], Constants.STRING_SEPARATOR_INNER))
        else:
            pass
        # print("received message: ", str(message.payload.decode("utf-8")))
        # self.received_inputs.append(message)

    async def setup(self):
        self.received_inputs = []
        """ This will listen to the sensors collecting data """
        # self.mqtt_listener = MQTTClient(Constants.MQTT_BROKER_ADDRESS, "NAO_VisionHandler_Listener", Constants.MQTT_CLIENT_TYPE_LISTENER, Constants.TOPIC_HUMAN_DETECTION, self.on_message)
        self.mqtt_listener = MQTTClient(Constants.MQTT_BROKER_ADDRESS, "NAO_VisionHandler_Listener", Constants.MQTT_CLIENT_TYPE_LISTENER, Constants.TOPIC_GROUP_VISION+"#", self.on_message)

        await super().setup()