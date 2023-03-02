from spade.behaviour import OneShotBehaviour
from spade.message import Message

from mas.agent.workeragent import WorkerAgent


import utils.constants as Constants
from utils.mqttclient import MQTTClient

import utils.utils as utils

from itertools import groupby

import logging
logger = logging.getLogger("nosar.mas.agent.worker.visionhandler")

class VisionHandler(WorkerAgent):
    """ Vision worker agent. deals with all vision-related data.
    e.g., object detection, person detection, emotions, etc.
    These might also include the mined distance of the robot from people. """
    class SendMsgToBehaviour(OneShotBehaviour):
        """
        Sends all collected text to the BDI agent
        """

        def __init__(self, receiver, metadata):
            super().__init__()
            self.receiver = receiver
            self.metadata = metadata


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
                    logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "sending data as requested to the datacollector")
                    logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, s_ordered_dict)
                    msg = utils.prepareMessage(self.agent.jid, self.receiver, Constants.PERFORMATIVE_INFORM, s_ordered_dict, topic, metadata)
                    await self.send(msg)


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
                logger.info("detected objects: {}".format(utils.splitStringToList(obj_list_str, separator=Constants.STRING_SEPARATOR_INNER)))
        elif message.topic == Constants.TOPIC_EMOTION_DETECTION:
            split_m = utils.splitStringToList(rec_m)
            for em in split_m:
                self.to_process_received_inputs[Constants.TOPIC_EMOTION_DETECTION].append(
                    utils.joinStrings([Constants.TOPIC_EMOTION_DETECTION, em],
                                      Constants.STRING_SEPARATOR_INNER))
                logger.info("detected emotion: {}".format(
                      utils.splitStringToList(em, separator=Constants.STRING_SEPARATOR_INNER)))
                self.processReceivedInputs()
        else:
            pass
        # print("received message: ", str(message.payload.decode("utf-8")))
        # self.received_inputs.append(message)

    def processReceivedInputs(self):
        for topic in self.to_process_received_inputs.keys():
            num_received_inputs_topic = len(self.to_process_received_inputs[topic])
            if num_received_inputs_topic > 0:
                if topic==Constants.TOPIC_EMOTION_DETECTION:
                    # I actually report to the data collector a particular emotion only if
                    # 1. I collected at least self.emotions_min_number data points
                    # 2. there is one emotion among the collected data points that appears more than self.main_emotion_min_ratio % of times
                    if num_received_inputs_topic >= self.emotions_min_number:
                        dict_count_emotions = {key: len(list(group)) for key, group in groupby(sorted(self.to_process_received_inputs[topic]))}
                        actually_detected_emotion = False
                        for em in dict_count_emotions.keys():
                            if ((dict_count_emotions[em] / num_received_inputs_topic)>= self.main_emotion_min_ratio) and (not em=="neutral"):
                                self.received_inputs[topic].append(em)
                                actually_detected_emotion = True
                                break
                        if actually_detected_emotion: #if I added an emotion I erase everything from to_process, so new data will need to be collected
                            self.to_process_received_inputs[topic] = []
    async def setup(self):
        self.received_inputs = {
            Constants.TOPIC_HUMAN_DETECTION: [],
            Constants.TOPIC_HEAD_TRACKER: [],
            Constants.TOPIC_OBJECT_DETECTION: [],
            Constants.TOPIC_EMOTION_DETECTION: []
        }

        self.to_process_received_inputs = {
            Constants.TOPIC_HUMAN_DETECTION: [],
            Constants.TOPIC_HEAD_TRACKER: [],
            Constants.TOPIC_OBJECT_DETECTION: [],
            Constants.TOPIC_EMOTION_DETECTION: []
        }
        self.emotions_min_number = 30 #this means I need to collect at least 30 data points about emotion
        self.main_emotion_min_ratio = 0.5 #and in at least 50% of the case (i.e., in the majority, i.e., if 30 then at least 15 of them) they should all about the same emotion
        """ This will listen to the sensors collecting data """
        # self.mqtt_listener = MQTTClient(Constants.MQTT_BROKER_ADDRESS, "NAO_VisionHandler_Listener", Constants.MQTT_CLIENT_TYPE_LISTENER, Constants.TOPIC_HUMAN_DETECTION, self.on_message)
        self.mqtt_listener = MQTTClient(Constants.MQTT_BROKER_ADDRESS, "NAO_VisionHandler_Listener", Constants.MQTT_CLIENT_TYPE_LISTENER, Constants.TOPIC_GROUP_VISION+"#", self.on_message)

        await super().setup()