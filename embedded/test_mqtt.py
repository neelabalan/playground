#!python3
import paho.mqtt.client as mqtt
import time
import sys

mqtt_broker="192.168.0.100"
mqtt_port=1883

topic="voltage"
def on_connect(client, userdata, flags, rc):
    if rc==0:
        print("connection successful")
        client.subscribe(topic)
    else:
        print("connection refused")

def on_disconnect(client, userdata, rc):
    print("Disconnected from broker")

#def on_subscribe(client, obj, mid, granted_qos):
#    print("Subscribed : "+str(mid) + " " + str(granted_qos))

def on_message(client, userdata, message):
    print("Message received - " + message.payload.decode())
    print(message.topic)

client=mqtt.Client()


client.on_connect=on_connect
client.on_disconnect=on_disconnect
client.subscribe(topic)
client.on_message=on_message

try:
    client.connect(mqtt_broker, mqtt_port)
    print("Connecting to broker", mqtt_broker)
except:
    print("ERROR -  COULD NOT CONNECT")
    sys.exit(1)


client.loop_forever()
