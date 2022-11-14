import collections
import random
import time
from datetime import datetime, timedelta

from spade.behaviour import CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour
from spade_bdi.bdi import BDIAgent

import agentspeak

from spade.message import Message

import utils.constants as Constants
import utils.utils as utils
from sar.norm.normativereasoner import NormativeReasoner

import logging
logger = logging.getLogger("nosar.sar.agent.bdicore")

class BDICore(BDIAgent):
    def add_custom_actions(self, actions):
        @actions.add(".greet", 1)
        def _greet(agent, term, intention):
            x = str(agentspeak.grounded(term.args[0], intention.scope))
            msg_body_dict = {**{
                Constants.SPADE_MSG_DIRECTIVE: Constants.DIRECTIVE_BEGIN_GREETING,
                Constants.SPADE_MSG_PERSON: x,
                Constants.SPADE_MSG_NAO_ROLE: self.curr_role,
                Constants.SPADE_MSG_HUMAN_EMOTION: self.curr_emotion
            }, **self.curr_social_interp}

            b = self.SendMessageBehaviour(Constants.CHATTER_JID, Constants.PERFORMATIVE_INFORM, msg_body_dict)
            self.add_behaviour(b)

            yield

        @actions.add(".goodbye", 1)
        def _goodbye(agent, term, intention):
            logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "in action .goodbye")
            x = str(agentspeak.grounded(term.args[0], intention.scope))
            to_say = random.choice(
                ["Bye bye " + ("" if x == Constants.ASL_FLUENT_UNKNOWN_PERSON else x) + "!", "Dooi Dooi!",
                 "See you another time " + ("" if x == Constants.ASL_FLUENT_UNKNOWN_PERSON else x) + "!"])

            msg_body_dict = {**{
                Constants.SPADE_MSG_DIRECTIVE: Constants.DIRECTIVE_SAY_IN_RESPONSE,
                Constants.SPADE_MSG_TO_SAY: to_say,
                Constants.SPADE_MSG_NAO_ROLE: self.curr_role,
                Constants.SPADE_MSG_HUMAN_EMOTION: self.curr_emotion
            }, **self.curr_social_interp}

            b = self.SendMessageBehaviour(Constants.CHATTER_JID, Constants.PERFORMATIVE_INFORM, msg_body_dict)
            self.add_behaviour(b)

            yield

        @actions.add(".shut_down", 1)
        def _turn_off(agent, term, intention):
            logger.info("As instructed by " + str(
                agentspeak.grounded(term.args[0], intention.scope)) + ", I will start procedure to shut down")

            msg_body_dict = {**{
                Constants.SPADE_MSG_DIRECTIVE: Constants.DIRECTIVE_SHUT_DOWN,
                Constants.SPADE_MSG_NAO_ROLE: self.curr_role,
                Constants.SPADE_MSG_HUMAN_EMOTION: self.curr_emotion
            }, **self.curr_social_interp}

            b = self.SendMessageBehaviour(Constants.SYSTEM_HANDLER_JID, Constants.PERFORMATIVE_INFORM, msg_body_dict)
            self.add_behaviour(b)

            # since the user input was a command, no reply is necessary, so I notify the chatter
            msg_body_dict_chatter = {**{
                Constants.SPADE_MSG_DIRECTIVE: Constants.DIRECTIVE_SET_USER_INPUT_PROCESSED_WITH_NO_REPLY,
                Constants.SPADE_MSG_NAO_ROLE: self.curr_role,
                Constants.SPADE_MSG_HUMAN_EMOTION: self.curr_emotion
            }, **self.curr_social_interp}
            b_ch = self.SendMessageBehaviour(Constants.CHATTER_JID, Constants.PERFORMATIVE_INFORM, msg_body_dict_chatter)
            self.add_behaviour(b_ch)

            yield

        @actions.add(".set_role", 1)
        def _set_role(agent, term, intention):
            self.setRole(str(agentspeak.grounded(term.args[0], intention.scope)))
            yield

        @actions.add(".set_human_emotion", 1)
        def _set_human_emotion(agent, term, intention):
            self.setEmotion(str(agentspeak.grounded(term.args[0], intention.scope)))
            yield

        @actions.add(".reply_to_reactive", 2)
        def _reply_to_reactive(agent, term, intention):
            logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "in action .reply_to_reactive")
            msg_body_dict = {**{
                Constants.SPADE_MSG_DIRECTIVE: Constants.DIRECTIVE_REPLY_TO_REACTIVE,
                Constants.SPADE_MSG_SAID: str(agentspeak.grounded(term.args[1], intention.scope)),
                Constants.SPADE_MSG_NAO_ROLE: self.curr_role,
                Constants.SPADE_MSG_HUMAN_EMOTION: self.curr_emotion
            }, **self.curr_social_interp}
            b = self.SendMessageBehaviour(Constants.CHATTER_JID, Constants.PERFORMATIVE_INFORM, msg_body_dict)
            self.add_behaviour(b)
            yield

        @actions.add(".reply_to_proactive", 2)
        def _reply_to_proactive(agent, term, intention):
            logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "in action .reply_to_proactive")
            msg_body_dict = {**{
                Constants.SPADE_MSG_DIRECTIVE: Constants.DIRECTIVE_REPLY_TO_PROACTIVE,
                Constants.SPADE_MSG_SAID: str(agentspeak.grounded(term.args[1], intention.scope)),
                Constants.SPADE_MSG_NAO_ROLE: self.curr_role,
                Constants.SPADE_MSG_HUMAN_EMOTION: self.curr_emotion
            }, **self.curr_social_interp}
            b = self.SendMessageBehaviour(Constants.CHATTER_JID, Constants.PERFORMATIVE_INFORM, msg_body_dict)
            self.add_behaviour(b)
            yield

        @actions.add(".go_to_posture", 1)
        def _go_to_posture(agent, term, intention):
            posture = str(agentspeak.grounded(term.args[0], intention.scope))
            logger.info("PERFORMING ACTION go to posture {}".format(posture))

            msg_body_dict = {**{
                Constants.SPADE_MSG_DIRECTIVE: Constants.DIRECTIVE_GOTOPOSTURE,
                Constants.SPADE_MSG_POSTURE: posture,
                Constants.SPADE_MSG_NAO_ROLE: self.curr_role,
                Constants.SPADE_MSG_HUMAN_EMOTION: self.curr_emotion
            }, **self.curr_social_interp}

            b = self.SendMessageBehaviour(Constants.POSTURE_HANDLER_JID, Constants.PERFORMATIVE_INFORM, msg_body_dict)
            self.add_behaviour(b)

            # since the user input was a command, no reply is necessary, so I notify the chatter
            msg_body_dict_chatter = {**{
                Constants.SPADE_MSG_DIRECTIVE: Constants.DIRECTIVE_SET_USER_INPUT_PROCESSED_WITH_NO_REPLY,
                Constants.SPADE_MSG_NAO_ROLE: self.curr_role,
                Constants.SPADE_MSG_HUMAN_EMOTION: self.curr_emotion
            }, **self.curr_social_interp}
            b_ch = self.SendMessageBehaviour(Constants.CHATTER_JID, Constants.PERFORMATIVE_INFORM,
                                             msg_body_dict_chatter)
            self.add_behaviour(b_ch)
            yield

        @actions.add(".play_animation", 1)
        def _play_animation(agent, term, intention):
            animation = str(agentspeak.grounded(term.args[0], intention.scope))
            logger.info("PERFORMING ACTION play_animation {}".format(animation))

            msg_body_dict = {**{
                Constants.SPADE_MSG_DIRECTIVE: Constants.DIRECTIVE_PLAYANIMATION,
                Constants.SPADE_MSG_POSTURE: animation,
                Constants.SPADE_MSG_NAO_ROLE: self.curr_role,
                Constants.SPADE_MSG_HUMAN_EMOTION: self.curr_emotion
            }, **self.curr_social_interp}

            b = self.SendMessageBehaviour(Constants.POSTURE_HANDLER_JID, Constants.PERFORMATIVE_INFORM, msg_body_dict)
            self.add_behaviour(b)

            # since the user input was a command, no reply is necessary, so I notify the chatter
            msg_body_dict_chatter = {**{
                Constants.SPADE_MSG_DIRECTIVE: Constants.DIRECTIVE_SET_USER_INPUT_PROCESSED_WITH_NO_REPLY,
                Constants.SPADE_MSG_NAO_ROLE: self.curr_role,
                Constants.SPADE_MSG_HUMAN_EMOTION: self.curr_emotion
            }, **self.curr_social_interp}
            b_ch = self.SendMessageBehaviour(Constants.CHATTER_JID, Constants.PERFORMATIVE_INFORM,
                                             msg_body_dict_chatter)
            self.add_behaviour(b_ch)
            yield

        @actions.add(".move_head", 1)
        def _move_head(agent, term, intention):
            direction = str(agentspeak.grounded(term.args[0], intention.scope))
            if (not direction == Constants.ASL_FLUENT_CENTER_DIRECTION) and (
            not self.isInRecentMemory(Constants.ASL_BEL_MOVED_HEAD_PREFIX + direction)):
                min_last_n_consecutive_batches = 2  # todo this could be changed into seconds instead of times...
                if len(self.memory.keys()) >= min_last_n_consecutive_batches:
                    reverse_order_mem = self.getOrderedMemoryFromYoungestToOldest()
                    n_last_consec_batches_is_looking = 0
                    for k, bel_batch in reverse_order_mem.items():
                        # print(bel_batch)
                        found_in_batch = False
                        for bel in bel_batch:
                            if ((Constants.ASL_BEL_IS_LOOKING in bel) and (
                                    direction in bel)):  # if is_looking(Person, Direction) in bel
                                n_last_consec_batches_is_looking += 1
                                found_in_batch = True
                        if ((not found_in_batch) and (n_last_consec_batches_is_looking > 0)) or (
                                n_last_consec_batches_is_looking >= min_last_n_consecutive_batches):
                            break  # I stop at the first occurrence on not having is_looking in the direction counting from the first occurrence

                    if n_last_consec_batches_is_looking >= min_last_n_consecutive_batches:
                        msg_body_dict = {**{
                            Constants.SPADE_MSG_DIRECTIVE: Constants.DIRECTIVE_MOVEHEAD,
                            Constants.SPADE_MSG_POSTURE: direction,
                            Constants.SPADE_MSG_NAO_ROLE: self.curr_role,
                            Constants.SPADE_MSG_HUMAN_EMOTION: self.curr_emotion
                        }, **self.curr_social_interp}

                        b = self.SendMessageBehaviour(Constants.POSTURE_HANDLER_JID, Constants.PERFORMATIVE_INFORM,
                                                      msg_body_dict)
                        self.add_behaviour(b)
                        self.setBelief(time.time(), [Constants.ASL_BEL_MOVED_HEAD_PREFIX + direction])
                # else:
                #     print("actually NOT PERFORMING ACTION move head because the person was looking ", direction, " for less than ", min_last_n_consecutive_batches, " times (",n_last_consec_batches_is_looking,") in recent memory")

            yield

        @actions.add(".establish_trust", 1)
        def _establish_trust(agent, term, intention):
            if not self.isInRecentMemory(Constants.ASL_BEL_ESTABLISHED_TRUST):
                logger.info("action establish trust")
                x = str(agentspeak.grounded(term.args[0], intention.scope))
                if x == Constants.ASL_FLUENT_UNKNOWN_PERSON:
                    to_say = "Oh, I see. Thank you for trusting me."
                else:
                    to_say = str(x) + ", thank you for trusting me with this."

                msg_body_dict = {**{
                    Constants.SPADE_MSG_DIRECTIVE: Constants.DIRECTIVE_SAY_IN_RESPONSE,
                    Constants.SPADE_MSG_TO_SAY: to_say,
                    Constants.SPADE_MSG_NAO_ROLE: self.curr_role,
                    Constants.SPADE_MSG_HUMAN_EMOTION: self.curr_emotion
                }, **self.curr_social_interp}

                b = self.SendMessageBehaviour(Constants.CHATTER_JID, Constants.PERFORMATIVE_INFORM, msg_body_dict)
                self.add_behaviour(b)

                msg_body_dict_posture = {**{
                    Constants.SPADE_MSG_DIRECTIVE: Constants.DIRECTIVE_PLAYANIMATION,
                    Constants.SPADE_MSG_POSTURE: Constants.ANIMATION_ESTABLISH_TRUST,
                    Constants.SPADE_MSG_NAO_ROLE: self.curr_role,
                    Constants.SPADE_MSG_HUMAN_EMOTION: self.curr_emotion
                }, **self.curr_social_interp}

                b = self.SendMessageBehaviour(Constants.POSTURE_HANDLER_JID, Constants.PERFORMATIVE_INFORM,
                                              msg_body_dict_posture)
                self.add_behaviour(b)

                self.setBelief(time.time(), [Constants.ASL_BEL_ESTABLISHED_TRUST, x])
            yield

        @actions.add(".update_topic_of_interest", 3)
        def _update_topic_of_interest(agent, term, intention):
            # print("As instructed by " + str(
            #     agentspeak.grounded(term.args[0], intention.scope)) + ", I will start procedure to shut down")
            if not self.isInRecentMemory(Constants.ASL_BEL_UPDATED_TOPIC_INTEREST):
                person = str(agentspeak.grounded(term.args[0], intention.scope))
                object = str(agentspeak.grounded(term.args[1], intention.scope))
                direction = str(agentspeak.grounded(term.args[2], intention.scope))
                msg_body_dict = {**{
                    Constants.SPADE_MSG_DIRECTIVE: Constants.DIRECTIVE_UPDATE_TOPIC_INTEREST,
                    Constants.SPADE_MSG_PERSON: person,
                    Constants.SPADE_MSG_OBJECT: object,
                    Constants.SPADE_MSG_DIRECTION: direction,
                    Constants.SPADE_MSG_NAO_ROLE: self.curr_role,
                    Constants.SPADE_MSG_HUMAN_EMOTION: self.curr_emotion
                }, **self.curr_social_interp}

                b = self.SendMessageBehaviour(Constants.CHATTER_JID, Constants.PERFORMATIVE_INFORM, msg_body_dict)
                self.add_behaviour(b)
                # msg = utils.prepareMessage(Constants.SYSTEM_HANDLER_JID, Constants.PERFORMATIVE_REQUEST, Constants.DIRECTIVE_SHUT_DOWN)
                # await self.send(msg)
                self.setBelief(time.time(), [Constants.ASL_BEL_UPDATED_TOPIC_INTEREST, object, direction])
            yield

        @actions.add(".execute_action", 1)
        def _execute_action(agent, term, intention):
            logger.error("I should PERFORM ACTION (not doing anything actually at the moment) {}".format(str(agentspeak.grounded(term.args[0], intention.scope))))
            yield

        @actions.add(".trigger_spontaneous_conversation", 0)
        def _trigger_spontaneous_conversation(agent, term, intention):
            logger.info("I trigger a spontaneous conversation, if needed ")
            """ What I want to do is the following:
            1. check if in the memory tehre is some "said", if yes then do nothing
            2. if not, then communicate to the chatter to Constants.DIRECTIVE_CONTINUE_CONVERSATION"""
            # said_sth_recently = False
            # for k in list(self.memory.keys()):
            #     for b in self.memory[k]:
            #         if "said" in b:
            #             said_sth_recently = True
            #             break
            # if not said_sth_recently:
            if not self.isInRecentMemory(Constants.ASL_BEL_SAID):  # if nothing said something recently
                msg_body_dict = {**{
                    Constants.SPADE_MSG_DIRECTIVE: Constants.DIRECTIVE_CONTINUE_CONVERSATION,
                    Constants.SPADE_MSG_NAO_ROLE: self.curr_role,
                    Constants.SPADE_MSG_HUMAN_EMOTION: self.curr_emotion
                }, **self.curr_social_interp}

                b = self.SendMessageBehaviour(Constants.CHATTER_JID, Constants.PERFORMATIVE_INFORM, msg_body_dict)
                self.add_behaviour(b)
            yield

        @actions.add(".update_topic_perception", 1)
        def _update_topic_perception(agent, term, intention):
            object_perceived = str(agentspeak.grounded(term.args[0], intention.scope))
            # already_updated_topic_recently = False
            # for k in list(self.memory.keys()):
            #     for b in self.memory[k]:
            #         # if (("updated_topic" in b) and (object in b)):
            #         if (("updated_topic" in b)):
            #             already_updated_topic_recently = True
            #             break
            # if not already_updated_topic_recently:
            if not self.isInRecentMemory(Constants.ASL_BEL_UPDATED_TOPIC_PERC):
                # times_perceived_object_recently = self.countInRecentMemory(["perceived_object", object])
                # times_perceived_object_recently = 0
                # for k in list(self.memory.keys()):
                #     for b in self.memory[k]:
                #         if ("perceived_object" in b and (object in b)):
                #             times_perceived_object_recently += 1
                # if times_perceived_object_recently <= 1:
                if self.countInRecentMemory([Constants.ASL_BEL_PERCEIVED_OBJECT, object_perceived]) <= 1:
                    msg_body_dict = {**{
                        Constants.SPADE_MSG_DIRECTIVE: Constants.DIRECTIVE_TURN_CONVERSATION,
                        Constants.SPADE_MSG_OBJECT: object_perceived,
                        Constants.SPADE_MSG_NAO_ROLE: self.curr_role,
                        Constants.SPADE_MSG_HUMAN_EMOTION: self.curr_emotion
                    }, **self.curr_social_interp}

                    b = self.SendMessageBehaviour(Constants.CHATTER_JID, Constants.PERFORMATIVE_INFORM, msg_body_dict)
                    self.add_behaviour(b)
                    self.setBelief(time.time(), [Constants.ASL_BEL_UPDATED_TOPIC_PERC, object_perceived])
            yield

        @actions.add(".tell_what_you_see", 0)
        def _tell_what_you_see(agent, term, intention):
            logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "telling what I see")
            visible_things = []
            # print("BDI: ", self.bdi_agent.beliefs)
            for beliefs in self.bdi_agent.beliefs:
                for i in range(len(list(self.bdi_agent.beliefs[beliefs]))):
                    try:
                        rb = str(list(self.bdi_agent.beliefs[beliefs])[i])
                        # print("BDI: ",rb)
                        new_b = rb
                        if Constants.ASL_SOURCE_PERCEPT_SUFFIX in rb:
                            new_b = rb.replace(Constants.ASL_SOURCE_PERCEPT_SUFFIX, "")
                        b_terms_vs_rest = new_b.split("(")
                        b_term = b_terms_vs_rest[0]
                        b_arg_list = []
                        try:
                            b_arg_list = (b_terms_vs_rest[1].replace(")", "")).split(",")
                        except:
                            pass
                        if b_term.startswith(Constants.ASL_BEL_PERCEIVED_OBJECT):
                            visible_things.append(str(b_arg_list[0]).replace("_", " "))
                    except IndexError:
                        pass
            # print("BDI: visible things: ", visible_things)
            to_say = ""
            if len(visible_things) > 1:
                to_say = "Either a "
                for vt_i in range(len(visible_things)):
                    to_say = to_say + visible_things[vt_i] + ("" if vt_i == len(visible_things) - 1 else " or a ")
            elif len(visible_things) == 1:
                to_say = "A " + visible_things[0] + ", I think."
            else:
                to_say = "Nothing really."

            msg_body_dict = {**{
                Constants.SPADE_MSG_DIRECTIVE: Constants.DIRECTIVE_SAY_IN_RESPONSE,
                Constants.SPADE_MSG_TO_SAY: to_say,
                Constants.SPADE_MSG_NAO_ROLE: self.curr_role,
                Constants.SPADE_MSG_HUMAN_EMOTION: self.curr_emotion
            }, **self.curr_social_interp}

            self.add_behaviour(
                self.SendMessageBehaviour(Constants.CHATTER_JID, Constants.PERFORMATIVE_INFORM, msg_body_dict))
            yield

        @actions.add(".tell_what_user_said", 0)
        def _tell_what_user_said(agent, term, intention):
            logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "telling what user said")
            msg_body_dict = {**{
                Constants.SPADE_MSG_DIRECTIVE: Constants.DIRECTIVE_SAY_WHAT_USER_SAID,
                Constants.SPADE_MSG_NAO_ROLE: self.curr_role,
                Constants.SPADE_MSG_HUMAN_EMOTION: self.curr_emotion
            }, **self.curr_social_interp}
            self.add_behaviour(
                self.SendMessageBehaviour(Constants.CHATTER_JID, Constants.PERFORMATIVE_INFORM, msg_body_dict))
            yield

        @actions.add(".tell_what_you_said", 0)
        def _tell_what_you_said(agent, term, intention):
            logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "telling what bot said")
            msg_body_dict = {**{
                Constants.SPADE_MSG_DIRECTIVE: Constants.DIRECTIVE_SAY_WHAT_BOT_SAID,
                Constants.SPADE_MSG_NAO_ROLE: self.curr_role,
                Constants.SPADE_MSG_HUMAN_EMOTION: self.curr_emotion
            }, **self.curr_social_interp}
            self.add_behaviour(
                self.SendMessageBehaviour(Constants.CHATTER_JID, Constants.PERFORMATIVE_INFORM, msg_body_dict))
            yield

        @actions.add(".tell_beliefs", 1)
        def _tell_beliefs(agent, term, intention):
            logger.info("telling beliefs, commanded by {}".format(str(agentspeak.grounded(term.args[0], intention.scope))))
            belief_list = []
            # print(self.bdi_agent.beliefs)
            for beliefs in self.bdi_agent.beliefs:
                for i in range(len(list(self.bdi_agent.beliefs[beliefs]))):
                    try:
                        rb = str(list(self.bdi_agent.beliefs[beliefs])[i])
                        belief_list.append(rb)
                    except IndexError:
                        pass

            # self.add_behaviour(self.SendMessageBehaviour(Constants.CHATTER_JID, Constants.PERFORMATIVE_INFORM,
            #                                              [Constants.DIRECTIVE_SAY_IN_RESPONSE, "Well, I know many things. But I think what you want to know is the following."] + self.curr_social_interp))
            knowledge_response = ""
            for b in belief_list:
                # print(b)
                is_from_perc = False
                new_b = b
                if Constants.ASL_SOURCE_PERCEPT_SUFFIX in b:
                    is_from_perc = True
                    new_b = b.replace(Constants.ASL_SOURCE_PERCEPT_SUFFIX, "")
                b_terms_vs_rest = new_b.split("(")
                b_term = b_terms_vs_rest[0]
                b_arg_list = []
                try:
                    b_arg_list = (b_terms_vs_rest[1].replace(")", "")).split(",")
                except:
                    pass

                to_say = ""
                # if is_from_perc:
                #     to_say = "I can see that "
                if b_term.startswith(Constants.ASL_BEL_IS_ADMIN):
                    to_say = to_say + str(b_arg_list[0]) + " is an admin."
                elif b_term.startswith(Constants.ASL_BEL_IS_LOOKING):
                    to_say = to_say + "you were just looking at your " + str(b_arg_list[1]).replace("_", " ") + "."
                elif b_term == "is":
                    to_say = to_say + "there is a " + str(b_arg_list[1]) + " at your " + str(b_arg_list[0]).replace("_",
                                                                                                                    " ") + "."
                elif b_term.startswith(Constants.ASL_BEL_DISTANCE):
                    to_say = to_say + "you were just at a distance that I consider to be" + str(b_arg_list[1]).replace(
                        "_", " ") + "."
                elif b_term.startswith(Constants.ASL_BEL_PERCEIVED_OBJECT):
                    to_say = to_say + "I can see a " + str(b_arg_list[0]).replace("_", " ") + " over there."
                elif b_term.startswith(Constants.ASL_BEL_UPDATED_TOPIC_PERC):
                    to_say = to_say + "I recently said something because I noticed a " + str(b_arg_list[0]).replace("_",
                                                                                                                    " ") + " right there."
                else:
                    to_say = ""
                if not to_say == "":
                    knowledge_response += " " + to_say
                    # self.add_behaviour(self.SendMessageBehaviour(Constants.CHATTER_JID, Constants.PERFORMATIVE_INFORM,
                    # [Constants.DIRECTIVE_SAY_SPONTANEOUS, to_say] + self.curr_social_interp))
            if not knowledge_response == "":
                knowledge_response = "Well, I know many things. But I think what you want to know is the following. " + knowledge_response
            else:
                knowledge_response = "I know that I know nothing!"

            msg_body_dict = {**{
                Constants.SPADE_MSG_DIRECTIVE: Constants.DIRECTIVE_SAY_IN_RESPONSE,
                Constants.SPADE_MSG_TO_SAY: knowledge_response,
                Constants.SPADE_MSG_NAO_ROLE: self.curr_role,
                Constants.SPADE_MSG_HUMAN_EMOTION: self.curr_emotion
            }, **self.curr_social_interp}

            self.add_behaviour(
                self.SendMessageBehaviour(Constants.CHATTER_JID, Constants.PERFORMATIVE_INFORM, msg_body_dict))
            yield

        # @actions.add(".my_action", 1)
        # def _my_action(agent, term, intention):
        #     arg = agentspeak.grounded(term.args[0], intention.scope)
        #     print(arg)
        #     yield

    class SendMessageBehaviour(OneShotBehaviour):
        def __init__(self, receiver, performative, message_body_dict, thread=None, metadata=None):
            super().__init__()
            self.receiver = receiver
            self.performative = performative
            self.thread = thread
            self.metadata = metadata
            self.message_body_dict = message_body_dict

        async def run(self):
            msg = utils.prepareMessage(self.agent.jid, self.receiver, self.performative, self.message_body_dict,
                                       self.thread, self.metadata)
            # print("sending message ", msg, "to ", self.receiver)
            await self.send(msg)

    class ManageMemoryBehaviour(PeriodicBehaviour):
        def __init__(self, period, start_at, beliefs_memory_size_seconds=60, long_term_memory_size_seconds=300):
            super().__init__(period, start_at)
            self.memory_size_seconds = beliefs_memory_size_seconds
            self.long_term_memory_size_seconds = long_term_memory_size_seconds
            self.memory_size = timedelta(seconds=self.memory_size_seconds)
            self.long_term_memory_size = timedelta(seconds=self.memory_size_seconds)

        async def run(self):
            # print("Running ManageMemoryBehavior...")
            # print("Memory at the beginning of run: ")
            # print(self.agent.memory)
            """ This behavior deletes the beliefs that are older than self.memory_size seconds
                            It assumes that every belief that is subject to deletion is a perceived belief."""

            oldest_time_timestamp_long_term = (datetime.now() - self.long_term_memory_size).timestamp()
            oldest_time_timestamp_beliefs = (datetime.now() - self.memory_size).timestamp()
            # print("deleting from memory that is older than memory_size_seconds seconds")
            for k in list(self.agent.memory.keys()):
                if float(k) < float(oldest_time_timestamp_long_term):
                    del self.agent.memory[k]  # todo here instead of deleting I could actually store it in some csv

            # print("Retrieving all behaviors that have source percept")
            source = "[source(percept)]"
            bel_list = self.agent.getBeliefsFromSource(source)
            # print(bel_list)

            for bel in bel_list:
                found = False
                for k in list(self.agent.memory.keys()):
                    if float(k) >= float(oldest_time_timestamp_beliefs):
                        for b in self.agent.memory[k]:
                            if str(bel) == self.agent.getBeliefString(b, source=source):
                                # print("Found bel ", str(bel), " in ", self.agent.memory[k])
                                found = True
                                break
                    if found:
                        break
                if not found:
                    # print("Bel ", bel, " is older than ", self.memory_size_seconds, " seconds. Removing it...")
                    self.agent.bdi.remove_belief(*self.agent.getListFromBeliefString(str(bel)))

            logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "Memory at the end of run: ")
            logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, self.agent.memory)

    class SpontaneousConversationBehaviour(PeriodicBehaviour):
        """ A periodic behavior that is run every period seconds and triggers a spontaneoous conversation
        which could be (or not) triggered and pursued based on the current status of conversation """

        def __init__(self, period, start_at):
            super().__init__(period, start_at)

        async def run(self):
            self.agent.bdi.set_belief(Constants.ASL_BEL_ADD_SPONT_CONV_GOAL)

    class SenseReasonAct(CyclicBehaviour):
        async def on_end(self):
            await self.agent.stop()

        async def run(self):
            # print("BDI: Starting one cycle of SENSEREASONACT at " + str(time.time()))
            # sense
            # request the data
            # print("BDI: asking the chatter to give data")
            request_msg_from_data_collector = utils.prepareMessage(self.agent.jid,
                                                                   Constants.DATA_COLLECTOR_JID,
                                                                   Constants.PERFORMATIVE_REQUEST,
                                                                   msg_body={})
            # print("BDI: Sending Message to DATACOLLECTOR at "+ str(time.time()))
            await self.send(request_msg_from_data_collector)
            # print("BDI Message Sent to DATACOLLECTOR at "+ str(time.time()))
            # print("BDI: waiting for chatter response")
            msg = await self.receive(timeout=0.1)  # wait for a response message for x seconds
            if msg:
                if msg.get_metadata(Constants.SPADE_MSG_METADATA_PERFORMATIVE) == Constants.PERFORMATIVE_INFORM:
                    if str(msg.sender) == Constants.DATA_COLLECTOR_JID:
                        logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "Data Collector told me {}".format(str(msg.body)))
                        msg_body = utils.readMessage(msg.body, msg.metadata)
                        self.reasonAndAct(msg_body)
                    else:
                        logger.error("Received a message from {}. Currently not supported".format(str(msg.sender)))
                else:
                    logger.error("As a BDI I received a message from {} that I don't understand: {}".format(str(msg.sender), str(msg.body)))

            # print("BDI: Ending one cycle of SENSEREASONACT at " + str(time.time()))

        def reasonAndAct(self, batch_of_beliefs_dict):
            # print("BDI: entering reason and act")
            self.prepareForNextCycle()  # this should remove all outdated beliefs
            self.addNewBeliefs(
                batch_of_beliefs_dict)  # this should add all new beliefs received by the data collector, without triggering the reasoning yet
            self.performReasoning()  # start the reasoning (normative and non)

        def prepareForNextCycle(self):
            # print("BDI: preparing for next cycle")
            self.agent.bdi.set_belief(Constants.ASL_BEL_PREPARE_FOR_NEXT_CYCLE)
            # self.removePrevNorms()
            self.agent.setRole(Constants.ASL_FLUENT_ROLE_NONE)
            # self.removeBeliefsWithKey("perceived_object")
            # self.removeBeliefsWithKey("distance")
            # self.removeBeliefsWithKey("is_looking")
            # self.removeBeliefsWithKey("saw")

        def addNewBeliefs(self, batch_of_beliefs_dict):
            # print("BDI: adding new beliefs")

            batch = batch_of_beliefs_dict[Constants.SPADE_MSG_BATCH_ID]

            """ I first set possible beliefs about the name of the person.
            In this way later inference will be able to use this info"""
            for key, bel in batch_of_beliefs_dict.items():
                if key == Constants.ASL_BEL_PERSON_NAME or key == Constants.ASL_BEL_VISIBLE:  # note for these it is assumed that there is only one possible belief, so the key is checked to be ==
                    # print("BDI: setting belief ", bel, "for batch ", batch)
                    self.agent.setBelief(batch, bel)  # IT IS ASSUMED THAT BEL IS A LIST
            # for b in new_bel_list:
            #     bel = utils.splitStringBelToList(b)
            #     if ("person_name" in bel) or ("visible" in bel):
            #         self.agent.setBelief(batch, bel)

            """ and then I just process all other beliefs """
            for key, bel in batch_of_beliefs_dict.items():
                if key == Constants.SPADE_MSG_BATCH_ID:
                    continue
                elif key == Constants.SPADE_MSG_SOCIAL_EVAL:
                    self.agent.curr_social_interp = bel
                    # print("BDI: new social interp is ", self.agent.curr_social_interp)
                else:  # I am actually not using this key
                    # print("BDI: setting belief ", bel, "for batch ", batch)
                    self.agent.setBelief(batch,
                                         bel)  # note I may set again the beliefs above, but they will just be replaced (little waste here)

            # for b in new_bel_list:
            #     bel = utils.splitStringBelToList(b)
            #     if bel[0] == "social_eval":
            #         self.agent.curr_social_interp = bel
            #         print("BDI updating current social interpr to: ", bel)
            #         print("new social interp is ", self.agent.curr_social_interp)
            #     else:
            #         self.agent.setBelief(batch, bel)

        def performReasoning(self):
            # print("BDI: performing reasoning")

            # N.B. I could also perform some "external" (normative) reasoning
            # external to agentsopeak
            # by invoking some other functions and then setting/removing the opportune beliefs/goals
            self.agent.bdi.set_belief(Constants.ASL_BEL_PERFORM_REASONING)

        def removePrevNorms(self):
            # first all prohibitions then obligations
            for key in Constants.ASL_BEL_PROHIBITIONS_OBLIGATIONS:
                self.removeBeliefsWithKey(key)

        def removeBeliefsWithKey(self, key):
            for to_rem in self.agent.getBeliefsWithKey(key):
                # print(to_rem)
                self.agent.bdi.remove_belief(*to_rem)
                # print("removed ", str(to_rem))

    def getBeliefsWithKey(self, key, annotation=None):
        # print("getting beliefs with key ", key)
        belief_list = []
        # print(self.bdi_agent.beliefs)
        for beliefs in self.bdi_agent.beliefs:
            for i in range(len(list(self.bdi_agent.beliefs[beliefs]))):
                try:
                    rb = str(list(self.bdi_agent.beliefs[beliefs])[i])
                    # print("rb", rb)
                    if rb.startswith(key) and ((annotation is None) or (rb.endswith(annotation))):
                        raw_belief = self.getListFromBeliefString(
                            rb)
                        # print("raw belief", raw_belief)
                        belief_list.append(raw_belief)
                except IndexError:
                    pass
        return belief_list

    def getBeliefsFromSource(self, source):
        # print("getting beliefs with key ", key)
        belief_list = []
        # print(self.bdi_agent.beliefs)
        for beliefs in self.bdi_agent.beliefs:
            for i in range(len(list(self.bdi_agent.beliefs[beliefs]))):
                try:
                    rb = list(self.bdi_agent.beliefs[beliefs])[i]
                    # print(".................rb", rb)
                    if str(rb).endswith(source):
                        belief_list.append(rb)
                except IndexError:
                    pass
        return belief_list

    def setBelief(self, batch_id, bel):
        self.bdi.set_belief(*bel)
        self.addBelToBatch(batch_id, bel)

    def addBelToBatch(self, batch_id, bel: list):
        if batch_id in self.memory:
            self.memory[batch_id].append(bel)
        else:
            self.memory[batch_id] = [bel]

    def getBeliefString(self, bel: list, source=""):
        bel_str = bel[0]
        if len(bel) > 1:
            bel_str += "(" + utils.joinStrings(bel[1:], separator=", ") + ")"
        bel_str += source
        return bel_str

    def getListFromBeliefString(self, bel_str):
        """ bel_str is something like on of the following
        1. bel_name
        2. bel_name(par1, ..., parn)
        3. bel_name[...]
        4. bel_name(par1, ..., parn)[...]
        I return a list, ignoring the source
        """
        b_split_by_source = bel_str.split("[")
        if len(b_split_by_source) == 2:
            source = "[" + b_split_by_source[1]
        else:
            source = None
        b_split_by_args = b_split_by_source[0].split("(")
        b_name = b_split_by_args[0]
        if len(b_split_by_args) == 2:
            b_arg_list = b_split_by_args[1].replace(")", "").split(", ")
        else:
            b_arg_list = []
        return [b_name] + b_arg_list

    def printKnownBeliefs(self):
        for beliefs in self.bdi_agent.beliefs:
            bel_list = list(self.bdi_agent.beliefs[beliefs])
            for i in range(len(bel_list)):
                logger.info(bel_list[i])

    def setRole(self, role):
        self.curr_role = role
        # self.bdi.set_belief(Constants.ASL_BEL_CURR_ROLE, self.curr_role)

    def setEmotion(self, emotion):
        self.curr_emotion = emotion
        # self.bdi.set_belief(Constants.ASL_BEL_CURR_ROLE, self.curr_role)

    def isInRecentMemory(self, text):
        for k in list(self.memory.keys()):
            for b in self.memory[k]:
                if (text in b):
                    return True
        return False

    def countInRecentMemory(self, list_of_val):
        instances = 0
        for k in list(self.memory.keys()):
            for b in self.memory[k]:
                found = True
                for v in list_of_val:
                    if not v in b:
                        found = False
                        break
                if found:
                    instances = instances + 1
        return instances

    def getOrderedMemoryFromYoungestToOldest(self):
        od = collections.OrderedDict(reversed(sorted(self.memory.items())))
        return od

    async def setup(self):
        self.memory = {}
        self.curr_social_interp = {}
        self.curr_role = Constants.ASL_FLUENT_ROLE_NONE
        self.curr_emotion = Constants.ASL_FLUENT_EMOTION_NEUTRAL
        self.normative_reasoner = NormativeReasoner()
        b = self.SenseReasonAct()
        self.add_behaviour(b)
        start_at = datetime.now() + timedelta(seconds=1)
        beliefs_memory_size = 60  # seconds
        long_term_memory_size = 300
        mb = self.ManageMemoryBehaviour(period=beliefs_memory_size, start_at=start_at,
                                        beliefs_memory_size_seconds=beliefs_memory_size,
                                        long_term_memory_size_seconds=long_term_memory_size)
        self.add_behaviour(mb)
        start_at_sb = datetime.now() + timedelta(seconds=300)
        sb = self.SpontaneousConversationBehaviour(period=long_term_memory_size, start_at=start_at_sb)
        self.add_behaviour(sb)
