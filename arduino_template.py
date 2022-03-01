try:
	from pyfirmata import Arduino, util
	import paho.mqtt.client as mqtt
except:
	import pip
	pip.main(['install', 'pyfirmata', 'paho-mqtt'])
	from pyfirmata import Arduino, util

# Imports
import time
import paho.mqtt.client as mqtt

# Setup
group = "G1A"
topic = "G1A/CDR/DATA"
board = Arduino('/dev/tty.usbmodem14201')
mqttBroker = "vpn.ce.pdn.ac.lk"  # Must be connected to the vpn
mqttPort = 8883


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
	print("Connected with result code " + str(rc))
	# Subscribing in on_connect() means that if we lose the connection and
	# reconnect then subscriptions will be renewed.
	client.subscribe(topic)


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
	print(msg.topic + " " + str(msg.payload))


client = mqtt.Client(group)  # Group 1A (Classified Document Room)

try:
	client.connect(mqttBroker, mqttPort)
	client.on_connect = on_connect
	client.on_message = on_message
	client.loop_start()
except:
	print("Connection to MQTT broker failed!")
	exit(1)

iterator = util.Iterator(board)
iterator.start()

ldr_pin = board.get_pin('a:0:i')  # define LDR pin as Analog Input Pin 0
led_pin = board.get_pin('d:12:o')  # define LED pin as Digital Output Pin 12
button_pin = board.get_pin('d:9:i')  # define BUTTON pin as Digital Input Pin 9
alarm_led_pin = board.get_pin('d:7:o')  # define ALARM LED pin as Digital Output Pin 7

# Loop
while True:
	led_pin.write(1)  # turn on LED
	time.sleep(0.1)
	led_pin.write(0)  # turn off LED
	time.sleep(0.1)

	light_intensity = ldr_pin.read()  # read Analog value of LDR
	button_value = button_pin.read()  # read Digital value of Button State

	if button_value:  # button is pressed
		alarm_led_pin.write(1)  # turn on alarm LED
		time.sleep(0.05)
	else:
		alarm_led_pin.write(0)

	data = [str(light_intensity), str(button_value)]  # array of data
	data = ','.join(data)  # join array of data as a single comma seperated string

	client.publish(topic, data)  # publish the data to MQTT broker using the topic
	print('Sent from Arduino ', data)
