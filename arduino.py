try:
	from pyfirmata import Arduino, util
	import paho.mqtt.client as mqtt
except ImportError:
	import pip
	pip.main(['install', 'pyfirmata', 'paho-mqtt'])

# Imports
from pyfirmata import Arduino, util
from math import log
import time
import paho.mqtt.client as mqtt

# Setup
board = Arduino("COM4")

# start the utilization service
iterator = util.Iterator(board)
iterator.start()

# Define pins
thermistor_pin = board.get_pin('a:0:i')  # define THERMISTOR pin as Analog Input Pin 1
ldr_pin = board.get_pin('a:1:i')  # define LDR pin as Analog Input Pin 0
button_a_pin = board.get_pin('d:9:i')  # define BUTTON pin as Digital Input Pin 9
button_b_pin = board.get_pin('d:8:i')  # define BUTTON pin as Digital Input Pin 8
led_pin = board.get_pin('d:12:o')  # define LED pin as Digital Output Pin 12
alarm_led_pin = board.get_pin('d:7:o')  # define ALARM LED pin as Digital Output Pin 7


def check_tempurature_difference(thermistor_value):
	global previous_tempurature
	tempurature_difference = 0
	current_tempurature = 25
	if not thermistor_value:
		return tempurature_difference, current_tempurature
	# Get temperature
	VR2 = thermistor_value
	R1 = 10000
	T0 = 25 + 273.15
	R2 = R1 * (1 / VR2 - 1)
	logR2 = log(R2 / 1000)
	TK = 1 / ((logR2 / 3455) + (1 / T0))
	TC = TK - 273.15
	# Find tempurature difference
	current_tempurature = TC
	if not previous_tempurature:
		previous_tempurature = current_tempurature
		return tempurature_difference, current_tempurature
	tempurature_difference = abs(previous_tempurature - current_tempurature)
	previous_tempurature = current_tempurature
	return tempurature_difference, current_tempurature


def check_light_intensity_difference(ldr_value):
	global previous_light_intensity
	light_intensity_difference = 0
	current_light_intensity = 0
	if not ldr_value:
		return light_intensity_difference, current_light_intensity
	# Find light intensity difference
	current_light_intensity = ldr_value
	if not previous_light_intensity:
		previous_light_intensity = current_light_intensity
		return light_intensity_difference, current_light_intensity
	light_intensity_difference = abs(previous_light_intensity - current_light_intensity)
	previous_light_intensity = current_light_intensity
	return light_intensity_difference, current_light_intensity


def record_secret(button_value, button_x):
	global secret_sequence
	x = button_x
	current_time = time.time() + (3600 * 5.5)
	if button_value:
		if secret_sequence.get("button_" + x).get("start") == 0:
			secret_sequence["button_" + x]["start"] = current_time
			secret_sequence["button_" + x]["previous_timestamp"] = current_time
			secret_sequence["button_" + x]["previous_value"] = button_value
		else:
			if secret_sequence.get("button_" + x).get("previous_value") != button_value:
				secret_sequence["button_" + x]["previous_timestamp"] = current_time
				secret_sequence["button_" + x]["previous_value"] = button_value
	else:
		if secret_sequence.get("button_" + x).get("start") == 0:
			return
		else:
			if secret_sequence.get("button_" + x).get("previous_value") == button_value:
				if current_time - secret_sequence.get("button_" + x).get("previous_timestamp") > 5:
					secret_sequence["button_" + x]["end"] = current_time
			else:
				if current_time - secret_sequence.get("button_" + x).get("previous_timestamp") < 1:
					secret_sequence["button_" + x]["secret"] = secret_sequence.get("button_" + x).get("secret") + "."
					secret_sequence["button_" + x]["previous_timestamp"] = current_time
					secret_sequence["button_" + x]["previous_value"] = button_value
				else:
					secret_sequence["button_" + x]["secret"] = secret_sequence.get("button_" + x).get("secret") + "_"
					secret_sequence["button_" + x]["previous_timestamp"] = current_time
					secret_sequence["button_" + x]["previous_value"] = button_value


def match_secrets(button_a_value, button_b_value):
	global access
	if not access:
		if not secret_sequence.get("button_a").get("end"):
			record_secret(button_a_value, "a")
		if not secret_sequence.get("button_b").get("end"):
			record_secret(button_b_value, "b")
		if secret_sequence.get("button_a").get("end") and secret_sequence.get("button_b").get("end"):
			if not secret_sequence.get("start_time_difference"):
				secret_sequence["start_time_difference"] = secret_sequence.get("button_a").get("start") - secret_sequence.get("button_b").get("start")
				if secret_sequence.get("start_time_difference") == 0.0:
					secret_sequence["start_time_difference"] = 1
			if not secret_sequence.get("end_time_difference"):
				secret_sequence["end_time_difference"] = secret_sequence.get("button_a").get("end") - secret_sequence.get("button_b").get("end")
				if secret_sequence.get("end_time_difference") == 0.0:
					secret_sequence["end_time_difference"] = 1
			if secret_sequence.get("start_time_difference") and secret_sequence.get("end_time_difference"):
				if secret_sequence.get("start_time_difference") < 5 and secret_sequence.get("end_time_difference") < 5:
					if secret_sequence.get("button_a").get("secret") == ".._" and secret_sequence.get("button_a").get("secret") == "_..":
						access = "granted"
					else:
						access = "denied"
						secret_sequence["wrong_attempts"] = secret_sequence.get("wrong_attempts") + 1
				else:
					access = "denied"
					secret_sequence["wrong_attempts"] = secret_sequence.get("wrong_attempts") + 1
		else:
			if access == "granted":
				print("ACCESS GRANTED")
			elif access == "denied":
				print("ACCESS DENIED")


def main():
	global secret_sequence, access
	print("========= REPORTING STARTED =========")
	print(f"======== {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time() + (3600 * 5.5)))} ========")
	print("=" * 37)
	while True:
		currentTime = time.time() + (3600 * 5.5)
		print(f"======== {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(currentTime))} ========")
		# Read values from sensors
		tempurature_difference, current_tempurature = check_tempurature_difference(thermistor_pin.read())
		light_intensity_difference, current_light_intensity = check_light_intensity_difference(ldr_pin.read())
		match_secrets(button_a_pin.read(), button_b_pin.read())


if __name__ == "__main__":
	access = ""
	previous_tempurature = 0
	previous_light_intensity = 0
	previous_timestamp = 0
	secret_sequence = {
		"button_a": {
			"previous_value": 0,
			"previous_timestamp": 0,
			"start": 0,
			"end": 0,
			"secret": ""
		},
		"button_b": {
			"previous_value": 0,
			"previous_timestamp": 0,
			"start": 0,
			"end": 0,
			"secret": ""
		},
		"start_time_difference": 0,
		"end_time_difference": 0,
		"wrong_attempts": 0
	}
	try:
		main()
	except KeyboardInterrupt:
		print("========= REPORTING STOPPED =========")
