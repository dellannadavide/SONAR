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

        def __init__(self, receiver, metadata):
            super().__init__()
            self.receiver = receiver
            self.metadata = metadata

        # def getVisionInfo(self, topic):
        #     bel_list_from_oldest_one = []
        #     nr_rec_in = len(self.agent.received_inputs[topic])
        #     for i in range(nr_rec_in):
        #         b = self.agent.received_inputs[topic].pop()
        #         bel_list_from_oldest_one.append(b)
        #     return bel_list_from_oldest_one

        def getVisionInfo(self, topic):
            vision_info_dict_with_ordered_keys_from_oldest = {}
            nr_rec_in = len(self.agent.received_inputs[topic])
            for i in range(nr_rec_in):
                b = self.agent.received_inputs[topic].pop()  # extraction with removal
                vision_info_dict_with_ordered_keys_from_oldest[i] = b
            return vision_info_dict_with_ordered_keys_from_oldest


        async def run(self):
            # print("chatter running the sendmsgtobdibehavior")
            metadata = {Constants.SPADE_MSG_METADATA_KEYS_TYPE: "int"}
            if not self.metadata is None:
                if Constants.SPADE_MSG_BATCH_ID in self.metadata:
                    metadata[Constants.SPADE_MSG_BATCH_ID] = self.metadata[Constants.SPADE_MSG_BATCH_ID]
            # print(s_list)

            for topic in self.agent.received_inputs.keys():
                s_ordered_dict = self.getVisionInfo(topic)
                if len(s_ordered_dict.keys()) > 0:
                    print("sending data as requested to the datacollector")
                    print(s_ordered_dict)
                    msg = utils.prepareMessage(self.agent.jid, self.receiver, Constants.PERFORMATIVE_INFORM, s_ordered_dict, topic, metadata)
                    await self.send(msg)
        #
        # async def run(self):
        #     # print("chatter running the sendmsgtobdibehavior")
        #     metadata = None
        #     if not self.metadata is None:
        #         if "batch" in self.metadata:
        #             metadata = {"batch": self.metadata["batch"]}
        #
        #     for topic in self.agent.received_inputs.keys():
        #         s_list = self.getVisionInfo(topic)
        #         # print(s_list)
        #         if len(s_list) > 0:
        #             for p in s_list:
        #                 if len(p) > 0:
        #                     msg_body = p
        #                     # print("sending data as requested")
        #                     # print(msg_body)
        #                     msg = utils.prepareMessage(self.receiver, Constants.PERFORMATIVE_INFORM, msg_body, topic, metadata)
        #                     await self.send(msg)
        #     # else:
        #     #     msg_body = Constants.NO_DATA
        #     #     # print(msg_body)
        #     #     msg = utils.prepareMessage(self.receiver, Constants.PERFORMATIVE_INFORM, msg_body)
        #     #     await self.send(msg)

    async def send_msg_to(self, receiver, metadata=None, content=None):
        b = self.SendMsgToBehaviour(receiver, metadata)
        self.add_behaviour(b)

    def on_message(self, client, userdata, message):
        # print("Received message '" + str(message.payload) + "' on topic '"
        #       + message.topic + "' with QoS " + str(message.qos))
        rec_m = str(message.payload.decode("utf-8"))
        # print("As a VIDEO HANDLER I received data " + rec_m)

        if message.topic == Constants.TOPIC_HUMAN_DETECTION:
            split_m = utils.splitStringToList(rec_m)
            for m in split_m:
                self.received_inputs[Constants.TOPIC_HUMAN_DETECTION].append(utils.joinStrings([Constants.TOPIC_HUMAN_DETECTION,m], Constants.STRING_SEPARATOR_INNER))
        elif message.topic == Constants.TOPIC_HEAD_TRACKER:
            split_m = utils.splitStringToList(rec_m)
            for m in split_m:
                self.received_inputs[Constants.TOPIC_HEAD_TRACKER].append(
                    utils.joinStrings([Constants.TOPIC_HEAD_TRACKER,m], Constants.STRING_SEPARATOR_INNER))
        elif message.topic == Constants.TOPIC_OBJECT_DETECTION:
            split_m = utils.splitStringToList(rec_m)
            for obj_list_str in split_m:
                self.received_inputs[Constants.TOPIC_OBJECT_DETECTION].append(
                    utils.joinStrings([Constants.TOPIC_OBJECT_DETECTION, obj_list_str], Constants.STRING_SEPARATOR_INNER))
                print("detected objects: ", utils.splitStringToList(obj_list_str, separator=Constants.STRING_SEPARATOR_INNER))
        elif message.topic == Constants.TOPIC_EMOTION_DETECTION:
            split_m = utils.splitStringToList(rec_m)
            for em in split_m:
                self.received_inputs[Constants.TOPIC_EMOTION_DETECTION].append(
                    utils.joinStrings([Constants.TOPIC_EMOTION_DETECTION, em],
                                      Constants.STRING_SEPARATOR_INNER))
                print("detected emotion: ",
                      utils.splitStringToList(em, separator=Constants.STRING_SEPARATOR_INNER))
        else:
            pass
        # print("received message: ", str(message.payload.decode("utf-8")))
        # self.received_inputs.append(message)

    async def setup(self):
        self.received_inputs = {
            Constants.TOPIC_HUMAN_DETECTION: [],
            Constants.TOPIC_HEAD_TRACKER: [],
            Constants.TOPIC_OBJECT_DETECTION: [],
            Constants.TOPIC_EMOTION_DETECTION: []
        }
        """ This will listen to the sensors collecting data """
        # self.mqtt_listener = MQTTClient(Constants.MQTT_BROKER_ADDRESS, "NAO_VisionHandler_Listener", Constants.MQTT_CLIENT_TYPE_LISTENER, Constants.TOPIC_HUMAN_DETECTION, self.on_message)
        self.mqtt_listener = MQTTClient(Constants.MQTT_BROKER_ADDRESS, "NAO_VisionHandler_Listener", Constants.MQTT_CLIENT_TYPE_LISTENER, Constants.TOPIC_GROUP_VISION+"#", self.on_message)

        await super().setup()