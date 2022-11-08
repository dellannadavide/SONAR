import paho.mqtt.client as mqtt
import utils.constants as Constants

import logging
logger = logging.getLogger("nosar.sar.utils.mqttclient")

class MQTTClient:
    def __init__(self, broker, client_id, client_type, topic, on_message):
        self.mqttBroker = broker
        self.client_id = client_id
        self.client = mqtt.Client(client_id)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client_type = client_type
        self.isRunning = False

        self.client.connect(self.mqttBroker)

        if self.client_type == Constants.MQTT_CLIENT_TYPE_LISTENER:
            self.subscribe(topic)
            self.setOnMessage(on_message)

        self.startLoop()


    def subscribe(self, topic):
        self.client.subscribe(topic)

    def setOnMessage(self, on_message):
        self.client.on_message = on_message

    def startLoop(self):
        self.client.loop_start()
        self.isRunning = True

    def stopLoop(self):
        if self.isRunning:
            self.client.loop_stop()
            self.isRunning = False

    def isRunning(self):
        return self.isRunning

    def publish(self, topic, message):
        self.client.publish(topic, message)

    def disconnect(self):
        self.client.disconnect()

    def on_connect(self, client, userdata, flags, rc):
        logger.info("MQTT Client " + str(self.client_id) + " connecting to " + str(self.mqttBroker) + "...")
        logger.info("Connection returned " + str(rc))

    def on_disconnect(self, client, userdata, flags, rc):
        logger.info("MQTT Client "+str(self.client_id)+" disconnecting form "+str(self.mqttBroker)+"...")
        logger.info("Connection returned " + str(rc))
