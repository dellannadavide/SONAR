import sys
import time

import matplotlib as mpl

from mas.mas import MAS
from mas.mas_baseline import MAS_BASELINE

mpl.use('TkAgg')

import utils.constants as Constants

from datetime import datetime
import logging

""" This main module starts SONAR"""

if __name__ == '__main__':

    agent_type = "parrot_agent"
    # agent_type = "baseline_agent"
    agent_type = "sonar_agent"

    # exp_id = "jeec1"
    exp_id = "dda"

    now = datetime.now()
    exec_timestamp = str(now.strftime("%Y%m%d%H%M%S"))
    log_folder = "./log/"
    log_path_name = log_folder + exp_id + "_sonar_" + agent_type + "_" + exec_timestamp + ".log"

    logging.addLevelName(Constants.LOGGING_LV_DEBUG_NOSAR, Constants.LOGGING_LV_DEBUG_NOSAR_NAME)

    logging.basicConfig(level=Constants.LOGGING_LV_DEBUG_NOSAR_NAME,
                        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
                        handlers=[
                            logging.FileHandler(log_path_name, mode="a+"),
                            logging.StreamHandler(sys.stdout)
                        ],
                        )

    logger = logging.getLogger("nosar")

    logger.info("Starting agent")
    workers_to_start = [
        Constants.SYSTEM_HANDLER_NAME,
        # Constants.NORM_ADAPTER_NAME,
        Constants.CHATTER_NAME,
        # Constants.POSITION_HANDLER_NAME, #to be ignored since replaced by the vision
        Constants.VISION_HANDLER_NAME,
        Constants.POSTURE_HANDLER_NAME,
        Constants.DATA_COLLECTOR_NAME
    ]

    if agent_type == "parrot_agent":
        logger.warning("IMPORTANT!!! Using the parrotagent")
        a = MAS_BASELINE(Constants.BDI_CORE_JID, Constants.BDI_CORE_PWD,
                         asl_file="mas/basic_showcase_parrot.asl", workers_to_start=workers_to_start)
    if agent_type == "baseline_agent":
        logger.warning("IMPORTANT!!! Using the baseline agent")
        a = MAS_BASELINE(Constants.BDI_CORE_JID, Constants.BDI_CORE_PWD,
                         asl_file="mas/basic_minimal_baseline.asl", workers_to_start=workers_to_start)
    if agent_type == "sonar_agent":
        logger.warning("IMPORTANT!!! Using the social and norm aware agent")
        a = MAS(Constants.BDI_CORE_JID, Constants.BDI_CORE_PWD,
                asl_file="mas/basic2.asl", workers_to_start=workers_to_start)

    future = a.start()
    future.result()
    logger.info("Startup ended")

    while not a.my_behav.is_killed():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
    a.stop()
