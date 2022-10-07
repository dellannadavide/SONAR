import traceback

from spade.behaviour import OneShotBehaviour
from spade.message import Message

from sar.agent.workeragent import WorkerAgent

import chatterbot
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
from chatterbot.trainers import UbuntuCorpusTrainer
from chatterbot import filters

import utils.constants as Constants
from utils.mqttclient import MQTTClient

import utils.utils as utils

class Chatter(WorkerAgent):
    class SendMsgToBehaviour(OneShotBehaviour):
        """
        Sends all collected text to the BDI agent
        """

        def __init__(self, receiver):
            super().__init__()
            self.receiver = receiver

        def getSentences(self):
            bel_list_from_oldest_one = []
            nr_rec_in = len(self.agent.received_inputs)
            for i in range(nr_rec_in):
                b = self.agent.received_inputs.pop()
                bel_list_from_oldest_one.append(b)
            return bel_list_from_oldest_one

        async def run(self):
            # print("chatter running the sendmsgtobdibehavior")
            s_list = self.getSentences()
            # print(s_list)
            if len(s_list) > 0:
                msg_body = s_list
                print("sending data as requested to the datacollector")
                print(msg_body)
                msg = utils.prepareMessage(self.receiver, Constants.PERFORMATIVE_INFORM, msg_body)
                await self.send(msg)

    async def send_msg_to(self, receiver, content=None):
        # print("As a chatter, I received request from the BDI module to send data")
        b = self.SendMsgToBehaviour(receiver)
        self.add_behaviour(b)

    async def do_work(self, work_info):
        to_say = None
        work_info_list = utils.splitStringToList(work_info)
        print("work_info_list", work_info_list)
        if work_info_list[0] == Constants.DIRECTIVE_REPLY_TO:
            # print("Ok BDI told me to reply to "+work_info_list[1])
            message = work_info_list[1].replace(Constants.ASL_STRING_SEPARATOR, " ")
            if not self.gui_queue is None:
                resp = "Hello!"
            else:
                resp = self.getResponseFor(message)
            to_say = str(resp)
            print("response: ")
            print(to_say)
        elif work_info_list[0] == Constants.DIRECTIVE_SAY:
            to_say = work_info_list[1]
        elif work_info_list[0] == Constants.DIRECTIVE_UPDATE_TOPIC_INTEREST:
            self.last_detected_interest = work_info_list[1].replace(Constants.ASL_STRING_SEPARATOR, " ")
            print(self.last_detected_interest)
            # TODO: for the moment I'm only getting a response, but once integrated a more fancy language model perhaps it is possible to do better
            # for example we could give a command to crete a question that asks if the person is interested in ...
            # or something more articulated even
            try:
                resp = self.getResponseFor("I'm interested in "+str(self.last_detected_interest))
            except:
                print(traceback.format_exc())
                resp = None
            to_say = str(resp)
            print("response: ", to_say)
            # print(to_say)

        if not to_say is None:
            # dete-rmine social qualification of behavior
            social_qualifier_inputs = {}
            if len(work_info_list)>2 and (work_info_list[2] == "social_eval"): #todo at some point we need to clean all this stuff with explicit indeces
                sublist = work_info_list[3:len(work_info_list)]
                print(sublist)
                nr_pairs = int(len(sublist)/2)
                print(nr_pairs)
                for i in range(nr_pairs):
                    social_qualifier_inputs[sublist[i*2]] = float(sublist[(i*2)+1])

            print("social qualifier inputs")
            print(social_qualifier_inputs)

            volume = "0.5"
            if not self.fsq is None:
                social_qualification = None
                try:
                    social_qualification = self.fsq[0].getSocialQualification(social_qualifier_inputs)  # here this is is only concerning the position but it should actually refer to all possible inputs that we are interested into, maybe the social itnerpreter should be some other worker independent, which will give back info about social intepretation
                    print("volume_qualification")
                    print(social_qualification)
                except Exception:
                    print(traceback.format_exc())
                if (not social_qualification is None):
                    volume = str(social_qualification["VOLUME"])

            """ do the actual work i.e., send directive to nao """
            self.mqtt_publisher.publish(Constants.TOPIC_DIRECTIVE, "say" + Constants.STRING_SEPARATOR + to_say + Constants.STRING_SEPARATOR + "volume" + Constants.STRING_SEPARATOR + volume)

            # update the gui, if any
            if not self.gui_queue is None: #todo to remove this branch
                self.gui_queue.put(["NAO_GREETS", "True", to_say])


    def getResponseFor(self, text):
        try:
            self.mqtt_publisher.publish(Constants.TOPIC_LEDS,
                                        Constants.DIRECTIVE_LED_CHANGE_COLOR)
            resp = self.chatbot.get_response(text)
            self.mqtt_publisher.publish(Constants.TOPIC_LEDS,
                                        Constants.DIRECTIVE_LED_CHANGE_COLOR)
            return resp
        except:
            print(traceback.format_exc())
            resp = "Uops! Something went wrong. Could you repeat, please?"

    def on_message(self, client, userdata, message):
        rec_m = str(message.payload.decode("utf-8"))
        print("As a chatter I received data " + str(rec_m))
        if self.gui_queue is None:
            self.received_inputs.append(rec_m)
        if not self.gui_queue is None: #todo to remove this branch
            split_m = utils.splitStringToList(rec_m)
            if(str(split_m[0])=="True"):
                self.received_inputs.append("Hello Nao!")
            info_for_gui = ["PERSON_GREETS",
                            str(split_m[0])]
            self.gui_queue.put(info_for_gui)


    async def setup(self):
        """ I create and train the actual chatter"""
        # self.chatbot = ChatBot('Chatter', logic_adapters=['chatterbot.logic.BestMatch',
        #                                                   'chatterbot.logic.MathematicalEvaluation'
        #                                                   # 'chatterbot.logic.TimeLogicAdapter'
        #                                                  ])
        self.chatbot = ChatBot('Chatter', logic_adapters=[
            {
                'import_path': 'chatterbot.logic.BestMatch',
                "statement_comparison_function": "chatterbot.comparisons.levenshtein_distance"
            }
        ])

        # print("Training chatter")
        # self.trainer = ChatterBotCorpusTrainer(self.chatbot)
        # self.trainer.train("chatterbot.corpus.english",
        #                    # "chatterbot.corpus.english.greetings",
        #                    # "chatterbot.corpus.english.conversations",
        #                    "data.chatter.custom")

        #ubuntu corpur traininng takes extremely long and it is currently practically not usable
        # self.trainer = UbuntuCorpusTrainer(self.chatbot)
        # self.trainer.train()

        self.received_inputs = []
        self.last_detected_interest = ""

        """ This will listen to the sensors collecting data """
        self.mqtt_listener = MQTTClient(Constants.MQTT_BROKER_ADDRESS, "NAO_Chatter_Listener", Constants.MQTT_CLIENT_TYPE_LISTENER, Constants.TOPIC_SPEECH, self.on_message)

        """ This will publish what to say in response """
        self.mqtt_publisher = MQTTClient(Constants.MQTT_BROKER_ADDRESS, "NAO_Chatter_Publisher",
                                         Constants.MQTT_CLIENT_TYPE_PUBLISHER, None, None)

        await super().setup()