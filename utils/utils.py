import sys

from spade.message import Message
import utils.constants as Constants
import json

import logging
logger = logging.getLogger("sonar.mas.utils.utils")

""" A utility module. It contains some global utility functions"""

def prepareMessage(sender_jid, received_jid, performative, msg_body, thread=None, metadata=None):
    """
    Utility function used by the agents to communicate in the MAS. THe function prepares a Message instance.
    In particular, it constructs the metadata of the message from the input given as parameters and
    creates, if it is not, a json to use as msg_body
    :param sender_jid:
    :param received_jid:
    :param performative: a FIPA performative
    :param msg_body: the content of the body
    :param thread: a thread identifying the type of message
    :param metadata: the metadata, used to filter the message
    :return: an isntance of Message
    """
    """ 

    """
    msg = Message(received_jid)  # Instantiate the message
    msg.set_metadata("performative", performative)  # Set the "inform" FIPA performative
    if not metadata is None:
        if len(metadata)>0:
            for k, v in metadata.items():
                msg.set_metadata(k, v)

    if not isinstance(msg_body, dict):
        logger.critical("ERROR IN THE PREPARATION OF MESSAGE FROM {} TO {} with content {}".format(sender_jid, received_jid, msg_body))
        sys.exit()
    else:
        msg.body = json.dumps(msg_body)

    # if isinstance(msg_body, str):
    #     msg.body = msg_body
    # elif isinstance(msg_body, list):
    #     msg.body = joinStrings(msg_body)

    if not thread is None:
        msg.thread = thread

    return msg

def readMessage(json_msg_body, msg_metadata):
    """ returns the dictionary from the json"""
    if Constants.SPADE_MSG_METADATA_KEYS_TYPE in msg_metadata:
        if msg_metadata[Constants.SPADE_MSG_METADATA_KEYS_TYPE]=="int":
            return json.loads(json_msg_body, object_hook=jsonKeys2int)
        if msg_metadata[Constants.SPADE_MSG_METADATA_KEYS_TYPE]=="float":
            return json.loads(json_msg_body, object_hook=jsonKeys2float)
    return json.loads(json_msg_body)

def jsonKeys2int(x):
    if isinstance(x, dict):
        return {int(k): v for k, v in x.items()}
    return x

def jsonKeys2float(x):
    if isinstance(x, dict):
        return {float(k): v for k, v in x.items()}
    return x


def splitStringToList(str_to_split, separator=None):
    if separator is None:
        return str_to_split.split(Constants.STRING_SEPARATOR)
    else:
        return str_to_split.split(separator)


def joinStrings(list_to_join, separator=None):
    if separator is None:
        return Constants.STRING_SEPARATOR.join(list_to_join)
    else:
        return separator.join(list_to_join)


def splitStringBelToList(str_to_split):
    return str_to_split.split(Constants.BEL_STRING_SEPARATOR)


def joinStringsBel(list_to_join):
    return Constants.BEL_STRING_SEPARATOR.join(list_to_join)


def getStringFromJID(JID):
    return JID.localpart + "@" + JID.domain
