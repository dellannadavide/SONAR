from datetime import datetime
import logging

now = datetime.now()
exec_timestamp = str(now.strftime("%Y%m%d%H%M%S"))
log_folder = "../log/"
log_path_name = log_folder+"nosar_"+exec_timestamp+".log"


logging.basicConfig(level=logging.DEBUG,
format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s',
      filename=log_path_name,
      filemode='a+')

logger = logging.getLogger("mainfile")

loggerinner = logging.getLogger("mainfile.inner")

logger.debug("main debug")
logging.debug("Debug message")
loggerinner.debug("inner debug")
#
# logging.info("Informative message")
#
# logging.error("Error message")