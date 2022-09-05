import time
from datetime import datetime

from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade_bdi.bdi import BDIAgent

import agentspeak

from spade.message import Message

import utils.constants as Constants
import utils.utils as utils
from sar.norm.normativereasoner import NormativeReasoner


class BDICore(BDIAgent):
    def add_custom_actions(self, actions):
        @actions.add(".greet", 1)
        def _greet(agent, term, intention):
            x = str(agentspeak.grounded(term.args[0], intention.scope))
            if x=="unknown":
                to_say = "Hello there! What's your name?"
            else:
                to_say = "Hello "+x+"! What's up?"
            b = self.SendMessageBehaviour(Constants.CHATTER_JID, Constants.PERFORMATIVE_INFORM,
                                          [Constants.DIRECTIVE_SAY, to_say]+self.curr_social_interp)
            self.add_behaviour(b)
            # self.get("socialactuator").sendDirective("say;"+to_say)
            #msg = Message(to=self.get("socialactuator"))  # Instantiate the message
            #msg.body = "say,"+to_say  # Set the message content
            #await self.send(msg)
            yield

        @actions.add(".shut_down", 1)
        def _turn_off(agent, term, intention):
            print("As instructed by "+str(agentspeak.grounded(term.args[0], intention.scope))+", I will start procedure to shut down")
            b = self.SendMessageBehaviour(Constants.SYSTEM_HANDLER_JID, Constants.PERFORMATIVE_INFORM, Constants.DIRECTIVE_SHUT_DOWN)
            self.add_behaviour(b)
            # msg = utils.prepareMessage(Constants.SYSTEM_HANDLER_JID, Constants.PERFORMATIVE_REQUEST, Constants.DIRECTIVE_SHUT_DOWN)
            # await self.send(msg)
            yield

        @actions.add(".reply_to", 2)
        def _reply_to(agent, term, intention):
            # print("As instructed by " + str(
            #     agentspeak.grounded(term.args[0], intention.scope)) + ", I will start procedure to shut down")
            b = self.SendMessageBehaviour(Constants.CHATTER_JID, Constants.PERFORMATIVE_INFORM,
                                          [Constants.DIRECTIVE_REPLY_TO, str(agentspeak.grounded(term.args[1], intention.scope))]+self.curr_social_interp)
            self.add_behaviour(b)
            # msg = utils.prepareMessage(Constants.SYSTEM_HANDLER_JID, Constants.PERFORMATIVE_REQUEST, Constants.DIRECTIVE_SHUT_DOWN)
            # await self.send(msg)
            yield

        @actions.add(".go_to_posture", 1)
        def _go_to_posture(agent, term, intention):
            b = self.SendMessageBehaviour(Constants.POSTURE_HANDLER_JID, Constants.PERFORMATIVE_INFORM,
                                          [Constants.DIRECTIVE_GOTOPOSTURE, str(agentspeak.grounded(term.args[0], intention.scope))]+self.curr_social_interp)
            self.add_behaviour(b)
            yield

        # @actions.add(".my_action", 1)
        # def _my_action(agent, term, intention):
        #     arg = agentspeak.grounded(term.args[0], intention.scope)
        #     print(arg)
        #     yield

    class SendMessageBehaviour(OneShotBehaviour):
        def __init__(self, receiver, performative, message_list):
            super().__init__()
            self.receiver = receiver
            self.performative = performative
            self.message_list = message_list

        async def run(self):
            msg = utils.prepareMessage(self.receiver, self.performative, self.message_list)
            await self.send(msg)

    class SenseReasonAct(CyclicBehaviour):
        async def on_end(self):
            await self.agent.stop()

        async def run(self):
            # print("BDI: Starting one cycle of SENSEREASONACT at " + str(time.time()))
            # sense
            # request the data
            # print("BDI: asking the chatter to give data")
            request_voice_data_msg = utils.prepareMessage(Constants.DATACOLLECTOR_JID, Constants.PERFORMATIVE_REQUEST, None)
            # print("BDI: Sending Message to DATACOLLECTOR at "+ str(time.time()))
            await self.send(request_voice_data_msg)
            # print("BDI Message Sent to DATACOLLECTOR at "+ str(time.time()))
            # print("BDI: waiting for chatter response")
            msg = await self.receive(timeout=0.1)  # wait for a response message for 10 seconds
            if msg:
                # print("BDI: Message received from DATACOLLECTOR at "+ str(time.time()))
                print("BDI: Message received with content: {}".format(msg.body))
                if msg.get_metadata("performative") == Constants.PERFORMATIVE_NEW_BELIEF:
                    belief = utils.splitStringBelToList(msg.body)
                    self.agent.bdi.set_belief(belief[0], belief[1], belief[2])
                    """ here I want then to check the resulting beliefs and see if there are directives
                    in that case, send to the robot, i.e., send the directive to the social actuator which will write them in a file that will be read by the robot"""
                    print(self.agent.bdi.get_belief("directive"))
                elif msg.get_metadata("performative") == Constants.PERFORMATIVE_INFORM:
                    if str(msg.sender) == Constants.CHATTER_JID:
                        # print("Chatter told me "+str(msg.body))
                        msg_body = utils.splitStringToList(msg.body)
                        # print("As a BDI, I instruct chatter to reply only to the last message in the list")
                        response = utils.prepareMessage(Constants.CHATTER_JID, Constants.PERFORMATIVE_INFORM, ["reply_to", msg_body[len(msg_body)-1]])
                        await self.send(response)
                        # print("Message sent to Chatter!")
                    if str(msg.sender) == Constants.DATACOLLECTOR_JID:
                        # print("Chatter told me "+str(msg.body))
                        # print(msg.body)
                        msg_body = utils.splitStringToList(msg.body)
                        for b in msg_body:
                            bel = utils.splitStringBelToList(b)
                            if bel[0]=="social_eval":
                                self.agent.curr_social_interp = bel

                                #first I remove the previous norms
                                self.agent.removePrevNorms()
                                #then I get the norms applicable in the current context
                                applicable_norms = self.agent.normative_reasoner.getApplicableNorms(self.agent.curr_social_interp[1:len(self.agent.curr_social_interp)])
                                print(applicable_norms) #should be a list of beliefs e.g., proh(<..>)
                                #then I set those norms as new beliefs
                                if len(applicable_norms)>0:
                                    self.agent.bdi.set_belief(*applicable_norms)
                            else:
                                # print(bel)
                                self.agent.bdi.set_belief(*bel)
                            # print(self.agent.bdi.get_beliefs())
                            # print(self.agent.bdi.get_belief("said"))
                        # print("As a BDI, I instruct chatter to reply only to the last message in the list")
                        # response = utils.prepareMessage(Constants.CHATTER_JID, Constants.PERFORMATIVE_INFORM, ["reply_to", msg_body[len(msg_body)-1]])
                        # await self.send(response)
                        # print("Message sent to Chatter!")
                else:
                    print("As a BDI I received a message I don't understand")
            # print("BDI: Ending one cycle of SENSEREASONACT at " + str(time.time()))

    def getBeliefsWithKey(self, key):
        belief_list = []
        #print(self.bdi_agent.beliefs)
        for beliefs in self.bdi_agent.beliefs:
            for i in range(len(list(self.bdi_agent.beliefs[beliefs]))):
                try:
                    rb = str(list(self.bdi_agent.beliefs[beliefs])[i])
                    if rb.startswith(key):
                        #print(rb)
                        raw_belief = [rb.split('(')[0], rb.split('(')[1].split(')')[
                            0]]  # todo assumes that there is only one argument of the belief
                        belief_list.append(raw_belief)
                except IndexError:
                    pass
        return belief_list

    def removePrevNorms(self):
        #first all prohibitions then obligations
        keys = ["prohibited", "obliged"]
        for key in keys:
            for to_rem in self.getBeliefsWithKey(key):
                print(to_rem)
                self.bdi.remove_belief(*to_rem)
                print("removed ", str(to_rem))

    async def setup(self):
       self.curr_social_interp = []
       self.normative_reasoner = NormativeReasoner()
       b = self.SenseReasonAct()
       self.add_behaviour(b)
