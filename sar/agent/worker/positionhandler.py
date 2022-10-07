from spade.behaviour import OneShotBehaviour
from spade.message import Message

from sar.agent.workeragent import WorkerAgent


import utils.constants as Constants
from utils.mqttclient import MQTTClient

import utils.utils as utils

class PositionHandler(WorkerAgent):
    class SendMsgToBehaviour(OneShotBehaviour):
        """
        Sends all collected text to the BDI agent
        """

        def __init__(self, receiver):
            super().__init__()
            self.receiver = receiver

        def getDistances(self):
            bel_list_from_oldest_file = []
            nr_rec_in = len(self.agent.received_inputs)
            for i in range(nr_rec_in):
                b = self.agent.received_inputs.pop()
                bel_list_from_oldest_file.append(b)
            return bel_list_from_oldest_file

        async def run(self):
            # print("chatter running the sendmsgtobdibehavior")
            s_list = self.getDistances()
            # print(s_list)
            if len(s_list) > 0:
                msg_body = s_list
                # print("sending data as requested to the bdi")
                msg = utils.prepareMessage(self.receiver, Constants.PERFORMATIVE_INFORM, msg_body)
                await self.send(msg)

    async def send_msg_to(self, receiver, content=None):
        # print("As a chatter, I received request from the BDI module to send data")
        b = self.SendMsgToBehaviour(receiver)
        self.add_behaviour(b)

    def on_message(self, client, userdata, message):
        rec_m = str(message.payload.decode("utf-8"))
        # print("position handler: received message ", rec_m)
        self.received_inputs.append(rec_m)

    async def setup(self):
        """ I create and train the actual chatter"""
        self.received_inputs = []
        """ This will listen to the sensors collecting data """
        self.mqtt_listener = MQTTClient(Constants.MQTT_BROKER_ADDRESS, "NAO_PositionHandler_Listener", Constants.MQTT_CLIENT_TYPE_LISTENER, Constants.TOPIC_DISTANCE, self.on_message)
        await super().setup()