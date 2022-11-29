from spade.behaviour import OneShotBehaviour
from spade.message import Message

from sar.agent.workeragent import WorkerAgent


import utils.constants as Constants
from utils.mqttclient import MQTTClient

import utils.utils as utils

class PositionHandlerSim(WorkerAgent):
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
                msg = utils.prepareMessage(self.agent.jid, self.receiver, Constants.PERFORMATIVE_INFORM, msg_body)
                await self.send(msg)
            # else:
            #     msg_body = Constants.NO_DATA
            #     # print(msg_body)
            #     msg = utils.prepareMessage(self.receiver, Constants.PERFORMATIVE_INFORM, msg_body)
            #     await self.send(msg)

    async def send_msg_to(self, receiver, metadata=None, content=None):
        # print("As a chatter, I received request from the BDI module to send data")
        b = self.SendMsgToBehaviour(receiver)
        self.add_behaviour(b)

    def on_message(self, client, userdata, message):
        rec_m = str(message.payload.decode("utf-8"))
        rec_m_list = utils.splitStringToList(rec_m)
        # store the distance
        self.received_inputs.append(rec_m_list[2])

        if not self.gui_queue is None:

            info_for_gui = ["PERSON_POSITION",
                float(rec_m_list[0]), #x
                float(rec_m_list[1]), #y
                float(rec_m_list[2])] #dist
            self.gui_queue.put(info_for_gui)

            info_for_gui2 = ["NAO_NORM",
                            self.fsq[0].getRuleBase().getMF("mid_distance").param["b"],
                             self.fsq[0].getRuleBase().getMF("mid_distance").param["c"]]
            self.gui_queue.put(info_for_gui2)
            #person_idx, new_p_x, new_p_y, nao_x, nao_y, person_norm, nao_norm, person_greets, nao_greets

    async def setup(self):
        """ I create and train the actual chatter"""
        self.received_inputs = []
        """ This will listen to the sensors collecting data """
        self.mqtt_listener = MQTTClient(Constants.MQTT_BROKER_ADDRESS, "NAO_PositionHandler_Listener", Constants.MQTT_CLIENT_TYPE_LISTENER, Constants.TOPIC_DISTANCE, self.on_message)
        await super().setup()