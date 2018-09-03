#!/usr/bin/python

from pixel_ring import pixel_ring
import paho.mqtt.client as mqtt
import datetime
import os
import mraa
import time

en = mraa.Gpio(12)
if os.geteuid() != 0 :
    time.sleep(1)
         
en.dir(mraa.DIR_OUT)
en.write(0)

pixel_ring.set_brightness(50)


def time_now():
    return datetime.datetime.now().strftime('%H:%M:%S.%f')

# MQTT client to connect to the bus
mqtt_client = mqtt.Client()


def on_connect(client, userdata, flags, rc):
    # subscribe to all messages
    mqtt_client.subscribe('#')


# Process a message as it arrives
def on_message(client, userdata, msg):
    if msg.topic.find("audioServer") != -1:
        return
    print msg.topic
    if msg.topic.find("hermes/hotword/default/detected") != -1:
        pixel_ring.wakeup()
        return
    if msg.topic.find("hermes/dialogueManager/sessionStarted") != -1:
        pixel_ring.think()
        return
    if msg.topic.find("hermes/dialogueManager/sessionEnded") != -1:
        pixel_ring.off()
        return

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect('localhost', 1883)
mqtt_client.loop_forever()

hermes/hotword/default/detected
hermes/asr/stopListening
hermes/hotword/toggleOff
hermes/dialogueManager/sessionStarted
hermes/asr/startListening
hermes/asr/textCaptured
hermes/asr/stopListening
hermes/nlu/query
hermes/nlu/intentParsed
hermes/intent/searchWeatherForecast
hermes/dialogueManager/sessionEnded
hermes/asr/stopListening
hermes/hotword/toggleOn
