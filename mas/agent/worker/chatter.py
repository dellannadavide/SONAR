import logging
import random
import threading
import time
import traceback
from abc import abstractmethod
from datetime import datetime, timedelta

import contractions
import nltk
import spacy
import torch
from spade.behaviour import OneShotBehaviour
from statemachine import StateMachine, State
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers import pipeline
from transformers.utils import logging as transformers_logging

import utils.constants as Constants
import utils.utils as utils
from mas.agent.workeragent import WorkerAgent
from mas.utils.news import getRandomNewsFromBBC
from mas.utils.weather import getCurrentWeather
from utils.mqttclient import MQTTClient

logger = logging.getLogger("nosar.mas.agent.worker.chatter")


class Chatter(WorkerAgent):
    """
    A class representing a chatter worker agent: an agent that deals with chatting with a human.
    """

    """ Constants used to identify tasks and types of questions """
    _TASK_CONTINUE_CONVERSATION = "continue_conversation"
    _TASK_CONTINUE_CONVERSATION_PROACTIVE = "continue_conversation_proactive"
    _TASK_ASK_QUESTION = "ask_question"
    _TASK_CONTINUE_CONVERSATION_SPONTANEOUS = "spontaneous_continuation_conversation"
    _TASK_CONVERSATION_TURN_SPONTANEOUS = "spontaneous_conversation_turn"
    _QUESTION_TOPIC_TEXT = "about_text"
    _QUESTION_TOPIC_SUMMARY = "summary_conversation"
    _QUESTION_TOPIC_NEWS = "news"
    _QUESTION_TOPIC_WEATHER = "weather"
    _QUESTION_TOPIC_RANDOM = "random"
    _QUESTION_TOPIC_EMOTIONS = "human_emotion"
    _QUESTION_TOPIC_SOCIAL_QUESTION = "social_question"

    class ChatterStateMachine(StateMachine):
        """ The chatter makes use of a state machine to enter non-default states.
        This helps minimizing inconsistencies and allows to implement social practices.
        A multi-state temporal social practice corresponds to a path in the state machine."""
        def __init__(self, chatter) -> None:
            super().__init__()
            self.chatter = chatter
            self.name = ""
            self.temp_name = ""
            self.first_retrieval = True

        def setup(self, nlp):
            self.name_retrieval.setNLP(nlp)
            self.name_confirmation.setNLP(nlp)
            self.goodbye_confirmation.setNLP(nlp)

        class ChatterState(State):
            @abstractmethod
            def process_input(self, user_input: str):
                pass

        class DefaultChatterState(ChatterState):
            """ The default chatter state is the one where a normal reply is given.
            This happens by passing directly the user input to the data collector and then to the bdi agent.
            so here there is nothing. """
            def process_input(self, user_input):
                return None

        class NameRetrievalState(ChatterState):
            """ State entered when the name of a person needs to be retrieved. """
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
            """ After retrieving the name the agent asks for and checks confirmation that the correct name is learnt. """
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

        class GiveFollowUpAnswerState(ChatterState):
            """ A state entered when the chatter is instructed by the bdi agent to ask a question and then give a
            follow-up answer/sentence after the user replied.
            E.g.,
            agent: by the way do you know what's the temperature outside?
            [after saying this, enters GiveFollowUpAnswerState]
            user: no I don't
            agent: it's 4 degrees
            [the follow-up answer]
            """
            def __init__(self, name, value=None, initial=False):
                super().__init__(name, value, initial)
                self.follow_up_answer = ""

            def set_follow_up_answer(self, answer):
                self.follow_up_answer = answer

            def process_input(self, user_input):
                return self.follow_up_answer

        class GoodbyeConfirmationState(ChatterState):
            """ A state entered to confirm that the person is leaving before completing the goodbye social practice """
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

        class SleepingState(ChatterState):
            """ In this state the agent is asleep and all user inputs are ignored unless the sentence is 'wake up'"""
            def __init__(self, name, value=None, initial=False, nlp=None):
                super().__init__(name, value, initial)

            def process_input(self, user_input):
                logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "going ahead only if the sentence is 'wake up'")
                return user_input.lower() == "wake up"

        # States
        default = DefaultChatterState('Default', initial=True)
        name_retrieval = NameRetrievalState('Retrieving Person Name')
        name_confirmation = NameConfirmationState('Confirming Person Name')
        giving_follow_up_answer = GiveFollowUpAnswerState('Give a Follow Up Answer')
        goodbye_confirmation = GoodbyeConfirmationState("Ending Conversation")
        sleeping = SleepingState("Sleeping State")

        end_name_retrieval_negative = name_retrieval.to(default)

        def possibly_end_retrieval(self):
            """ Function called to check if the name retrieval practice should be terminated """
            if self.is_name_retrieval and self.first_retrieval:
                to_say = "Nevermind."
                # self.chatter.converser.addBotResponseToConversation(to_say, True)
                self.chatter.qualifyAndSendResponse(to_say, {}, True)
                self.chatter.setOneInputProcessed()
                self.end_name_retrieval_negative()

        # State Transitions, and associated events
        retrieve_name = default.to(name_retrieval)

        def on_retrieve_name(self):
            delay = 60
            start_time = threading.Timer(delay, self.possibly_end_retrieval)
            start_time.start()

        confirm_name = name_retrieval.to(name_confirmation)

        def on_confirm_name(self):
            to_say = "Your name is " + str(self.temp_name) + ", correct?"
            # self.chatter.converser.addBotResponseToConversation(to_say, False)
            self.chatter.qualifyAndSendResponse(to_say, {}, False)

        repeat_name = name_confirmation.to(name_retrieval)

        def on_repeat_name(self):
            to_say = "Alright, can you repeat your name then?"
            # self.chatter.converser.addBotResponseToConversation(to_say, False)
            self.chatter.qualifyAndSendResponse(to_say, {}, False)

        end_name_retrieval_positive = name_confirmation.to(default)

        start_follow_up_answer = default.to(giving_follow_up_answer)
        end_follow_up_answer = giving_follow_up_answer.to(default)

        begin_goodbye = default.to(goodbye_confirmation)
        exit_goodbye_negative = goodbye_confirmation.to(default)
        go_to_sleep = goodbye_confirmation.to(sleeping)
        wake_up = sleeping.to(default)

        def on_go_to_sleep(self):
            self.chatter.received_inputs[Constants.TOPIC_INTERNAL_COMMUNICATIONS].append(Constants.DIRECTIVE_SLEEP)

        def on_wake_up(self):
            self.chatter.received_inputs[Constants.TOPIC_INTERNAL_COMMUNICATIONS].append(Constants.DIRECTIVE_WAKE_UP)
            to_say = "Ahh! what a nap!"
            # self.chatter.converser.addBotResponseToConversation(to_say, False)
            self.chatter.qualifyAndSendResponse(to_say, {}, False)

        def on_end_name_retrieval_positive(self):
            to_say = "Got it! Nice to meet you " + str(self.name) + "."
            to_say = to_say+" "+random.choice(Constants.GREETING_QUESTIONS)
            self.chatter.received_inputs[Constants.TOPIC_NAME_LEARNT].append(str(self.name))
            self.chatter.qualifyAndSendResponse(to_say, {}, False)

        def process_input(self, rec_m):
            """ This function is called for every input received by the user.
            Based on the current state of the state machine, it determines the correct consequence
            """
            # N.B rec_m may contain other things in addition to the text of the user (e.g., the volume of voice)
            # so I first extract just the text to process
            user_input = (utils.splitStringToList(rec_m, Constants.STRING_SEPARATOR_INNER)[0]).strip()
            logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "Processing input " + user_input)

            # I first do the processing of the input based on the current state:
            # Note, this step is expected not to transition between states
            # NOR affect the memory of the conversation
            state_output = self.current_state.process_input(user_input)
            # then I transition if necessary, and I update the memory
            if self.is_default:
                if not state_output is None:
                    logger.error(
                        "Something is wrong. state_output is not None after processing input from default state")
                else:
                    self.chatter.received_inputs[Constants.TOPIC_SPEECH].append(rec_m) # append the received input to the chatter dict that will be comunicate to the data collector
                    self.chatter.converser.addUserInput(user_input) # add the user input to the converser, which keeps track of the conversation
                    self.chatter.addOneInputBeingProcessed() # set one input as being processed

            elif self.is_name_retrieval:
                # when I'm in states that are not the default,
                # I do not want to send stuff to the data collector (so I do not add to received_inputs),
                # but I still would like to store the conversation
                self.chatter.converser.addUserInput(user_input)  # note I only add to the user input history
                self.chatter.addOneInputBeingProcessed()

                if state_output is not None:  # the output is the name
                    self.temp_name = state_output
                    self.confirm_name()  # I transition to confirmation
                else:  # then no name detected
                    to_say = "I couldn't get your name. Could you repeat, please?"
                    self.chatter.qualifyAndSendResponse(to_say, {}, False)
                    self.first_retrieval = False
            elif self.is_name_confirmation:
                self.chatter.converser.addUserInput(user_input)
                self.chatter.addOneInputBeingProcessed()

                if state_output == "yes":
                    self.name = self.temp_name
                    self.end_name_retrieval_positive()
                elif state_output == "no":
                    self.temp_name = ""
                    self.repeat_name()  # i go back to name_retrieval
                else:
                    to_say = "Please, to avoid misunderstandings, can you confirm that your name is " + str(
                        self.temp_name) + "?"
                    # self.chatter.converser.addBotResponseToConversation(to_say, False)
                    self.chatter.qualifyAndSendResponse(to_say, {}, False)
            elif self.is_giving_follow_up_answer:
                self.chatter.converser.addUserInput(user_input)
                self.chatter.addOneInputBeingProcessed()

                self.end_follow_up_answer()
                self.chatter.qualifyAndSendResponse(state_output, {}, False)
            elif self.is_goodbye_confirmation:
                self.chatter.converser.addUserInput(user_input)
                self.chatter.addOneInputBeingProcessed()

                if state_output == "yes":
                    self.go_to_sleep()
                elif state_output == "no":
                    to_say = "Oh, I must have misunderstood, sorry! We can stay together for a little longer! Yay!"
                    # self.chatter.converser.addBotResponseToConversation(to_say, False)
                    self.chatter.qualifyAndSendResponse(to_say, {}, False)
                    self.exit_goodbye_negative()
                else:
                    to_say = "I'm not sure I understood, are you actually leaving?"
                    # self.chatter.converser.addBotResponseToConversation(to_say, False)
                    self.chatter.qualifyAndSendResponse(to_say, {}, False)
            elif self.is_sleeping:
                if state_output == True: #wake up
                    self.chatter.converser.addUserInput(user_input)
                    self.chatter.addOneInputBeingProcessed()
                    self.wake_up()
                else:
                    self.chatter.setOneInputProcessed()

            else:
                logger.error("I'm in some wrong state {}".format(self.current_state))
                logger.error("This should actually never happen...")

    class Converser:
        """ The Converser is a class used to keep track of the conversation so far so to be able to
        have some context in the responses provided to the user. """
        def __init__(self, model_name) -> None:
            super().__init__()
            self.model_name = model_name
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
            self.max_length_history = 4
            self.chat_history_ids = None
            self.input_ids = None
            self.user_inputs = []
            self.generated_responses = []
            self.first_indeces_steps = []
            self.initializeVariables()

        def initializeVariables(self):
            self.chat_history_ids = None
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
                self.first_indeces_steps[i] = self.first_indeces_steps[i] - index_step_to_remove

        def addBotResponse(self, response_text):
            tokenized_response = self.tokenizer.encode(response_text + self.tokenizer.eos_token,
                                                       return_tensors="pt")
            if self.chat_history_ids is None:
                tokeinzed_new_input = self.tokenizer.encode("New beginning" + self.tokenizer.eos_token,
                                                    return_tensors="pt")
                self.chat_history_ids = tokeinzed_new_input
                self.input_ids = tokeinzed_new_input
                self.user_inputs.append(tokeinzed_new_input)

            self.chat_history_ids = torch.cat([self.chat_history_ids, tokenized_response], dim=-1)
            self.generated_responses.append(response_text)
            self.first_indeces_steps.append(self.chat_history_ids.shape[-1])

            if (len(self.first_indeces_steps) % (self.max_length_history + 1)) == 0:
                self.removeOldestInteractionFromChatHistory()

        def addUserInput(self, input_text, create_history=False):
            # print("----------adding user input ", input_text, " to the conversation")
            tokenized_input = self.tokenizer.encode(input_text + self.tokenizer.eos_token,
                                                    return_tensors="pt")
            if create_history or (self.chat_history_ids is None):
                self.chat_history_ids = tokenized_input
                self.input_ids = tokenized_input
                self.user_inputs.append(input_text)
            else:  # otherwise the chat_history_ids should have already been updated, or what?
                # shouldn't I uncomment the next command??
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
                idx_first_token_last_bot_response = self.first_indeces_steps[-2] + self.input_ids.shape[
                    -1]  # the index of the beginning of the last step (step = interaction, -2 because -1 basically is just the length of the whole conversation) + the part contributed by the user
                self.chat_history_ids = self.chat_history_ids[:,
                                        0:idx_first_token_last_bot_response]  # cropped chat history
                last_gen_resp = self.generated_responses[-1]  # store the last_gen_Resp
                self.generated_responses = self.generated_responses[
                                           :-1]  # remove it from the list (I will add it later)
                self.first_indeces_steps = self.first_indeces_steps[
                                           :-1]  # remove also the last indeces step, I will recompute it

            if not last_gen_resp == "":
                if not last_gen_resp.endswith(".") and not last_gen_resp.endswith("!") and not last_gen_resp.endswith(
                        "?"):
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
                    logger.info("user >> {}".format(text))
                else:
                    logger.info("bot >> {}".format(text))


        def getITHToLastUserReponse(self, i):
            if i>0:
                if len(self.user_inputs)>i-1:
                    return self.user_inputs[-i]
                else:
                    return None
            return None

        def getITHToLastBotReponse(self, i):
            if i > 0:
                if len(self.generated_responses) > i - 1:
                    return self.generated_responses[-i]
                else:
                    return None
            return None


        def getConversationString(self, last_n_sentences=None):
            conv_str = ""
            conv = self.getConversation()
            conv_len = len(conv)
            first_sentence_id = 0
            if not last_n_sentences is None:
                first_sentence_id = max(0, conv_len - last_n_sentences)

            for i in range(first_sentence_id, conv_len):
                is_user, text = conv[i]
                conv_str += (" " if (
                        conv_str == "" or conv_str.endswith(".") or conv_str.endswith("!") or conv_str.endswith(
                    "?")) else ". ") + text
            return conv_str

    class SendMsgToBehaviour(OneShotBehaviour):
        """
        Sends all collected info (stored in the agent's received_inputs dict) to the data collector agent
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
            metadata = {Constants.SPADE_MSG_METADATA_KEYS_TYPE: "int"}
            if not self.metadata is None:
                if Constants.SPADE_MSG_BATCH_ID in self.metadata:
                    metadata[Constants.SPADE_MSG_BATCH_ID] = self.metadata[Constants.SPADE_MSG_BATCH_ID]

            for topic in self.agent.received_inputs.keys():
                s_ordered_dict = self.getSentences(topic)
                if len(s_ordered_dict.keys()) > 0:
                    logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "sending data as requested to the datacollector")
                    logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, s_ordered_dict)
                    msg = utils.prepareMessage(self.agent.jid, self.receiver, Constants.PERFORMATIVE_INFORM,
                                               s_ordered_dict, topic, metadata)
                    await self.send(msg)


    def __init__(self, jid: str, password: str, verify_security: bool = False, fsi=None, fsq=None, gui_queue=None):
        """ Init of the chatter agent"""
        super().__init__(jid, password, verify_security, fsi, fsq, gui_queue)
        self.asked_about_emotions = None
        self.to_add_to_next_sentence = None

    async def send_msg_to(self, receiver, metadata=None, content=None):
        # print("As a chatter, I received request from the data collector to send data")
        b = self.SendMsgToBehaviour(receiver, metadata)
        self.add_behaviour(b)

    async def do_work(self, work_info_dict):
        """ Function automatically invoked when the agent receives a message with performative INFORM.
        This type of message is typically received by the BDI agent which informs the chatter to say or do something
        e.g., to process the user input without reply, to reply in a proactive way, to say something spontaneous, etc."""
        to_say = None
        is_spontaneous = None

        logger.info("work_info {}".format(work_info_dict))

        if work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_SET_USER_INPUT_PROCESSED_WITH_NO_REPLY:
            logger.log(Constants.LOGGING_LV_DEBUG_NOSAR,
                       "CHATTER: setting input processed with no reply (adding a fake 'ok' bot response to conversation)")
            self.converser.addBotResponseToConversation("ok", False)
            self.setOneInputProcessed()

        if work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_REPLY_TO_REACTIVE:
            message = work_info_dict[Constants.SPADE_MSG_SAID].replace(Constants.ASL_STRING_SEPARATOR, " ")
            to_say = self.getTextFor(Chatter._TASK_CONTINUE_CONVERSATION, message, False)
            logger.info("response to : {}".format(message))
            logger.info(to_say)
            is_spontaneous = False

        if work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_REPLY_PARROT:
            message = work_info_dict[Constants.SPADE_MSG_SAID].replace(Constants.ASL_STRING_SEPARATOR, " ")
            to_say = message
            logger.info("response to : {}".format(message))
            logger.info(to_say)
            is_spontaneous = False

        if work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_REPLY_TO_PROACTIVE:
            message = work_info_dict[Constants.SPADE_MSG_SAID].replace(Constants.ASL_STRING_SEPARATOR, " ")
            emotion = None
            if Constants.SPADE_MSG_HUMAN_EMOTION in work_info_dict and \
                    (not work_info_dict[Constants.SPADE_MSG_HUMAN_EMOTION] == Constants.ASL_FLUENT_EMOTION_NEUTRAL):
                emotion = work_info_dict[Constants.SPADE_MSG_HUMAN_EMOTION]
            to_say = self.getTextFor(Chatter._TASK_CONTINUE_CONVERSATION_PROACTIVE, message, human_emotion=emotion,
                                     is_spontaneous=False)
            logger.info("response to : {}".format(message))
            logger.info(to_say)
            is_spontaneous = False

        elif work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_SAY_SPONTANEOUS:
            logger.log(Constants.LOGGING_LV_DEBUG_NOSAR,
                       "---------- INPUTS BEING PROCESSED, IN WORK INFO SAY SPONTANEOUS {}".format(
                           self.inputs_being_processed))
            if self.noInputBeingProcessed() and self.chatter_state_machine.is_default:
                to_say = work_info_dict[Constants.SPADE_MSG_TO_SAY]
                is_spontaneous = True

        elif work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_SAY_WHAT_USER_SAID:
            to_say = "You said: "+ self.converser.getITHToLastUserReponse(2)
            is_spontaneous = False

        elif work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_SAY_WHAT_BOT_SAID:
            last_response = str(self.converser.getITHToLastBotReponse(1)).split(".")[-1]
            last_response = last_response.split("?")[-1]
            to_say = "I said: "+ str(last_response)
            is_spontaneous = False

        elif work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_SAY_IN_RESPONSE:
            to_say = work_info_dict[Constants.SPADE_MSG_TO_SAY]
            is_spontaneous = False

        elif work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_BEGIN_GREETING:
            if self.noInputBeingProcessed() and self.chatter_state_machine.is_default:
                name = work_info_dict[Constants.SPADE_MSG_PERSON]
                if name == Constants.ASL_FLUENT_UNKNOWN_PERSON:
                    to_say = "Hello there! What's your name?"
                    self.chatter_state_machine.retrieve_name()
                else:
                    to_say = "Hello " + name + "! What's up?"
                is_spontaneous = True
                # self.converser.addBotResponseToConversation(to_say, True)

        elif work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_BEGIN_GOODBYE:
            to_say = work_info_dict[Constants.SPADE_MSG_TO_SAY]
            self.chatter_state_machine.begin_goodbye()
            is_spontaneous = False

        elif work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_UPDATE_TOPIC_INTEREST:

            if self.noInputBeingProcessed() and self.chatter_state_machine.is_default:
                logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, work_info_dict)
                self.last_detected_interest = work_info_dict[Constants.SPADE_MSG_OBJECT].replace(
                    Constants.ASL_STRING_SEPARATOR, " ")
                self.direction_last_detected_interest = work_info_dict[Constants.SPADE_MSG_DIRECTION].replace(
                    Constants.ASL_STRING_SEPARATOR, " ")
                logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, self.last_detected_interest)
                logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, self.direction_last_detected_interest)
                try:
                    if self.direction_last_detected_interest == Constants.ASL_FLUENT_UNKNOWN_DIRECTION:
                        t2tinput = "You are looking at the " + str(
                            self.last_detected_interest) + " and you know what is a " + str(
                            self.last_detected_interest) + "."
                    else:
                        t2tinput = "You are looking at the " + str(self.last_detected_interest) + " on your " + str(
                            self.direction_last_detected_interest) + " and you know what is a " + str(
                            self.last_detected_interest) + "."

                    question = self.getTextFor(Chatter._TASK_ASK_QUESTION, t2tinput, True)

                    logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, question)
                    resp = question

                except:
                    logger.error(traceback.format_exc())
                    resp = None
                to_say = str(resp)
                logger.info("response: {}".format(to_say))
                is_spontaneous = True
                # self.converser.addBotResponseToConversation(resp, True)
            # print(to_say)
        elif work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_TURN_CONVERSATION:
            if self.noInputBeingProcessed() and self.chatter_state_machine.is_default:
                topic = work_info_dict[Constants.SPADE_MSG_OBJECT].replace(Constants.ASL_STRING_SEPARATOR, " ").replace("_", " ")
                logger.info(
                    "I trigger a spontaneous conversation about the perceived object {}".format(topic))
                resp = self.getTextFor(Chatter._TASK_CONVERSATION_TURN_SPONTANEOUS, topic, True)
                to_say = str(resp)
                is_spontaneous = True
                # self.converser.addBotResponseToConversation(to_say, True)  # here is_spontaneous should be given True
        elif work_info_dict[Constants.SPADE_MSG_DIRECTIVE] == Constants.DIRECTIVE_CONTINUE_CONVERSATION:
            if self.noInputBeingProcessed() and self.chatter_state_machine.is_default:
                # topic = work_info_dict[Constants.SPADE_MSG_OBJECT].replace(Constants.ASL_STRING_SEPARATOR, " ")
                logger.info(
                    "I trigger a spontaneous continuation of the conversation because nothing was said for some time")
                resp = self.getTextFor(Chatter._TASK_CONTINUE_CONVERSATION_SPONTANEOUS, "", True)
                to_say = str(resp)
                is_spontaneous = True
                # self.converser.addBotResponseToConversation(to_say, True)  # here is_spontaneous should be given True



        if (not to_say is None) and (not is_spontaneous is None):
            if is_spontaneous:
                if self.areInputsBeingProcessed():
                    """
                    In this (special) case, the person has said something while the robot was preparing a spontaneous sentence.
                    In order to avoid confusing texts, what I do is to store the spontaneous text (to_say) in a variable,
                    and I will append such text to the next response to the person's sentence as soon as it is ready.
                    """
                    self.to_add_to_next_sentence = to_say
                else:
                    """ Otherwise, all good, normal case qualifyandsend.
                    Note:
                    it could still be that the person says something in this small timegap but
                    if I do this test here, I do not need to do twice the social qualification via fuzzy inference, and also
                    I can compute one single emotion and movement for the entire sentence)"""
                    self.qualifyAndSendResponse(to_say, work_info_dict, is_spontaneous)
                    self.to_add_to_next_sentence = None
            else:
                """ It is not spontaneous, so it's the reply.
                I check if there is something to add to the end of the sentence and if so I do it"""
                if not self.to_add_to_next_sentence is None:
                    to_say = to_say + " " + self.to_add_to_next_sentence
                    self.to_add_to_next_sentence = None
            
                self.qualifyAndSendResponse(to_say, work_info_dict, is_spontaneous)

    def qualifyAndSendResponse(self, to_say, work_info_dict, is_spontaneous_response):
        """ This function represents the social qualification of the chatter agent.
        It does the following steps:
        1. it determines the emotion associated to the sentence it is going to say.
        The emotion is transformed in a label that will be used to determine an appropriate animation to do while saying the words
        2. it runs fuzzy inference to determine appropriate levels of volume, speed and tone of voice
        based on the current social interpretation of the situation (this info is stored in the work_info_dict, sent by the BDI agent).
        3. if the agent has a particular role, then rules are applied to also qualify the sentence based on the role
        (e.g., for the subordinate role, the agent will not use contractions, and will add "sir" to the sentence)
        4. finally send via mqtt all directives for the robot's actuators
        """

        logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "IN QUALIFY: {}".format(work_info_dict))
        """ Function that qualifies the text to say based on the social info"""
        animation_to_perfom = None
        emotion_label = None

        volume = "90"
        speed = "90"
        tone = "100"
        if not self.fsq is None: #THIS TESTS IF THE CHATTER HAS SOCIAL AND NORM-AWARENESS CAPABILITIES ENABLED
            """ Determining the emotion associated to the text to say """

            logger.info("determined to say: {}".format(to_say))

            logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "I determine the emotion associated to the text.")
            emotion = self.temotion_classifier(to_say)[0][0]
            if emotion["score"] > 0.7:
                emotion_label = emotion["label"]
            logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "emotion detected: {}".format(emotion_label))
            animation_to_perfom = emotion_label

            """ Using the fuzzy system to determine the adequate levels of volume, etc., based on the social inputs """

            social_qualification = None
            try:
                if (Constants.SPADE_MSG_NAO_ROLE in work_info_dict) and (work_info_dict[Constants.SPADE_MSG_NAO_ROLE] == Constants.ASL_FLUENT_ROLE_SUBORDINATE):
                    work_info_dict[Constants.LV_ROLE_SUBORDINATE] = 1.0

                social_qualification = self.fsq[0].getSocialQualification(
                    work_info_dict)  # here this is is only concerning the position but it should actually refer to all possible inputs that we are interested into, maybe the social itnerpreter should be some other worker independent, which will give back info about social intepretation
                logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "SOCIAL_qualification")
                logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, social_qualification)
            except Exception:
                logger.warning(
                    "Note: the exception is (in some cases) expected. I'm printing the traceback for now for the sake of clarity")
                logger.warning(traceback.format_exc())
            if (not social_qualification is None):
                volume = str(social_qualification[Constants.LV_VOLUME])
                speed = str(social_qualification[Constants.LV_SPEED_VOICE])
                tone = str(social_qualification[Constants.LV_TONE_VOICE])

            """ Qualifying the behavior based on the role of the agent w.r.t. the person """
            if Constants.SPADE_MSG_NAO_ROLE in work_info_dict:
                if work_info_dict[Constants.SPADE_MSG_NAO_ROLE] == Constants.ASL_FLUENT_ROLE_SUBORDINATE:
                    # changing what to say
                    to_say = contractions.fix(to_say)
                    if not "sir" in to_say.lower():
                        to_say = random.choice(["Sir, ", ""]) + to_say + random.choice([" Sir!", "!"])
                    # and also executing a certain animation
                    # self.mqtt_publisher.publish(Constants.TOPIC_POSTURE,
                    #                             utils.joinStrings([Constants.DIRECTIVE_PLAYANIMATION,
                    #                                                Constants.ANIMATION_YES_SIR]))
                    animation_to_perfom = Constants.ANIMATION_YES_SIR  # I override the animation with a more specific one for the role

        """ Doing the actual work i.e., send directive to nao """
        if not animation_to_perfom is None:
            self.mqtt_publisher.publish(Constants.TOPIC_POSTURE,
                                        utils.joinStrings([Constants.DIRECTIVE_PLAYANIMATION, animation_to_perfom]))

        message_to_say_list = [Constants.DIRECTIVE_SAY, to_say, "volume", volume, "speed", speed, "tone", tone]
        if not emotion_label is None:
            message_to_say_list.extend(["emotion", str(emotion_label)])


        self.mqtt_publisher.publish(Constants.TOPIC_DIRECTIVE_TTS, utils.joinStrings(message_to_say_list))

        """ Storing the info in the conversation """
        self.converser.addBotResponseToConversation(to_say, is_spontaneous_response)
        if not is_spontaneous_response:
            self.setOneInputProcessed()
        logger.info("conversation is")
        self.converser.printConversation()



    def setOneInputProcessed(self):
        """ used to avoid processing more than one user sentence at a time"""
        self.inputs_being_processed = max(self.inputs_being_processed - 1,
                                          0)  # making sure I don't go below 0 in any case

        """ If nothing is being processed (concerning the text, I reset the led color to default) """
        if self.noInputBeingProcessed():  # IN THIS CASE I SEE THERE ARE NO RECEIVED INPUT UNPROCESSED SO I ALSO CHANGE THE COLOR OF NAO'S CHEST
            self.mqtt_publisher.publish(Constants.TOPIC_LEDS,
                                        utils.joinStrings(
                                            [Constants.DIRECTIVE_LED_SET_THINKING, "False"]))

    def addOneInputBeingProcessed(self):
        self.inputs_being_processed += 1

    def areInputsBeingProcessed(self):
        return self.inputs_being_processed > 0

    def noInputBeingProcessed(self):
        return self.inputs_being_processed == 0

    def getQuestion(self, text, topic):
        """
        Returns a question on a particular topic starting from text when needed
        :param text:
        :param topic:
        :return:
        """
        logger.log(Constants.LOGGING_LV_DEBUG_NOSAR,
                   "in getQuestions {}, {}".format(text, topic))
        resp = ""
        if topic == Chatter._QUESTION_TOPIC_TEXT:
            r = self.t2tgenerator("generate questions : " + text,
                                  max_length=18,
                                  do_sample=True,
                                  top_p=0.92,
                                  top_k=100,
                                  temperature=0.75)
            resp = r[0]['generated_text'].split("<sep>")[0]
        if topic == Chatter._QUESTION_TOPIC_SOCIAL_QUESTION:
            resp = random.choice(Constants.SOCIAL_QUESTIONS_EXAMPLES)
        if topic == Chatter._QUESTION_TOPIC_SUMMARY:
            summary = \
            self.summarizer(self.converser.getConversationString(last_n_sentences=5), min_length=5, max_length=40)[0][
                "summary_text"]
            resp = self.getQuestion("You can tell me more about " + summary, Chatter._QUESTION_TOPIC_TEXT)
        if topic == Chatter._QUESTION_TOPIC_NEWS:

            one_news_title, one_news_description = getRandomNewsFromBBC()
            news = one_news_title+". "+one_news_description
            resp = random.choice(Constants.VOCABULARY_ANYWAYS)+". " + random.choice(["I was checking the news. ",
                                                                                     "I can't stop reading the news. ",
                                                                                     "I'm obsessed with the news today. ",
                                                                                     "Reading the news right now. ",
                                                                                     "I was again checking the news. "]) + self.getQuestion(news,
                                                  Chatter._QUESTION_TOPIC_TEXT)

            if self.chatter_state_machine.is_default:
                self.chatter_state_machine.start_follow_up_answer()
                self.chatter_state_machine.giving_follow_up_answer.set_follow_up_answer("It's "+self.question_answerer(question=resp, context=news)["answer"])

        if topic == Chatter._QUESTION_TOPIC_WEATHER:
            weather = getCurrentWeather()

            possible_questions_types = ["You think about ", "You like ", "You are enjoying "]
            q_type = random.choice(possible_questions_types)
            resp = random.choice(Constants.VOCABULARY_ANYWAYS)+". " + self.getQuestion(q_type + weather,
                                                  Chatter._QUESTION_TOPIC_TEXT)

            if self.chatter_state_machine.is_default:
                self.chatter_state_machine.start_follow_up_answer()
                self.chatter_state_machine.giving_follow_up_answer.set_follow_up_answer(self.question_answerer(question=resp, context=weather)["answer"])

        if topic == Chatter._QUESTION_TOPIC_EMOTIONS:
            g = self.tgenerator("Today you look " + text + ". Is it because", max_length=50,
                                do_sample=True,
                                top_p=0.92,
                                top_k=100,
                                temperature=0.75)

            resp = g[0]['generated_text'].split("?")[0] + "?"

        if topic == Chatter._QUESTION_TOPIC_RANDOM:
            n = random.random()
            logger.info("In chatter question about random topic, n is {}".format(n))
            if n < 0.7: #in x% of cases I ask a questions about the last text
                selected_topic = Chatter._QUESTION_TOPIC_TEXT
                # in this case I also convert the person sentence from first to second person,
                # so that the question is more meaningful
                text_for_question_list = []
                for word in nltk.wordpunct_tokenize(text):
                    if word.lower() in Constants.I_YOU_MAPPING.keys():
                        text_for_question_list.append(Constants.I_YOU_MAPPING[word.lower()])
                    else:
                        text_for_question_list.append(word)
                text = " ".join(text_for_question_list)
                logger.log(Constants.LOGGING_LV_DEBUG_NOSAR,
                           "generating questions for converted text {}".format(text))

            elif n < 0.8: #in 10%, I as a question about the conversation so far
                selected_topic = Chatter._QUESTION_TOPIC_SUMMARY
            elif n < 0.9: # in 10%, I ask a random social question
                selected_topic = Chatter._QUESTION_TOPIC_SOCIAL_QUESTION
            elif n < 0.975: # in 7.5% I ask a question about the news
                selected_topic = Chatter._QUESTION_TOPIC_NEWS
            else: #  in 2.5% I ask a question about the weather
                selected_topic = Chatter._QUESTION_TOPIC_WEATHER

            logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "Selected topic is "+str(selected_topic))
            resp = self.getQuestion(text, selected_topic)
        return resp

    def isQuestion(self, text):
        try:
            is_Q = self.question_statement_classifier(text)[0]["label"] == "LABEL_1"
        except:
            is_Q = False
        return is_Q

    def getSpontaneousQuestion(self, text):
        resp = ""
        if text =="":
            if len(self.converser.getConversation()) > 1: #at least one user input
                text = self.converser.user_inputs[-1]
                resp = self.getQuestion(text, Chatter._QUESTION_TOPIC_RANDOM)
            else:
                resp = self.getQuestion("", Chatter._QUESTION_TOPIC_NEWS)
        else:
            resp = self.getQuestion(text, Chatter._QUESTION_TOPIC_RANDOM)

        return resp

    def getTextFor(self, task, text, human_emotion=None, is_spontaneous=False):
        """
        Determines a response for a certain task (e.g., continue conversation proactive, or ask a question),
        starting from text (i.e., using text as a starting point, based on the task)
        taking into account possible human emotion detected
        :param task:
        :param text:
        :param human_emotion:
        :param is_spontaneous:
        :return:
        """
        resp = ""
        try:
            if task == Chatter._TASK_CONTINUE_CONVERSATION:
                resp = self.converser.getResponse(text)
            elif task == Chatter._TASK_CONTINUE_CONVERSATION_PROACTIVE:
                """ The default case.
                Here I just want to use the conversation pipeline to generate a meaningful continuation.
                N.B. is_spontaneous is assumed False"""
                if not self.isQuestion(text):
                    logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "The user did not ask a question, so I try to reply in a more interesting way")
                    if not self.last_robot_said_was_question and random.random() > 0.75:  # in 25% of cases I ask a question, so I don't always go to a dead end
                        logger.log(Constants.LOGGING_LV_DEBUG_NOSAR,
                                   "last time i did not ask a question and random is larger than 0.6 so I ask a question")
                        if (not human_emotion is None) and (not self.asked_about_emotions):
                            resp = self.getQuestion(human_emotion, Chatter._QUESTION_TOPIC_EMOTIONS)
                            self.asked_about_emotions = True #I do it only once in every interaction (i.e., run of code)
                        else:
                            logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "I'm going to ask a question about a random topic")
                            resp = self.getQuestion(text, Chatter._QUESTION_TOPIC_RANDOM)
                        self.last_robot_said_was_question = True
                    else:
                        logger.log(Constants.LOGGING_LV_DEBUG_NOSAR,
                                   "last time i asked a question or random is not larger than 0.6 so I just respond")
                        resp = self.converser.getResponse(text)
                        self.last_robot_said_was_question = False
                else:  # if it's a question I just try to answer
                    if "what time is it" in text.lower():
                        current_time = datetime.now().strftime("%H:%M")
                        resp = "It's "+current_time+"." + (random.choice(["Why do you ask?", "Why?", "How does this make you feel?"]) if random.random()>0.5 else "")
                    else:
                        if not "?" in text:
                            text = text+"?" #this is not really necessary but I found that it helps the language model to give more meaningful answers
                        resp = self.converser.getResponse(text)
                    self.last_robot_said_was_question = False

                if resp == "" or len(resp) < 2:  # If "the robot doesn't know what to say"
                    logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "Robot doesn't know what to say (was going for: {}). I generate a spontaneous question.".format(resp))
                    if random.random()>0.8:
                        resp = self.getSpontaneousQuestion(text)
                        self.last_robot_said_was_question = True
                    else:
                        resp = random.choice([
                            "I'm not really sure what to say now.",
                            "I'm kind of confused right now.",
                            "I'm not sure I understood."
                            "I'm not following. Can you repeat?",
                            "What did you say?"])
                        if "?" in resp:
                            self.last_robot_said_was_question = True
                        else:
                            self.last_robot_said_was_question = False


            if task == Chatter._TASK_ASK_QUESTION:
                """ In this case, I want to generate a question for the user based on the text in argument text.
                I do so via the t2tgenerator. The answer will be the first one returned.
                In case the task is marked as is_spontaneous, I add the question to the conversation with an empty user input.
                Otherwise, the user input is already assumed to be the last one, and I simply add the answer."""
                resp = self.getQuestion(text, Chatter._QUESTION_TOPIC_TEXT)

            if task == Chatter._TASK_CONTINUE_CONVERSATION_SPONTANEOUS:
                """ In this case, I generate a question in a spontaneous way based on the summary of the conversation had so far."""
                resp = self.getSpontaneousQuestion("")

            if task == Chatter._TASK_CONVERSATION_TURN_SPONTANEOUS:
                """ In this case, I generate a question in a spontaneous way based on a text generates starting from an input
                given in the argument text (e.g., this could be an object that has been observed, or some belief, or something else)"""

                types_of_questions = ["Did you know that a " + text,
                                      "What kind of " + text,
                                      "Is that a " + text,
                                      "I noticed a " + text + ". Is it",
                                      "Is that " + text + "",
                                      "What a pretty " + text,
                                      "That's an interesting "+text+". Is it"]
                selected_type_of_question = random.choice(types_of_questions)
                g = self.tgenerator(selected_type_of_question, max_length=50,
                                   do_sample=True,
                                   top_p=0.92,
                                   top_k=100,
                                   temperature=0.75,
                                   num_return_sequences=10)
                resp = g[0]['generated_text'].split("?")[0] + "?"
        except:
            resp = ""

        if (resp == "") or len(resp) < 2:
            # self.converser.initializeVariables()
            resp = "Sorry, can you repeat, please?"
            # self.conversation.generated_responses[len(self.conversation.generated_responses) - 1] = resp

        return resp

    def on_message(self, client, userdata, message):
        """ Function automatically called every time data is received via mqtt"""
        rec_m = str(message.payload.decode("utf-8"))
        logger.info("As a chatter I received data " + str(rec_m))

        if self.noInputBeingProcessed() or not self.chatter_state_machine.is_default:
            # if self.gui_queue is None:
            self.mqtt_publisher.publish(Constants.TOPIC_LEDS,
                                        utils.joinStrings([Constants.DIRECTIVE_LED_SET_THINKING, "True"]))

            self.last_thinking_time = time.time()

            # self.addOneInputBeingProcessed()
            self.chatter_state_machine.process_input(rec_m)

        else:
            if float((datetime.now() - self.max_time_thinking).timestamp()) < float(self.last_thinking_time):
                # if still not enough time passed (when now - x seconds is before last thinking time)
                # then I still wait
                logger.log(Constants.LOGGING_LV_DEBUG_NOSAR,
                           "Note: I ignore this data because there is already one input being processed.")
                logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, self.inputs_being_processed)
                logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, self.chatter_state_machine.is_default)
            else:
                #in this case max thinking time is expired
                logger.log(Constants.LOGGING_LV_DEBUG_NOSAR,
                           "Timer is expired, I ignore the previous sentence and re process the current one")
                self.setOneInputProcessed()
                self.on_message(client, userdata, message)

    def kickstartLMs(self):
        """ Kickstarting the language models to speed up later answers """

        logger.info("Kickstarting Language Models so to speed up interaction with humans...")
        kickstart_conversation_user_inputs = ["Hello!", "You are going to speak with a human, are you ready?",
                                              "Let's begin!"]  # I do it with three sentences because in some cases the randomness will not initiate the dialogue model
        for s in kickstart_conversation_user_inputs:
            # kickstarting the converser
            self.converser.addUserInput(s)
            self.converser.addBotResponseToConversation(self.getTextFor(Chatter._TASK_CONTINUE_CONVERSATION, s, False),
                                                        False)
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
        transformers_logging.set_verbosity(40)

        """ Initializing all language models """
        """ The converser to generate responses in dialogues """
        self.converser = self.Converser("microsoft/DialoGPT-medium")
        # self.converser = self.Converser("facebook/blenderbot-400M-distill")
        # self.converser = self.Converser("microsoft/DialoGPT-large")

        """ The t2t generator is used to generate questions """
        self.t2tgenerator = pipeline("text2text-generation", model="valhalla/t5-base-e2e-qg")
        """ The question-answering is used to generate answers to the self-generate questions"""
        self.question_answerer = pipeline("question-answering", model="deepset/roberta-base-squad2",
                            tokenizer="deepset/roberta-base-squad2")
        """ The summarizer is used to summarize the converstion so far, or to summarize the news """
        self.summarizer = pipeline("summarization")
        """ The text generator is used to generate spontaneous sentences or questions """
        self.tgenerator = pipeline('text-generation', model="facebook/opt-350m")
        """ The temotionclassifier is use for sentiment analysis of the agent's sentences"""
        self.temotion_classifier = pipeline("text-classification", model='bhadresh-savani/bert-base-uncased-emotion',
                                            top_k=1)
        """ The question statement classifier is a classifier that determines whether a sentence is a question or not"""
        self.question_statement_classifier = pipeline("text-classification",
                                                      model='shahrukhx01/question-vs-statement-classifier')

        """ Init spacy, the state machine and different variables"""
        self.nlp = spacy.load("en_core_web_sm")

        self.chatter_state_machine = self.ChatterStateMachine(self)
        self.chatter_state_machine.setup(self.nlp)

        self.last_thinking_time = -1
        self.max_time_thinking = timedelta(seconds=30)

        self.asked_about_emotions = False
        self.to_add_to_next_sentence = None

        """ Kickstarting the language models with a couple initial sentences to speed up answering"""
        self.kickstartLMs()

        """ This dictionary will contain the different inputs that are going to be communicated to the
        data collector and then to the bdi """
        self.received_inputs = {
            Constants.TOPIC_SPEECH: [],
            Constants.TOPIC_NAME_LEARNT: [],
            Constants.TOPIC_INTERNAL_COMMUNICATIONS: []
        }
        self.inputs_being_processed = 0
        self.last_detected_interest = ""
        self.last_robot_said_was_question = False

        """ This will listen to the sensors collecting data """
        self.mqtt_listener = MQTTClient(Constants.MQTT_BROKER_ADDRESS, "NAO_Chatter_Listener",
                                        Constants.MQTT_CLIENT_TYPE_LISTENER, Constants.TOPIC_SPEECH, self.on_message)

        """ This will publish what to say in response """
        self.mqtt_publisher = MQTTClient(Constants.MQTT_BROKER_ADDRESS, "NAO_Chatter_Publisher",
                                         Constants.MQTT_CLIENT_TYPE_PUBLISHER, None, None)

        await super().setup()
