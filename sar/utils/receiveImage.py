import time

from utils.mqttclient import MQTTClient
import utils.constants as Constants
import PIL.Image as Image


def on_message(client, userdata, message):
    # print("received message: ", str(message.payload.decode("utf-8")))
    # data = message.split(str=";")
    # imageWidth = int(data[0])
    # imageHeight = int(data[1])
    # image_string = data[2]
    im = Image.frombytes("RGB", (640, 480), message.payload)
    im.show()

if __name__ == "__main__":
    mqtt_listener = MQTTClient(Constants.MQTT_BROKER_ADDRESS, "NAO_ImageReader", Constants.MQTT_CLIENT_TYPE_LISTENER, Constants.TOPIC_IMAGE, on_message)
    while True:
        time.sleep(1)