import time
from datetime import timedelta, datetime

import spade
from spade.behaviour import OneShotBehaviour, PeriodicBehaviour
from spade.message import Message
from spade.template import Template

from sar.agent.workeragent import WorkerAgent

import utils.utils as utils
import utils.constants as Constants


class DataColletor(WorkerAgent):
    """
    Collects data from all different sources, cleans them and sends them to the BDI
    """

    class CollectDataBehaviour(PeriodicBehaviour):
        def __init__(self, period, start_at, data_sources):
            super().__init__(period, start_at)
            self.data_sources = data_sources
            self.timeout_data_source = period

        async def run(self):
            self.agent.current_batch = self.agent.current_batch + 1
            self.batch = self.agent.current_batch
            collected_data = {}
            for d in self.data_sources:
                collected_data[d] = None
            nr_datasources = len(collected_data)
            nr_data_collected = 0

            for data_source in collected_data:
                # print("DataCollector, preparing message for "+str(data_source))
                request_data_msg = utils.prepareMessage(data_source, Constants.PERFORMATIVE_REQUEST, None)
                await self.send(request_data_msg)

            beliefs_to_send = []
            visible_person = "none"

            for d in self.data_sources:
                # using a template here is useful so I create a behavior for every data source
                # and I do not risk that the same data source uses all behaviors for example because faster
                template = Template()
                template.sender = d
                b = self.agent.WaitForMessageBehaviour(self.timeout_data_source, batch=self.batch)
                self.agent.add_behaviour(b, template)

    class WaitForMessageBehaviour(OneShotBehaviour):
        def __init__(self, timeout_data_source, batch):
            super().__init__()
            self.timeout_data_source = timeout_data_source
            self.batch = batch

        async def run(self):
            # print("running behavior of datacollector")
            bel = []
            msg = await self.receive(timeout=self.timeout_data_source)  # wait for a response message
            if msg:
                sender = str(msg.sender)
                print("DataCollector: Message received with content: {}".format(msg.body))
                if sender == Constants.VISION_HANDLER_JID:
                    print(msg.body)
                    vision_data = utils.splitStringToList(msg.body)
                    print(vision_data)
                    vision_data = str(vision_data[len(vision_data) - 1]).lower()  # e.g., taking only the last one here
                    print(vision_data)
                    vision_data_inner = utils.splitStringToList(vision_data, Constants.STRING_SEPARATOR_INNER)
                    print(vision_data_inner)
                    if vision_data_inner[0] == Constants.TOPIC_HUMAN_DETECTION.lower():
                        # self.agent.visible_person = vision_data
                        # bel = utils.joinStringsBel()
                        bel = ["saw", "face", vision_data_inner[1]]
                    if vision_data_inner[0] == Constants.TOPIC_HEAD_TRACKER.lower():
                        direction = "unknown"
                        yaw = int(vision_data_inner[2])
                        pitch = int(vision_data_inner[4])
                        roll = int(vision_data_inner[6])
                        if yaw < 0:
                            if pitch  < 0:
                                direction = "bottom_right"
                            else:
                                direction = "top_right"
                        else:
                            if pitch  < 0:
                                direction = "bottom_left"
                            else:
                                direction = "top_left"
                        bel = ["is_looking", direction]
                    print(bel)
                    # beliefs_to_send.append(bel)
                if sender == Constants.CHATTER_JID:
                    chatter_data = utils.splitStringToList(msg.body)
                    print("============chatter data: ", str(chatter_data))
                    last_chatter_data = str(chatter_data[len(chatter_data) - 1])  # e.g., taking only the last one here
                    last_chatter_data_split = utils.splitStringToList(last_chatter_data,
                                                                      Constants.STRING_SEPARATOR_INNER)
                    last_chatter_data_sentence = last_chatter_data_split[0].replace(" ", Constants.ASL_STRING_SEPARATOR)
                    last_chatter_data_volume = last_chatter_data_split[1].replace(" ", Constants.ASL_STRING_SEPARATOR)
                    bel = ["said", last_chatter_data_sentence, float(last_chatter_data_volume)]
                    print(bel)
                    # beliefs_to_send.append(bel)
                if sender == Constants.POSITION_HANDLER_JID:
                    position_data = utils.splitStringToList(msg.body)
                    position_data = float(position_data[len(position_data) - 1])  # e.g., taking only the last one here
                    # position data is the distance
                    bel = ["dist", position_data]
                    # print(bel)
                await self.agent.addToBatch(self.batch, sender, bel)
            else:  # if timeout reached
                await self.agent.addToBatch(self.batch, utils.getStringFromJID(self.template.sender), bel)

    class SendMsgToBehaviour(OneShotBehaviour):
        def __init__(self, receiver, content):
            super().__init__()
            self.receiver = receiver
            self.content = content

        async def run(self):
            if self.content is None:
                """ This is the default behavior, which sends the msg to the bdi agent"""
                nr_rec_in = len(self.agent.data_to_send)
                for i in range(nr_rec_in):
                    bel = self.agent.data_to_send.pop()
                    # bel_list = []
                    # for i in batch:
                    #     bel_list.extend(batch[i])
                    # if len(bel_list)>0:
                    msg_body = bel
                    # print("sending data as requested to the bdi")
                    # print("sending "+str(msg_body))
                    msg = utils.prepareMessage(self.receiver, Constants.PERFORMATIVE_INFORM, msg_body)
                    await self.send(msg)
                # print("DATACOLLECTOR: Completed running sendmsgtoBehavior at " + str(time.time()))
            else:
                """ Non-default behavior"""
                print("sending data as requested to " + str(self.receiver))
                msg = utils.prepareMessage(self.receiver, Constants.PERFORMATIVE_INFORM, self.content)
                print("sending " + str(msg))
                await self.send(msg)
                print("it says sent")

    async def send_msg_to(self, receiver, content=None):
        # print("As a chatter, I received request from the BDI module to send data")
        # print("DATACOLLECTOR: Received request from BDI at " + str(time.time()))
        b = self.SendMsgToBehaviour(receiver, content)
        # print("DATACOLLECTOR: Created new sendmsgtoBehavior at " + str(time.time()))
        self.add_behaviour(b)

    async def addToBatch(self, batch, sender, bel):

        if not batch in self.work_in_progress_data:
            self.work_in_progress_data[batch] = {}

        self.work_in_progress_data[batch][sender] = bel

        # if I completed the batch
        if len(self.work_in_progress_data[batch]) == len(self.workers_data_sources):
            # print(batch)
            # print(self.work_in_progress_data[batch])
            # print(self.work_in_progress_data)
            """ you should also create all the necessary beliefs from the data"""
            bels_to_add = []

            batch_visible_person = "unknown"
            # chatter_data = None
            # position_data = None

            data = {}

            # vision
            if Constants.VISION_HANDLER_JID in self.workers_data_sources:
                vision_bel_list = self.work_in_progress_data[batch][Constants.VISION_HANDLER_JID]
                # print("vision_bel_list", vision_bel_list)
                if len(vision_bel_list) > 0:
                    if vision_bel_list[0] == "is_looking":
                        bel_string = utils.joinStringsBel(
                            ["is_looking", batch_visible_person]+vision_bel_list[1:])
                        bels_to_add.append(bel_string)
                        print(bel_string)
                    else:
                        bels_to_add.append(utils.joinStringsBel(vision_bel_list))
                        batch_visible_person = vision_bel_list[2]

            # chatter
            if Constants.CHATTER_JID in self.workers_data_sources:
                chatter_bel_list = self.work_in_progress_data[batch][Constants.CHATTER_JID]
                if len(chatter_bel_list) > 0:
                    print("chatter bel list", chatter_bel_list)
                    chatter_data_sentence = chatter_bel_list[1]
                    chatter_data_volume = chatter_bel_list[2]
                    if chatter_data_sentence.lower() in Constants.POSTURES:
                        bel_string = utils.joinStringsBel(
                            ["said", batch_visible_person, Constants.POSTURES[chatter_data_sentence.lower()],
                             "is_posture"])
                    else:
                        bel_string = utils.joinStringsBel(["said", batch_visible_person, chatter_data_sentence])
                    bels_to_add.append(bel_string)
                    data[Constants.LV_COMMUNICATING] = 1.0
                    data[Constants.LV_VOLUME] = float(chatter_data_volume)
                # else:
                #     data[Constants.LV_COMMUNICATING] = 0.0

            # position
            if Constants.POSITION_HANDLER_JID in self.workers_data_sources:
                position_bel_list = self.work_in_progress_data[batch][Constants.POSITION_HANDLER_JID]
                if len(position_bel_list) > 0:
                    position_data = position_bel_list[1]
                    data[Constants.LV_DIST] = position_data


            # alltogether
            """ This next test is very important because it allows to make sure we do not perform inference (social interpretation) if we do not have any data
            (otherwise we give a random interpretation to a context and we don't want this) """
            social_values = None
            best_social_interpr = None

            nr_info = len(data)
            # print("nr info", nr_info)
            if nr_info > 0:
                # if there is some data, then I fill all the rest with "off" values
                # for social_cue in Constants.LV_SOCIAL_CUES:
                #     if not social_cue in data:
                #         data[social_cue] = 0.0
                #
                for fsi_input in self.fsi.fuzzyRuleBase.inputs:
                    if not fsi_input in data:
                        print(fsi_input, "not in data")
                        # print(fsi_input)
                        print(self.fsi.fuzzyRuleBase.ling_vars_dict)
                        print(self.fsi.fuzzyRuleBase.ling_vars_dict[fsi_input])
                        print(self.fsi.fuzzyRuleBase.ling_vars_dict[fsi_input].getDefaultVal())
                        input_default_val = self.fsi.fuzzyRuleBase.ling_vars_dict[fsi_input].getDefaultVal()
                        input_min_val = self.fsi.fuzzyRuleBase.ling_vars_dict[fsi_input].universe_of_discourse[0]
                        print("default val of", fsi_input, ": ", input_default_val)
                        if input_default_val is None:
                            data[fsi_input] = input_min_val
                        else:
                            data[fsi_input] = input_default_val
                # print("data: " + str(data))
                social_values, best_social_interpr = self.fsi.getBestSocialInterpretation(data)

            if best_social_interpr is None:
                best_social_interpr = "UNKNOWN"

            if (not best_social_interpr is None):
                # print("best social interpretation: " + str(best_social_interpr))
                """
                The following test also is very important: we send data to the norm adapter only if there is more than
                one social cue. Otherwise we are not learning/adapting correctly, but only reinforcing knowledge."""
                if nr_info > 1:
                    msg_to_norm_adapter = [Constants.TOPIC_SOCIAL_INTERPR, str(best_social_interpr)]
                    if not social_values is None:
                        for s in social_values:
                            msg_to_norm_adapter.extend([str(s), str(social_values[s])])
                    for d in data:
                        msg_to_norm_adapter.extend([str(d), str(data[d])])
                    send_msg_to_norm_adapter = self.SendMsgToBehaviour(Constants.NORMADAPTER_JID, msg_to_norm_adapter)
                    print("DATACOLLECTOR: Created new sendmsgtoBehavior at " + str(time.time()))
                    print(msg_to_norm_adapter)
                    self.add_behaviour(send_msg_to_norm_adapter)

            if (not social_values is None):
                print("social_values: " + str(social_values))
                # I also create another belief with the current values of social interpretation
                sev = []
                for s in social_values:
                    sev.append(s)
                    sev.append(str(social_values[s]))
                bel_v = utils.joinStringsBel(["social_eval"] + sev)
                bels_to_add.append(bel_v)
                # beliefs_to_send.append(bel)
                if (not batch_visible_person == "none"):
                    bel = utils.joinStringsBel(
                        ["distance", batch_visible_person, str(best_social_interpr).lower()])
                    bels_to_add.append(bel)
                    print(bel)

            if (len(bels_to_add) > 0):
                self.data_to_send.extend(bels_to_add)
            del self.work_in_progress_data[batch]

    async def setup(self):
        await super().setup()
        # self.visible_person = "none"
        self.current_batch = -1
        self.work_in_progress_data = {}

        self.data_to_send = []

        self.workers_data_sources = [Constants.CHATTER_JID,
                                     Constants.POSITION_HANDLER_JID,
                                     Constants.VISION_HANDLER_JID]  # ... here you can add the others, or remove some

        self.workers_data_sources = [Constants.CHATTER_JID]  # ... here you can add the others, or remove some

        start_at = datetime.now() + timedelta(seconds=1)
        b = self.CollectDataBehaviour(period=0.1, start_at=start_at, data_sources=self.workers_data_sources)
        self.add_behaviour(b)
