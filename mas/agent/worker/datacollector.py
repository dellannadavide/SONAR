import logging
import time
from datetime import timedelta, datetime

from spade.behaviour import OneShotBehaviour, PeriodicBehaviour
from spade.template import Template

import utils.constants as Constants
import utils.utils as utils
from mas.agent.workeragent import WorkerAgent

logger = logging.getLogger("nosar.mas.agent.worker.datacollector")


class DataColletor(WorkerAgent):
    """
    Collects data from all different sources, cleans them and sends them to the BDI
    """

    _KEY_DIST_DATA = "dist_data"
    _KEY_VISION_DETECTED_PERSON = "person"
    _KEY_EMOTION_NEUTRAL = "neutral"

    class CollectDataBehaviour(PeriodicBehaviour):
        def __init__(self, period, start_at, data_sources):
            super().__init__(period, start_at)
            self.data_sources = data_sources
            self.timeout_data_source = period

        async def run(self):
            self.agent.current_batch = time.time()
            self.batch = self.agent.current_batch

            for data_source in self.data_sources.keys():
                for thread in self.data_sources[data_source]:
                    # print("DataCollector, preparing message for "+str(data_source))
                    request_data_msg = utils.prepareMessage(sender_jid=self.agent.jid,
                                                            received_jid=data_source,
                                                            performative=Constants.PERFORMATIVE_REQUEST,
                                                            msg_body={},
                                                            thread=thread,
                                                            metadata={Constants.SPADE_MSG_BATCH_ID: str(self.batch)})
                    await self.send(request_data_msg)

            beliefs_to_send = []
            visible_person = "none"

            """ For every source and for every thread I create a waitformessage behavior that will wait for a message """
            for d in self.data_sources.keys():
                # using a template here is useful so I create a behavior for every data source
                # and I do not risk that the same data source uses all behaviors for example because faster
                for thread in self.data_sources[d]:
                    template = Template()
                    template.sender = d
                    template.thread = thread
                    template.metadata = {Constants.SPADE_MSG_BATCH_ID: str(self.batch)}

                    b = self.agent.WaitForMessageBehaviour(self.timeout_data_source, batch=self.batch)
                    self.agent.add_behaviour(b, template)

    class WaitForMessageBehaviour(OneShotBehaviour):
        """ This is the behavior that receives and store data from all the workers.
        Another behavior will later process them and create beliefs to send to the bdi.

        This one shot behavior is regularly run for every source and for every thread
        and waits for a messagee from that source-thread for max timeout_data_source sec.
        """

        def __init__(self, timeout_data_source, batch):
            super().__init__()
            self.timeout_data_source = timeout_data_source
            self.batch = batch
            self.already_added_visible_belief = False

        async def run(self):
            # print("running behavior of datacollector")
            bels = []
            msg = await self.receive(timeout=self.timeout_data_source)  # wait for a response message
            if msg:
                sender = str(msg.sender)
                thread = str(msg.thread)
                msg_body_dict = utils.readMessage(msg.body, msg.metadata)

                logger.info("DataCollector (batch " + str(
                    self.batch) + "): Message received from " + sender + "-" + thread + " with content: {}".format(
                    msg.body))
                """ If the sender is the VISION_HANDLER """
                if sender == Constants.VISION_HANDLER_JID:
                    logger.info("vision data: {}".format(str(msg_body_dict)))
                    vision_data = msg_body_dict[max(msg_body_dict.keys())]
                    logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, vision_data)
                    vision_data_inner = utils.splitStringToList(vision_data, Constants.STRING_SEPARATOR_INNER)
                    logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, vision_data_inner)
                    """ DISTINGUISHING BETWEEEN THREADS """
                    if thread == Constants.TOPIC_HUMAN_DETECTION:

                        face = vision_data_inner[1]
                        if not face == Constants.ASL_FLUENT_UNKNOWN_PERSON:
                            self.agent.interacting_person = face
                        bels.append(
                            [Constants.ASL_BEL_VISIBLE, Constants.ASL_FLUENT_FACE, self.agent.interacting_person])
                        self.already_added_visible_belief = True
                    if thread == Constants.TOPIC_HEAD_TRACKER:
                        direction = Constants.ASL_FLUENT_UNKNOWN_DIRECTION
                        epsilon = 10
                        yaw = int(vision_data_inner[2])
                        pitch = int(vision_data_inner[4])
                        roll = int(vision_data_inner[6])
                        dist = float(vision_data_inner[8])

                        direction_yaw = ""
                        if yaw < 0 - epsilon:
                            direction_yaw = Constants.ASL_FLUENT_RIGHT_DIRECTION
                        elif yaw > 0 + epsilon:
                            direction_yaw = Constants.ASL_FLUENT_LEFT_DIRECTION
                        direction_pitch = ""
                        if pitch < 0 - epsilon:
                            direction_pitch = Constants.ASL_FLUENT_BOTTOM_DIRECTION
                        elif pitch > 0 + epsilon:
                            direction_pitch = Constants.ASL_FLUENT_TOP_DIRECTION

                        if direction_yaw == "":
                            if direction_pitch == "":
                                direction = Constants.ASL_FLUENT_CENTER_DIRECTION
                            else:
                                direction = direction_pitch
                        else:
                            if direction_pitch == "":
                                direction = direction_yaw
                            else:
                                direction = direction_pitch + "_" + direction_yaw

                        bels.append([Constants.ASL_BEL_IS_LOOKING, direction])

                        if dist != -1.0:
                            bels.append([DataColletor._KEY_DIST_DATA, dist])
                        logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "DETECTED DISTANCE IS {}".format(dist))
                    if thread == Constants.TOPIC_OBJECT_DETECTION:
                        for obj in vision_data_inner[1:]:
                            if obj == DataColletor._KEY_VISION_DETECTED_PERSON:
                                if not self.already_added_visible_belief:
                                    bels.append([Constants.ASL_BEL_VISIBLE, Constants.ASL_FLUENT_FACE,
                                                 self.agent.interacting_person])
                            else:
                                bels.append([Constants.ASL_BEL_PERCEIVED_OBJECT,
                                             obj.replace(" ", Constants.ASL_STRING_SEPARATOR)])
                    if thread == Constants.TOPIC_EMOTION_DETECTION:
                        for em in vision_data_inner[1:]:
                            if not em == DataColletor._KEY_EMOTION_NEUTRAL:
                                bels.append([Constants.ASL_BEL_DETECTED_EMOTION, em])
                    logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, bels)
                """ If the sender is the CHATTER """
                if sender == Constants.CHATTER_JID:

                    logger.info("chatter data: {}".format(msg_body_dict))
                    last_chatter_data = msg_body_dict[max(msg_body_dict.keys())]
                    last_chatter_data_split = utils.splitStringToList(last_chatter_data,
                                                                      Constants.STRING_SEPARATOR_INNER)
                    if thread == Constants.TOPIC_NAME_LEARNT:
                        self.agent.interacting_person = last_chatter_data_split[0].lower()
                        bels.append([Constants.ASL_BEL_PERSON_NAME, self.agent.interacting_person])
                    if thread == Constants.TOPIC_INTERNAL_COMMUNICATIONS:
                        internal_comm = last_chatter_data_split[0].lower()
                        bels.append([Constants.ASL_BEL_INTERNAL, internal_comm])
                    if thread == Constants.TOPIC_SPEECH:
                        last_chatter_data_sentence = last_chatter_data_split[0].replace(" ",
                                                                                        Constants.ASL_STRING_SEPARATOR)
                        last_chatter_data_volume = last_chatter_data_split[1].replace(" ",
                                                                                      Constants.ASL_STRING_SEPARATOR)
                        bels.append(
                            [Constants.ASL_BEL_SAID, last_chatter_data_sentence, float(last_chatter_data_volume)])

                    logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "bels: {}".format(bels))

                if sender == Constants.POSITION_HANDLER_JID:

                    position_data = msg_body_dict[max(msg_body_dict.keys())]
                    bels.append([DataColletor._KEY_DIST_DATA, position_data])


                logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "adding bels " + str(bels) + " to batch")
                await self.agent.addToBatch(self.batch, sender, thread, bels)  # n.b. bels is a list of lists
            else:  # if timeout reached
                # print("Timeout reached")
                # in this case i still add an empty list to the batch so the batch is considered completed
                await self.agent.addToBatch(self.batch, utils.getStringFromJID(self.template.sender),
                                            str(self.template.thread), [])

    class SendMsgToBehaviour(OneShotBehaviour):
        def __init__(self, receiver, content):
            super().__init__()
            self.receiver = receiver
            self.content = content

        async def run(self):
            if self.content is None:
                """ This is the default behavior, which sends the msg to the bdi agent"""
                last_batch_id = self.agent.last_batch_in_data_to_send
                if not last_batch_id is None:
                    if last_batch_id in self.agent.data_to_send.keys():
                        last_batch = self.agent.data_to_send[last_batch_id]
                        msg_body = {**{
                            Constants.SPADE_MSG_BATCH_ID: last_batch_id
                        }, **last_batch}
                        logger.info("data collector: sending to bdi {}".format(str(msg_body)))
                        msg = utils.prepareMessage(self.agent.jid, self.receiver, Constants.PERFORMATIVE_INFORM,
                                                   msg_body)
                        await self.send(msg)

                        # print("deleting all data collected before the batch just sent")
                        for k in list(self.agent.data_to_send.keys()):
                            if float(k) <= float(last_batch_id):
                                del self.agent.data_to_send[k]
            else:
                """ Non-default behavior (e.g., for the norm aapter)"""
                # print("sending data as requested to " + str(self.receiver))
                msg = utils.prepareMessage(self.agent.jid, self.receiver, Constants.PERFORMATIVE_INFORM, self.content)
                # print("sending " + str(msg))
                await self.send(msg)
                # print("it says sent")

    async def send_msg_to(self, receiver, metadata=None, content=None):
        # print("DATACOLLECTOR: Received request from BDI at " + str(time.time()))
        b = self.SendMsgToBehaviour(receiver, content)
        # print("DATACOLLECTOR: Created new sendmsgtoBehavior at " + str(time.time()))
        self.add_behaviour(b)

    async def addToBatch(self, batch, sender, thread, list_of_bel_lists):
        """ This will start constructing beliefs to send to the bdi """

        if not batch in self.work_in_progress_data:
            self.work_in_progress_data[batch] = {}

        sender_thread = sender + "-" + thread
        if not sender_thread in self.work_in_progress_data[batch]:
            self.work_in_progress_data[batch][sender_thread] = []

        self.work_in_progress_data[batch][sender_thread].extend(list_of_bel_lists)

        # if I completed the batch
        if len(self.work_in_progress_data[batch].keys()) == self.required_nr_data_for_batch:
            bels_to_add = {}

            batch_visible_person = self.interacting_person

            data = {}

            # vision
            if Constants.VISION_HANDLER_JID in self.workers_data_sources_threads.keys():
                for thread in self.workers_data_sources_threads[Constants.VISION_HANDLER_JID]:
                    vision_bel_lists = self.work_in_progress_data[batch][Constants.VISION_HANDLER_JID + "-" + thread]
                    for vision_bel_list in vision_bel_lists:
                        if len(vision_bel_list) > 0:
                            logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "vision_bel_list {}".format(vision_bel_list))
                            if vision_bel_list[0] == DataColletor._KEY_DIST_DATA:
                                position_data = vision_bel_list[1]
                                data[Constants.LV_DIST] = position_data
                                logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, data)
                            else:
                                """ the following allows for having multiple beliefs of a kind (e.g., multiple perceived_object beliefs)
                                 It assumes that in the bdicore the key of these beliefs is not used for anything
                                 (the key of beliefs that should be singletone instead is used)"""
                                if vision_bel_list[0] in bels_to_add:
                                    bel_idx = 1
                                    key_bel = vision_bel_list[0] + "_" + str(bel_idx)
                                    while key_bel in bels_to_add:
                                        bel_idx += 1
                                        key_bel = vision_bel_list[0] + "_" + str(bel_idx)
                                    bels_to_add[key_bel] = vision_bel_list
                                else:
                                    bels_to_add[vision_bel_list[0]] = vision_bel_list

            # chatter
            if Constants.CHATTER_JID in self.workers_data_sources_threads.keys():
                for thread in self.workers_data_sources_threads[Constants.CHATTER_JID]:
                    chatter_bel_lists = self.work_in_progress_data[batch][Constants.CHATTER_JID + "-" + thread]
                    for chatter_bel_list in chatter_bel_lists:
                        if len(chatter_bel_list) > 0:
                            logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "chatter bel list {}".format(chatter_bel_list))
                            if chatter_bel_list[0] == Constants.ASL_BEL_PERSON_NAME:
                                batch_visible_person = chatter_bel_list[1]
                                bels_to_add[chatter_bel_list[0]] = chatter_bel_list
                            elif chatter_bel_list[0] == Constants.ASL_BEL_INTERNAL:
                                internal_comm = chatter_bel_list[1]
                                bels_to_add[chatter_bel_list[0]] = [internal_comm]
                            else:
                                chatter_data_sentence = chatter_bel_list[1].lower()
                                chatter_data_human_sentence = chatter_data_sentence.replace(Constants.ASL_STRING_SEPARATOR, " ")
                                chatter_data_volume = chatter_bel_list[2]
                                #TODO I think all the following ifs could be generalized, so that it is possible to add some without changing the data collector
                                if chatter_data_sentence in Constants.POSTURES:
                                    formed_bel = [Constants.ASL_BEL_SAID,
                                                  Constants.POSTURES[chatter_data_sentence],
                                                  Constants.ASL_FLUENT_IS_POSTURE]
                                elif chatter_data_sentence in Constants.ANIMATIONS:
                                    formed_bel = [Constants.ASL_BEL_SAID,
                                                  Constants.ANIMATIONS[chatter_data_sentence],
                                                  Constants.ASL_FLUENT_IS_ANIMAATION]
                                elif len([i for i in Constants.VOCABULARY_BYE_BYE if
                                          i.lower() in chatter_data_human_sentence]) > 0:
                                    formed_bel = [Constants.ASL_BEL_SAID, Constants.ASL_FLUENT_BYE]
                                elif len([i for i in Constants.VOCABULARY_TELL_ROBOT_NAME if
                                          i.lower() in chatter_data_human_sentence]) > 0:
                                    formed_bel = [Constants.ASL_BEL_SAID, Constants.ASL_FLUENT_TELL_ROBOT_NAME]
                                elif len([i for i in Constants.VOCABULARY_WHAT_IS_THIS if
                                          i.lower() == chatter_data_human_sentence]) > 0:  # note here I'm checking if it's equal
                                    formed_bel = [Constants.ASL_BEL_SAID, Constants.ASL_FLUENT_WHAT_YOU_SEE]
                                elif len([i for i in Constants.VOCABULARY_WHAT_USER_SAID if
                                          i.lower() == chatter_data_human_sentence]) > 0:  # same here
                                    formed_bel = [Constants.ASL_BEL_SAID, Constants.ASL_FLUENT_WHAT_USER_SAID]
                                elif len([i for i in Constants.VOCABULARY_WHAT_ROBOT_SAID if
                                          i.lower() == chatter_data_human_sentence]) > 0:  # same here
                                    formed_bel = [Constants.ASL_BEL_SAID, Constants.ASL_FLUENT_WHAT_ROBOT_SAID]
                                else:
                                    formed_bel = [Constants.ASL_BEL_SAID, chatter_data_sentence]
                                bels_to_add[Constants.ASL_BEL_SAID] = formed_bel
                                # here I create the data inputs for the social interpreter.
                                # these inputs are obtained by both the sensors and the analysis of the words and of the context
                                data[Constants.LV_COMMUNICATING] = 1.0
                                data[Constants.LV_VOLUME] = float(chatter_data_volume)
                                if len([i for i in Constants.VOCABULARY_PERSONAL_CONVERSATION if
                                        i in chatter_data_sentence.replace(Constants.ASL_STRING_SEPARATOR, " ")]) > 0:
                                    data[Constants.LV_VOC_PERSONAL] = 1.0

            # position
            if Constants.POSITION_HANDLER_JID in self.workers_data_sources_threads.keys():
                for thread in self.workers_data_sources_threads[Constants.POSITION_HANDLER_JID]:
                    position_bel_lists = self.work_in_progress_data[batch][
                        Constants.POSITION_HANDLER_JID + "-" + thread]
                    for position_bel_list in position_bel_lists:
                        if len(position_bel_list) > 0:
                            position_data = position_bel_list[1]
                            data[Constants.LV_DIST] = position_data

            # alltogether
            social_values = None
            best_social_interpr = None

            nr_info = len(data)
            if (self.fsi is not None) and (nr_info > 0):
                for fsi_input in self.fsi.fuzzyRuleBase.inputs:
                    if not fsi_input in data:
                        logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, str(fsi_input) + " not in data")
                        input_default_val = self.fsi.fuzzyRuleBase.ling_vars_dict[fsi_input].getDefaultVal()
                        input_min_val = self.fsi.fuzzyRuleBase.ling_vars_dict[fsi_input].universe_of_discourse[0]
                        if input_default_val is None:
                            data[fsi_input] = input_min_val
                        else:
                            data[fsi_input] = input_default_val
                logger.info("data: {}".format(str(data)))
                social_values, best_social_interpr = self.fsi.getBestSocialInterpretation(data)
                logger.info("{}, best is {}".format(social_values, best_social_interpr))

            if (not best_social_interpr is None):
                """
                The following test is important: we send data to the norm adapter only if there is more than
                one social cue. Otherwise we are not learning/adapting correctly, but only reinforcing knowledge."""
                if nr_info > 1:
                    msg_to_norm_adapter = {
                        Constants.TOPIC_SOCIAL_INTERPR: str(best_social_interpr)
                    }
                    if not social_values is None:
                        for s in social_values:
                            msg_to_norm_adapter[str(s)] = str(social_values[s])
                    for d in data:
                        msg_to_norm_adapter[str(d)] = str(data[d])
                    send_msg_to_norm_adapter = self.SendMsgToBehaviour(Constants.NORM_ADAPTER_JID, msg_to_norm_adapter)
                    logger.info("DATACOLLECTOR: Created new sendmsgtoBehavior for norm adapter at {}".format(str(time.time())))
                    logger.info("datacollector msg for norm adapter: {}".format(msg_to_norm_adapter))
                    self.add_behaviour(send_msg_to_norm_adapter)

            if (not social_values is None):
                logger.log(Constants.LOGGING_LV_DEBUG_NOSAR, "social_values: {}".format(str(social_values)))
                bels_to_add[Constants.SPADE_MSG_SOCIAL_EVAL] = social_values
                if (not best_social_interpr is None):
                    bels_to_add[Constants.ASL_BEL_DISTANCE] = [Constants.ASL_BEL_DISTANCE,
                                                               str(best_social_interpr).lower()]
                if (not self.interacting_person == Constants.ASL_FLUENT_UNKNOWN_PERSON):
                    bels_to_add[Constants.ASL_BEL_PERSON_NAME] = [Constants.ASL_BEL_PERSON_NAME,
                                                                  str(self.interacting_person).lower()]

            if (len(bels_to_add.keys()) > 0):
                self.data_to_send[batch] = bels_to_add
                self.last_batch_in_data_to_send = batch
                # self.data_to_send.extend(bels_to_add)
                logger.info("Batch {} is {}".format(batch, bels_to_add))

            del self.work_in_progress_data[batch]

    async def setup(self):
        await super().setup()
        self.interacting_person = Constants.ASL_FLUENT_UNKNOWN_PERSON
        self.current_batch = None
        self.work_in_progress_data = {}

        self.data_to_send = {}
        self.last_batch_in_data_to_send = None


        """ This dictionary defines all sources for the data collector"""
        self.workers_data_sources_threads = {Constants.CHATTER_JID: [Constants.TOPIC_NAME_LEARNT,
                                                                     Constants.TOPIC_SPEECH,
                                                                     Constants.TOPIC_INTERNAL_COMMUNICATIONS],
                                             # note I'm using the topics as threads but the names could be different (in some cases, actually, they already are)
                                             Constants.VISION_HANDLER_JID: [Constants.TOPIC_HUMAN_DETECTION,
                                                                            Constants.TOPIC_HEAD_TRACKER,
                                                                            Constants.TOPIC_OBJECT_DETECTION,
                                                                            Constants.TOPIC_EMOTION_DETECTION]
                                             }  # ... here you can add the others, or remove some, eg., Constants.POSITION_HANDLER_JID

        self.required_nr_data_for_batch = 0
        for d in self.workers_data_sources_threads:
            for t in self.workers_data_sources_threads[d]:
                self.required_nr_data_for_batch += 1

        start_at = datetime.now() + timedelta(seconds=1)
        b = self.CollectDataBehaviour(period=0.2, start_at=start_at, data_sources=self.workers_data_sources_threads)
        self.add_behaviour(b)
