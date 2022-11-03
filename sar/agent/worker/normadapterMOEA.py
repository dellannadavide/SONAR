import copy

from spade.behaviour import PeriodicBehaviour, OneShotBehaviour

from sar.agent.workeragent import WorkerAgent
from simpful import *

from utils import utils
import utils.constants as Constants

from datetime import timedelta, datetime



class NormAdapterMOEA(WorkerAgent):

    class AdaptNorms(PeriodicBehaviour):
        def __init__(self, period, start_at):
            super().__init__(period, start_at)
            self.timeout_data_source = period

        async def run(self):
            if (not self.agent.adapting) and (len(self.agent.collected_knowledge)>self.agent.min_nr_datapoints_for_adaptation):
                print("Adapting the rules in all fuzzy rule bases...")
                print("collected knowledge")
                data = copy.deepcopy(self.agent.collected_knowledge)
                # print(self.agent.collected_knowledge)
                b = self.agent.PerformAdaptation(data)
                self.agent.add_behaviour(b)

    class PerformAdaptation(OneShotBehaviour):
        def __init__(self, data):
            super().__init__()
            self.data = data

        async def run(self):
            self.agent.adapting = True
            # first the fuzzy social interpreter
            self.agent.fsi.adapt(self.data, self.agent.optim_param)
            # then all the fsq
            for fsq in self.agent.fsq:
                self.agent.fsq[fsq].adapt(self.data, self.agent.optim_param)
            # self.agent.collected_knowledge = []
            print("Adaptation completed.")
            self.agent.adapting = False

    async def setup(self):
        await super().setup()
        self.collected_knowledge = []
        self.min_nr_datapoints_for_adaptation = 5
        self.optim_param = {
            "algo": Constants.NSGA3,
            "scale": False,
            "core-pos": True,
            "core-width": True,
            "support-width": True,
            "gp": False
        }
        nr_var_descriptors = 0
        if self.optim_param["scale"]:
            nr_var_descriptors += 5
        if self.optim_param["core-pos"]:
            nr_var_descriptors += 2
        if self.optim_param["core-width"]:
            nr_var_descriptors += 2
        if self.optim_param["support-width"]:
            nr_var_descriptors += 2
        if self.optim_param["gp"]:
            nr_var_descriptors += 3
        self.optim_param["nr_param_per_var"] = nr_var_descriptors

        self.adapting = False

        start_at = datetime.now() + timedelta(seconds=5)
        b = self.AdaptNorms(period=6, start_at=start_at)
        self.add_behaviour(b)


    async def do_work(self, work_info):
        print("!!!!!!!!!!!!!!!!!!!!! TO MAKE SURE THAT THE DICTIONARY WORK_INFO IS READ PROPERLY !!!!!!!!!!!!!!!!!!!!!!!")

        """ work_info is the message from the data collector with all the info
        it is a string which represents a list, where element 0 is the topic of element 1, and element 2 is the topic of element 2, etc."""
        work_info_list = utils.splitStringToList(work_info)
        nr_pairs = int(len(work_info_list)/2) #n.b. it is expected to be always even
        data_point = {}
        done = 0
        for i in range(nr_pairs):
            topic = work_info_list[done+i]
            value = work_info_list[done+i+1]

            if not topic==Constants.TOPIC_SOCIAL_INTERPR:
                value = float(value)

            data_point[topic] = value
            done = done+1

        self.collected_knowledge.append(data_point)




