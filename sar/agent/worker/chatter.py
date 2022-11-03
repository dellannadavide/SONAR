import copy
import random
import threading
import traceback

from spade.behaviour import OneShotBehaviour
from spade.message import Message

from sar.agent.workeragent import WorkerAgent

# import chatterbot
# from chatterbot import ChatBot
# from chatterbot.trainers import ChatterBotCorpusTrainer
# from chatterbot.trainers import UbuntuCorpusTrainer
# from chatterbot import filters

import utils.constants as Constants
from sar.utils.news import getRandomNewsFromBBC
from sar.utils.weather import getCurrentWeather
from utils.mqttclient import MQTTClient

import utils.utils as utils

from transformers import pipeline

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

from transformers.utils import logging

from abc import abstractmethod
import spacy
from statemachine import StateMachine, State


class Chatter(WorkerAgent):
    _TASK_CONTINUE_CONVERSATION = "continue_conversation"
    _TASK_ASK_QUESTION = "ask_question"
    _TASK_CONTINUE_CONVERSATION_SPONTANEOUS = "spontaneous_continuation_conversation"
    _TASK_CONVERSATION_TURN_SPONTANEOUS = "spontaneous_conversation_turn"
    _QUESTION_TOPIC_TEXT = "about_text"
    _QUESTION_TOPIC_SUMMARY = "summary_conversation"
    _QUESTION_TOPIC_NEWS = "news"
    _QUESTION_TOPIC_WEATHER = "weather"
    _QUESTION_TOPIC_RANDOM = "random"

    class ChatterStateMachine(StateMachine):
        def __init__(self, chatter) -> None:
            super().__init__()
            self.chatter = chatter
            self.name = ""
            self.temp_name = ""
            self.first_retrieval = True

        def setup(self, nlp):
            self.name_retrieval.setNLP(nlp)
            self.name_confirmation.setNLP(nlp)

        class ChatterState(State):
            @abstractmethod
            def process_input(self, user_input: str):
                pass

        class DefaultChatterState(ChatterState):
            def process_input(self, user_input):
                return None

        class NameRetrievalState(ChatterState):
            def __init__(self, name, value=None, initial=False, nlp=None):
                super().__init__(name, value, initial)
                self.nlp = nlp

            def setNLP(self, nlp):
                self.nlp = nlp

            def process_input(self, user_input):
                detected_name = None
                if not self.nlp is None:
                    doc = self.nlp(user_input)
                    for token in doc:
                        if token.pos_ == "PROPN":
                            detected_name = token.text
                return detected_name

        class NameConfirmationState(ChatterState):
            def __init__(self, name, value=None, initial=False, nlp=None):
                super().__init__(name, value, initial)
                self.nlp = nlp

            def setNLP(self, nlp):
                self.nlp = nlp

            def isYesNoUnclearAnswer(self, text):
                doc = self.nlp(text.lower())
                evidence_positive = False
                evidence_negative = False
                for token in doc:
                    if token.text in Constants.SPEECH_KEYWORDS_AFFIRMATIVE:
                        evidence_positive = True
                    if token.text in Constants.SPEECH_KEYWORDS_NEGATIVE:
                        evidence_negative = True
                if evidence_positive and not evidence_negative:
                    return "yes"
                elif evidence_negative and not evidence_positive:
                    return "no"
                else:
                    return "unclear"

            def process_input(self, user_input):
                return self.isYesNoUnclearAnswer(user_input)

        # States
        default = DefaultChatterState('Default', initial=True)
        name_retrieval = NameRetrievalState('Retrieving Person Name')
        name_confirmation = NameConfirmationState('Confirming Person Name')

        end_name_retrieval_negative = name_retrieval.to(default)

        def possibly_end_retrieval(self):
            if self.is_name_retrieval and self.first_retrieval:
                to_say = "Nevermind."
                # self.chatter.converser.addBotResponseToConversation(to_say, True)
                self.chatter.qualifyAndSendResponse(to_say, {}, True)
                self.chatter.inputs_being_processed = self.chatter.inputs_being_processed - 1
                print("---------- INPUTS BEING PROCESSED, AFTER SAYING NEVERMIND ", self.chatter.inputs_being_processed)
                self.end_name_retrieval_negative()


        # State Transitions, and associated events
        retrieve_name = default.to(name_retrieval)

        def on_retrieve_name(self):
            delay = 60
            start_time = threading.Timer(delay, self.possibly_end_retrieval)
            start_time.start()

        confirm_name = name_retrieval.to(name_confirmation)

        def on_confirm_name(self):
            to_say = "Your name is "+str(self.temp_name)+", correct?"
            # self.chatter.converser.addBotResponseToConversation(to_say, False)
            self.chatter.qualifyAndSendResponse(to_say, {}, False)

        repeat_name = name_confirmation.to(name_retrieval)

        def on_repeat_name(self):
            to_say = "Alright, can you repeat your name then?"
            # self.chatter.converser.addBotResponseToConversation(to_say, False)
            self.chatter.qualifyAndSendResponse(to_say, {}, False)

        end_name_retrieval_positive = name_confirmation.to(default)

        def on_end_name_retrieval_positive(self):
            to_say = "Got it! Nice to meet you "+ str(self.name)+"!"
            self.chatter.received_inputs[Constants.TOPIC_NAME_LEARNT].append(str(self.name))
            # self.chatter.converser.addBotResponseToConversation(to_say, False)
            self.chatter.qualifyAndSendResponse(to_say, {}, False)
            # self.chatter.inputs_being_processed = self.chatter.inputs_being_processed - 1

        def process_input(self, rec_m):
            # N.B rec_m may contain other things in addition to the text of the user (e.g., the volume of voice)
            # so I first extract just the text to process
            user_input = (utils.splitStringToList(rec_m, Constants.STRING_SEPARATOR_INNER)[0]).strip()
            print(user_input)

            # I first do the processing of the input based on the current state:
            # Note, this step is expected not to transition between states
            # NOR affect the memory of the conversation
            state_output = self.current_state.process_input(user_input)
            # then I transition if necessary, and I update the memory
            if self.is_default:
                if not state_output is None:
                    print("something is wrong")
                else:
                    self.chatter.received_inputs[Constants.TOPIC_SPEECH].append(rec_m)
                    self.chatter.converser.addUserInput(user_input)
                    self.chatter.inputs_being_processed += 1

            elif self.is_name_retrieval: #when I'm in states that are not the default, I do not want to send stuff to the data collector (so I do not add to received_inputs), but I still would like to store the conversation
                self.chatter.converser.addUserInput(user_input) #note I only add to the user input history
                self.chatter.inputs_being_processed += 1

                if state_output is not None:  # the output is the name
                    self.temp_name = state_output
                    # print("---setting temp_name to", self.temp_name)
                    self.confirm_name()  # I transition to confirmation
                else:  # then no name detected
                    to_say = "I couldn't get your name. Could you repeat, please?"
                    # self.chatter.converser.addBotResponseToConversation(to_say, False)
                    self.chatter.qualifyAndSendResponse(to_say, {}, False)
                    self.first_retrieval = False
            elif self.is_name_confirmation:
                self.chatter.converser.addUserInput(user_input)
                self.chatter.inputs_being_processed += 1

                if state_output == "yes":
                    self.name = self.temp_name
                    self.end_name_retrieval_positive()
                elif state_output == "no":
                    self.temp_name = ""
                    self.repeat_name()  # i go back to name_retrieval
                else:
                    to_say = "Please, to avoid misunderstandings, can you confirm that your name is "+str(self.temp_name)+"?"
                    # self.chatter.converser.addBotResponseToConversation(to_say, False)
                    self.chatter.qualifyAndSendResponse(to_say, {}, False)
            else:
                print("WARNING!! I'm in some wrong state ", self.current_state)
                print("WARNING!! This should actually never happen...")

    class Converser:
        def __init__(self, model_name) -> None:
            super().__init__()
            self.model_name = model_name
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
            self.max_length_history = 3
            self.chat_history_ids = None
            # self.bot_input_ids = None
            # self.chat_history_ids_list = None
            self.input_ids = None
            self.user_inputs = []
            self.generated_responses = []
            self.first_indeces_steps = []
            self.initializeVariables()

        def initializeVariables(self):
            self.chat_history_ids = None
            # self.bot_input_ids = None
            # self.chat_history_ids_list = None
            self.input_ids = None
            self.user_inputs = []
            self.generated_responses = []
            self.first_indeces_steps = []

        def getResponse(self, text):
            # NOTE: IT IS ASSUMED THAT AT THIS POINT (I.E., WHEN THIS FUNCTION IS CALLED),
            # THE USER INPUT text IS ALREADY BOTH IN SELF.USER_INPUTS AND IN SELF.INPUT_IDS
            # SO THAT THE two CALLS JUST HERE BELOW CAN BE COMMENTED OUT.
            # self.user_inputs.append(text)
            # self.input_ids = self.tokenizer.encode(text + self.tokenizer.eos_token, return_tensors="pt")

            new_history_ids = self.model.generate(
                self.chat_history_ids,
                max_length=1000,
                do_sample=True,
                top_p=0.95,
                top_k=50,
                temperature=0.75,
                pad_token_id=self.tokenizer.eos_token_id
            )

            output = self.tokenizer.decode(new_history_ids[:, self.chat_history_ids.shape[-1]:][0],
                                           skip_special_tokens=True)

            return output

        def removeOldestInteractionFromChatHistory(self):
            index_step_to_remove = self.first_indeces_steps[0]
            self.chat_history_ids = self.chat_history_ids[:, index_step_to_remove:]

            self.first_indeces_steps = self.first_indeces_steps[1:]
            for i in range(len(self.first_indeces_steps)):
                self.first_indeces_steps[i] = self.first_indeces_steps[i]-index_step_to_remove


        def addBotResponse(self, response_text):
            tokenized_response = self.tokenizer.encode(response_text + self.tokenizer.eos_token,
                                                       return_tensors="pt")
            self.chat_history_ids = torch.cat([self.chat_history_ids, tokenized_response], dim=-1)
            self.generated_responses.append(response_text)
            self.first_indeces_steps.append(self.chat_history_ids.shape[-1])

            if (len(self.first_indeces_steps) % (self.max_length_history+1)) == 0:
                self.removeOldestInteractionFromChatHistory()


        def addUserInput(self, input_text, create_history=False):
            # print("----------adding user input ", input_text, " to the conversation")
            tokenized_input = self.tokenizer.encode(input_text + self.tokenizer.eos_token,
                                                    return_tensors="pt")
            if create_history or (self.chat_history_ids is None):
                self.chat_history_ids = tokenized_input
                self.input_ids = tokenized_input
                self.user_inputs.append(input_text)
            else: #otherwise the chat_history_ids should have already been updated, or what?
                #shouldn't I uncomment the next command??
                self.chat_history_ids = torch.cat([self.chat_history_ids, tokenized_input], dim=-1)
                self.input_ids = tokenized_input
                self.user_inputs.append(input_text)

        def addBotResponseToConversation(self, response, is_spontaneous):
            # print("I'm inside addBotResponseToConversation. Called for response ", response, " and spontaneity ", is_spontaneous)
            # print("The chat history is", self.chat_history_ids)
            if is_spontaneous:  # this means that this response does not come as a consequence of user input
                if self.chat_history_ids is None:
                    # in case it is the very first interaction, I create a fake user input (we do not want empty inputs)
                    # and then I append the bot spontaneous response
                    self.addUserInput("Hello!", create_history=True)
                    self.addBotResponse(response)
                else:
                    # otherwise, I assume that a user input is given and I want to replace the last bot response (if it exists) with the new spontaneous one
                    self.replaceLastBotResponseWith(response)
            else:  # the response comes as a consequene of user input, so I just need to add the bot response
                self.replaceLastBotResponseWith(response)

        def replaceLastBotResponseWith(self, new_response):
            last_gen_resp = ""
            if (len(self.generated_responses) > 0) and (len(self.generated_responses) >= len(self.user_inputs)):
                idx_first_token_last_bot_response = self.first_indeces_steps[-2] + self.input_ids.shape[-1] #the index of the beginning of the last step (step = interaction, -2 because -1 basically is just the length of the whole conversation) + the part contributed by the user
                self.chat_history_ids = self.chat_history_ids[:, 0:idx_first_token_last_bot_response] # cropped chat history
                last_gen_resp = self.generated_responses[-1] #store the last_gen_Resp
                self.generated_responses = self.generated_responses[:-1] #remove it from the list (I will add it later)
                self.first_indeces_steps = self.first_indeces_steps[:-1] #remove also the last indeces step, I will recompute it

            if not last_gen_resp == "":
                if not last_gen_resp.endswith(".") and not last_gen_resp.endswith("!") and not last_gen_resp.endswith("?"):
                    last_gen_resp += ". "
                else:
                    last_gen_resp += " "
            self.addBotResponse(last_gen_resp + new_response)

        def getConversation(self):
            """ Returns a list of pairs is_user, text"""
            conv = []
            for i in range(len(self.user_inputs)):
                conv.append((True, self.user_inputs[i]))
                if i < len(self.generated_responses):
                    conv.append((False, self.generated_responses[i]))
            return conv

        def printConversation(self):
            # print(self.chat_history_ids)
            for is_user, text in self.getConversation():
                if is_user:
                    print("user >> ", text)
                else:
                    print("bot >> ", text)

        def getConversationString(self, last_n_sentences = None):
            conv_str = ""
            conv = self.getConversation()
            conv_len = len(conv)
            first_sentence_id = 0
            if not last_n_sentences is None:
                first_sentence_id = max(0, conv_len-last_n_sentences)

            for i in range(first_sentence_id, conv_len):
                is_user, text = conv[i]
                conv_str += (" " if (
                        conv_str == "" or conv_str.endswith(".") or conv_str.endswith("!") or conv_str.endswith(
                    "?")) else ". ") + text
            return conv_str

    class SendMsgToBehaviour(OneShotBehaviour):
        """
        Sends all collected text to the data collector agent
        """

        def __init__(self, receiver, metadata):
            super().__init__()
            self.receiver = receiver
            self.metadata = metadata

        def getSentences(self, topic):
            sentence_dict_with_ordered_keys_from_oldest = {}
            nr_rec_in = len(self.agent.received_inputs[topic])
            for i in range(nr_rec_in):
                b = self.agent.received_inputs[topic].pop()  # extraction with removal
                sentence_dict_with_ordered_keys_from_oldest[i] = b
            return sentence_dict_with_ordered_keys_from_oldest

        async def run(self):
            # print("chatter running the sendmsgtobdibehavior")
            metadata = {Constants.SPADE_MSG_METADATA_KEYS_TYPE: "int"}
            if not self.metadata is None:
                if Constants.SPADE_MSG_BATCH_ID in self.metadata:
                    metadata[Constants.SPADE_MSG_BATCH_ID] = self.metadata[Constants.SPADE_MSG_BATCH_ID]
            # print(s_list)

            for topic in self.agent.received_inputs.keys():
                s_ordered_dict = self.getSentences(topic)
                if len(s_ordered_dict.keys()) > 0:
                    print("sending data as requested to the datacollector")
                    print(s_ordered_dict)
                    msg = utils.prepareMessage(self.agent.jid, self.receiver, Constants.PERFORMATIVE_INFORM, s_ordered_dict, topic, metadata)
                    await self.send(msg)
            # else:
            #     msg_body = Constants.NO_DATA
            #     # print(msg_body)
            #     msg = utils.prepareMessage(self.receiver, Constants.PERFORMATIVE_INFORM, msg_body)
            #     await self.send(msg)

    async def send_msg_to(self, receiver, metadata=None, content=None):
        # print("As a chatter, I received request from the data collector to send data")
        b = self.SendMsgToBehaviour(receiver, metadata)
        self.add_behaviour(b)

    async def do_work(self, work_info_dict):
        to_say = None
        is_spontaneous = None
        self.mqtt_publisher.publish(Constants.TOPIC_LEDS,
                                    utils.joinStrings([Constants.DIRECTIVE_LED_SET_COLOR, Constants.COLORS_BLUE]))
        print("work_info ", work_info_dict)
        # work_info_list = utils.splitStringToList(work_info)
        # print("work_info_list", work_info_list)
        if work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_REPLY_TO:
            # print("Ok BDI told me to reply to "+work_info_list[1])
            message = work_info_dict[Constants.SPADE_MSG_SAID].replace(Constants.ASL_STRING_SEPARATOR, " ")
            to_say = self.getTextFor(Chatter._TASK_CONTINUE_CONVERSATION, message, False)
            print("response to : ", message)
            print(to_say)
            is_spontaneous = False
            # self.converser.addBotResponseToConversation(to_say, False)
            # self.inputs_being_processed = self.inputs_being_processed - 1
        elif work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_SAY_SPONTANEOUS:
            print("---------- INPUTS BEING PROCESSED, IN WORK INFO SAY SPONTANEOUS ", self.inputs_being_processed)
            if self.inputs_being_processed == 0 and self.chatter_state_machine.is_default:
                to_say = work_info_dict[Constants.SPADE_MSG_TO_SAY]
                is_spontaneous = True
                # self.converser.addBotResponseToConversation(to_say, True)
        elif work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_SAY_IN_RESPONSE:
            to_say = work_info_dict[Constants.SPADE_MSG_TO_SAY]
            is_spontaneous = False
            # self.converser.addBotResponseToConversation(to_say, False)
            # self.inputs_being_processed = self.inputs_being_processed - 1
        elif work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_BEGIN_GREETING:

            if self.inputs_being_processed == 0 and self.chatter_state_machine.is_default:
                name = work_info_dict[Constants.SPADE_MSG_PERSON]
                if name == Constants.ASL_FLUENT_UNKNOWN_PERSON:
                    to_say = "Hello there! What's your name?"
                    self.chatter_state_machine.retrieve_name()
                else:
                    to_say = "Hello " + name + "! What's up?"
                is_spontaneous = True
                # self.converser.addBotResponseToConversation(to_say, True)

        elif work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_UPDATE_TOPIC_INTEREST:

            if self.inputs_being_processed == 0 and self.chatter_state_machine.is_default:
                print(work_info_dict)
                self.last_detected_interest = work_info_dict[Constants.SPADE_MSG_OBJECT].replace(Constants.ASL_STRING_SEPARATOR, " ")
                self.direction_last_detected_interest = work_info_dict[Constants.SPADE_MSG_DIRECTION].replace(Constants.ASL_STRING_SEPARATOR, " ")
                print(self.last_detected_interest)
                print(self.direction_last_detected_interest)
                try:
                    if self.direction_last_detected_interest == Constants.ASL_FLUENT_UNKNOWN_DIRECTION:
                        t2tinput = "You are looking at the " + str(self.last_detected_interest) + ". You know what is a " + str(
                            self.last_detected_interest) + "."
                    else:
                        t2tinput = "You are looking at the " + str(self.last_detected_interest) + " on your " + str(
                            self.direction_last_detected_interest) + ". You know what is a " + str(
                            self.last_detected_interest) + "."

                    question = self.getTextFor(Chatter._TASK_ASK_QUESTION, t2tinput, True)

                    print(question)
                    resp = question

                except:
                    print(traceback.format_exc())
                    resp = None
                to_say = str(resp)
                print("response: ", to_say)
                is_spontaneous = True
                # self.converser.addBotResponseToConversation(resp, True)
            # print(to_say)
        elif work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_TURN_CONVERSATION:

            if self.inputs_being_processed == 0 and self.chatter_state_machine.is_default:
                topic = work_info_dict[Constants.SPADE_MSG_OBJECT].replace(Constants.ASL_STRING_SEPARATOR, " ")
                resp = self.getTextFor(Chatter._TASK_CONVERSATION_TURN_SPONTANEOUS, topic, True)
                to_say = str(resp)
                is_spontaneous = True
                # self.converser.addBotResponseToConversation(to_say, True)  # here is_spontaneous should be given True

        if (not to_say is None) and (not is_spontaneous is None):
            self.qualifyAndSendResponse(to_say, work_info_dict, is_spontaneous)


    def qualifyAndSendResponse(self, to_say, work_info_dict, is_spontaneous_response):
        """ Function that qualifies the text to say based on the social info"""
        animation_to_perfom = None


        """ Determining the emotion associated to the text to say """
        emotion_label = None
        print("determined to say: ", to_say)

        print("I determine the emotion associated to the text.")
        emotion = self.temotion_classifier(to_say)[0][0]
        if emotion["score"] > 0.7:
            emotion_label = emotion["label"]
        print("emotion detected: ", emotion_label)
        animation_to_perfom = emotion_label

        """ Using the fuzzy system to determine the adequate levels of volume, etc., based on the social inputs """
        # social_qualifier_inputs = {}
        # if len(work_info_list) > 2 and (work_info_list[
        #                                     2] == "social_eval"):  # todo at some point we need to clean all this stuff with explicit indeces
        #     sublist = work_info_list[3:len(work_info_list)]
        #     print(sublist)
        #     nr_pairs = int(len(sublist) / 2)
        #     print(nr_pairs)
        #     for i in range(nr_pairs):
        #         key = sublist[i * 2]
        #         val = sublist[(i * 2) + 1]
        #         social_qualifier_inputs[key] = float(val)

        print("social qualifier inputs (trying to use the all work_info_dict, instead of the social_qualifier_inputs)")
        print(work_info_dict)

        volume = "70"
        if not self.fsq is None:
            social_qualification = None
            try:
                social_qualification = self.fsq[0].getSocialQualification(work_info_dict)  # here this is is only concerning the position but it should actually refer to all possible inputs that we are interested into, maybe the social itnerpreter should be some other worker independent, which will give back info about social intepretation
                print("volume_qualification")
                print(social_qualification)
            except Exception:
                print(
                    "Note: the exception exception is (in some cases) expected. I'm printing the traceback for now for the sake of clarity")
                print(traceback.format_exc())
            if (not social_qualification is None):
                volume = str(social_qualification[Constants.LV_VOLUME])


        """ Qualifying the behavior based on the role of the agent w.r.t. the person """
        if Constants.SPADE_MSG_NAO_ROLE in work_info_dict:
            if work_info_dict[Constants.SPADE_MSG_NAO_ROLE] == Constants.ASL_FLUENT_ROLE_SUBORDINATE:
                # changing what to say
                to_say = "Sir, " + to_say + " Sir!"
                # and also executing a certain animation
                # self.mqtt_publisher.publish(Constants.TOPIC_POSTURE,
                #                             utils.joinStrings([Constants.DIRECTIVE_PLAYANIMATION,
                #                                                Constants.ANIMATION_YES_SIR]))
                animation_to_perfom = Constants.ANIMATION_YES_SIR #I override the animation with a more specific one for the role

        """ Doing the actual work i.e., send directive to nao """
        if len(self.received_inputs[Constants.TOPIC_SPEECH]) == 0: #IN THIS CASE I SEE THERE ARE NO RECEIVED INPUT UNPROCESSED SO I ALSO CHANGE THE COLOR OF NAO'S CHEST
            self.mqtt_publisher.publish(Constants.TOPIC_LEDS,
                                        utils.joinStrings(
                                            [Constants.DIRECTIVE_LED_SET_COLOR, Constants.COLORS_WHITE]))

        if not animation_to_perfom is None:
            self.mqtt_publisher.publish(Constants.TOPIC_POSTURE,
                                        utils.joinStrings([Constants.DIRECTIVE_PLAYANIMATION, animation_to_perfom]))

        self.mqtt_publisher.publish(Constants.TOPIC_DIRECTIVE,
                                    utils.joinStrings([Constants.DIRECTIVE_SAY, to_say, "volume", volume]))
                                    # "say" + Constants.STRING_SEPARATOR + to_say + Constants.STRING_SEPARATOR + "volume" + Constants.STRING_SEPARATOR + volume)

        """ Finally, storing the info in the conversation """
        self.converser.addBotResponseToConversation(to_say, is_spontaneous_response)
        if not is_spontaneous_response:
            self.inputs_being_processed = self.inputs_being_processed - 1

        print("conversation is")
        self.converser.printConversation()


    def getQuestion(self, text, topic):
        resp = ""
        if topic == Chatter._QUESTION_TOPIC_TEXT:
            r = self.t2tgenerator("generate questions : " + text,
                                  max_length=18,
                                  do_sample=True,
                                  top_p=0.92,
                                  top_k=100,
                                  temperature=0.75)
            # print("questions for ", text, ": ")
            # for s in r:
            #     first = s['generated_text'].split("<sep>")[0]
            #     print(first)
            # print("")
            resp = r[0]['generated_text'].split("<sep>")[0]
        if topic == Chatter._QUESTION_TOPIC_SUMMARY:
            summary = self.summarizer(self.converser.getConversationString(last_n_sentences=5), min_length=5, max_length=40)[0][
                "summary_text"]
            # print(summary)
            resp = self.getQuestion("You can tell me more about " + summary, Chatter._QUESTION_TOPIC_TEXT)
        if topic == Chatter._QUESTION_TOPIC_NEWS:
            resp = "Anyways. " + self.getQuestion("You think about " + getRandomNewsFromBBC(), Chatter._QUESTION_TOPIC_TEXT)
        if topic == Chatter._QUESTION_TOPIC_WEATHER:
            resp = "Anyways. " + self.getQuestion("You think about " + getCurrentWeather(), Chatter._QUESTION_TOPIC_TEXT)
        if topic == Chatter._QUESTION_TOPIC_RANDOM:
            possible_topics = [Chatter._QUESTION_TOPIC_TEXT]*15 + \
                              [Chatter._QUESTION_TOPIC_SUMMARY]*3 + \
                              [Chatter._QUESTION_TOPIC_NEWS, Chatter._QUESTION_TOPIC_WEATHER] # by doing so I'm reducing (in a very rudimental way) the chances to ask about the news (so it doesn't happen often)
            resp = self.getQuestion(text, possible_topics[random.randint(0, len(possible_topics)-1)])
        return resp

    def isQuestion(self, text):
        try:
            is_Q = self.question_statement_classifier(text)[0]["label"] == "LABEL_1"
        except:
            is_Q = False
        return is_Q

    def getSpontaneousQuestion(self):
        resp = ""
        if len(self.converser.getConversation()) < 4:  # if less than 2 interactions
            resp = "Hey, I was reading the news. " + self.getQuestion("", Chatter._QUESTION_TOPIC_NEWS)
        else:
            resp = "By the way, I was thinking about our conversation earlier. " + self.getQuestion("", Chatter._QUESTION_TOPIC_SUMMARY)

        return resp

    def getTextFor(self, task, text, is_spontaneous=False):
        resp = ""
        # self.mqtt_publisher.publish(Constants.TOPIC_LEDS,
        #                             utils.joinStrings([Constants.DIRECTIVE_LED_SET_COLOR, Constants.COLORS_BLUE]))
        try:
            if task == Chatter._TASK_CONTINUE_CONVERSATION:
                """ The default case.
                Here I just want to use the conversation pipeline to generate a meaningful continuation.
                N.B. is_spontaneous is assumed False"""
                # user_input = self.conversation.past_user_inputs[len(self.conversation.past_user_inputs)-1]
                # print(self.conversation.past_user_inputs)
                # print(self.conversation.generated_responses)
                # print(self.conversation.new_user_input)
                # print("..--")
                # being slow to process everything, it might happen that multiple user inputs are given before previous answer is processed
                if not self.isQuestion(text):
                    if random.random()>0.7: #in 30% of cases I ask a question, so I don't always just reply
                        resp = self.getQuestion(text, Chatter._QUESTION_TOPIC_RANDOM)
                    else:
                        resp = self.converser.getResponse(text)
                else:
                    resp = self.converser.getResponse(text)
                if resp == "" or len(resp)<2:
                    resp = self.getSpontaneousQuestion()

            if task == Chatter._TASK_ASK_QUESTION:
                """ In this case, I want to generate a question for the user based on the text in argument text.
                I do so via the t2tgenerator. The answer will be the first one returned.
                In case the task is marked as is_spontaneous, I add the question to the conversation with an empty user input.
                Otherwise, the user input is already assumed to be the last one, and I simply add the answer."""
                resp = self.getQuestion(text, Chatter._QUESTION_TOPIC_TEXT)

            if task == Chatter._TASK_CONTINUE_CONVERSATION_SPONTANEOUS:
                """ In this case, I generate a question in a spontaneous way based on the summary of the conversation had so far."""
                resp = self.getSpontaneousQuestion()

            if task == Chatter._TASK_CONVERSATION_TURN_SPONTANEOUS:
                """ In this case, I generate a question in a spontaneous way based on a text generates starting from an input
                given in the argument text (e.g., this could be an object that has been observed, or some belief, or something else)"""
                g = self.tgenerator("a " + text, max_length=20,
                                    do_sample=True,
                                    top_p=0.92,
                                    top_k=100,
                                    temperature=0.75)
                print(g)
                resp = self.getQuestion("You know that " + g[0]["generated_text"] + ".", Chatter._QUESTION_TOPIC_TEXT)
        except:
            resp = ""

        if (resp == "") or len(resp)<2:
            self.converser.initializeVariables()
            resp = "Sorry, can you repeat, please?"
            # self.conversation.generated_responses[len(self.conversation.generated_responses) - 1] = resp

        return resp

    def on_message(self, client, userdata, message):
        rec_m = str(message.payload.decode("utf-8"))
        print("As a chatter I received data " + str(rec_m))

        if self.inputs_being_processed == 0 or not self.chatter_state_machine.is_default:
            # if self.gui_queue is None:
            self.mqtt_publisher.publish(Constants.TOPIC_LEDS,
                                        utils.joinStrings([Constants.DIRECTIVE_LED_SET_COLOR, Constants.COLORS_BLUE]))

            self.chatter_state_machine.process_input(rec_m)

        else:
            print(
                "Note: I ignore this data because there is already one input being processed.")
            print(self.inputs_being_processed)
            print(self.chatter_state_machine.is_default)

        # self.received_inputs.append(
        #     rec_m)  # N.B rec_m may contain other things in addition to the text of the user (e.g., the volume of voice=
        # user_input = utils.splitStringToList(rec_m, Constants.STRING_SEPARATOR_INNER)[0]
        # self.converser.addUserInput(user_input)
        # self.inputs_being_processed = self.inputs_being_processed + 1

    def kickstartLMs(self):
        print("Kickstarting Language Models so to speed up interaction with humans...")
        # kickstart_conversation_user_inputs = ["Hello!", "You are going to speak with a human, are you ready?", "Let's begin!"]
        kickstart_conversation_user_inputs = ["Hello!", "You are going to speak with a human, are you ready?", "Let's begin!"] # I do it with three sentences because in some cases the randomness will not initiate the dialogue model
        for s in kickstart_conversation_user_inputs:
            # kickstarting the converser
            self.converser.addUserInput(s)
            self.converser.addBotResponseToConversation(self.getTextFor(Chatter._TASK_CONTINUE_CONVERSATION, s, False), False)
            # kickstarting the t2tgenerator
            q = self.getQuestion(s, Chatter._QUESTION_TOPIC_TEXT)
            # kickstarting the summarizer
            summ = self.summarizer(self.converser.getConversationString(), min_length=5, max_length=20)[0][
                "summary_text"]
            # kickstarting the tgenerator
            g = self.tgenerator(s, max_length=20, do_sample=True, top_p=0.92, top_k=100, temperature=0.75)
            # kickstarting the temotion_classifier
            e = self.temotion_classifier(s)

    async def setup(self):
        logging.set_verbosity(40)  # errors

        # """ I create and train the actual chatter"""
        # self.chatbot = ChatBot('Chatter', logic_adapters=['chatterbot.logic.BestMatch',
        #                                                   'chatterbot.logic.MathematicalEvaluation'
        #                                                   # 'chatterbot.logic.TimeLogicAdapter'
        #                                                  ])
        # self.chatbot = ChatBot('Chatter', logic_adapters=[
        #     {
        #         'import_path': 'chatterbot.logic.BestMatch',
        #         "statement_comparison_function": "chatterbot.comparisons.levenshtein_distance"
        #     }
        # ])
        #
        # self.to_train = False
        # if self.to_train:
        #     print("Training chatter")
        #     self.trainer = ChatterBotCorpusTrainer(self.chatbot)
        #     self.trainer.train("chatterbot.corpus.english",
        #                        # "chatterbot.corpus.english.greetings",
        #                        # "chatterbot.corpus.english.conversations",
        #                        "data.chatter.custom")

        self.converser = self.Converser("microsoft/DialoGPT-medium")
        self.t2tgenerator = pipeline("text2text-generation", model="valhalla/t5-base-e2e-qg")
        self.summarizer = pipeline("summarization")
        self.tgenerator = pipeline('text-generation', model="facebook/opt-350m")
        self.temotion_classifier = pipeline("text-classification", model='bhadresh-savani/bert-base-uncased-emotion',
                                            top_k=1)
        self.question_statement_classifier = pipeline("text-classification", model='shahrukhx01/question-vs-statement-classifier')
        self.nlp = spacy.load("en_core_web_sm")

        self.chatter_state_machine = self.ChatterStateMachine(self)
        self.chatter_state_machine.setup(self.nlp)


        self.kickstartLMs()

        # giving a first input to initialize the models, it seems it is faster after
        # self.converser.addUserInput("Hello!")
        # self.converser.getResponse("Hello!")
        # init_sum = self.summarizer(self.converser.getConversationString(), min_length=5, max_length=20)[0][
        #     "summary_text"]
        # init_q = self.getQuestion("You can tell me more about " + init_sum)
        #
        # init_g = self.tgenerator(init_sum)

        # conversational_pipeline = pipeline("text2text-generation") #not working like this but could be interesting to try e.g., for sentiment analysis
        # self.conversation = Conversation()

        # ubuntu corpur traininng takes extremely long and it is currently practically not usable
        # self.trainer = UbuntuCorpusTrainer(self.chatbot)
        # self.trainer.train()

        self.received_inputs = {
            Constants.TOPIC_SPEECH: [],
            Constants.TOPIC_NAME_LEARNT: []
        }
        self.inputs_being_processed = 0
        self.last_detected_interest = ""

        """ This will listen to the sensors collecting data """
        self.mqtt_listener = MQTTClient(Constants.MQTT_BROKER_ADDRESS, "NAO_Chatter_Listener",
                                        Constants.MQTT_CLIENT_TYPE_LISTENER, Constants.TOPIC_SPEECH, self.on_message)

        """ This will publish what to say in response """
        self.mqtt_publisher = MQTTClient(Constants.MQTT_BROKER_ADDRESS, "NAO_Chatter_Publisher",
                                         Constants.MQTT_CLIENT_TYPE_PUBLISHER, None, None)

        await super().setup()
