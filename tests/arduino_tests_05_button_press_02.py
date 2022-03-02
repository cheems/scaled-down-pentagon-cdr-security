try:
	from pyfirmata import Arduino, util
	import paho.mqtt.client as mqtt
except ImportError:
	import pip
	pip.main(['install', 'pyfirmata', 'paho-mqtt'])

# Imports
from pyfirmata import Arduino, util
import time

# Setup
board = Arduino("COM4")

# start the utilization service
iterator = util.Iterator(board)
iterator.start()

button_a_pin = board.get_pin('d:9:i')  # define BUTTON pin as Digital Input Pin 9
button_b_pin = board.get_pin('d:8:i')  # define BUTTON pin as Digital Input Pin 8


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
	print(f"BUTTON_{x.upper()}_VALUE:", button_value)


def main():
	global secret_sequence, access
	print("========= REPORTING STARTED =========")
	print(f"======== {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time() + (3600 * 5.5)))} ========")
	print("=" * 37)
	while True:
		currentTime = time.time() + (3600 * 5.5)
		print(f"======== {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(currentTime))} ========")
		# Read values from sensors
		button_a_value = button_a_pin.read()
		button_b_value = button_b_pin.read()
		if not access:
			if not secret_sequence.get("button_a").get("end"):
				record_secret(button_a_value, "a")
			if not secret_sequence.get("button_b").get("end"):
				record_secret(button_b_value, "b")
			if secret_sequence.get("button_a").get("end") and secret_sequence.get("button_b").get("end"):
				if not secret_sequence.get("start_time_difference"):
					secret_sequence["start_time_difference"] = secret_sequence.get("button_a").get("start") - secret_sequence.get("button_b").get("start")
					if secret_sequence.get("start_time_difference") == 0.0:
						secret_sequence["start_time_difference"] = 0.1
				if not secret_sequence.get("end_time_difference"):
					secret_sequence["end_time_difference"] = secret_sequence.get("button_a").get("end") - secret_sequence.get("button_b").get("end")
					if secret_sequence.get("end_time_difference") == 0.0:
						secret_sequence["end_time_difference"] = 0.1
			if secret_sequence.get("start_time_difference") and secret_sequence.get("end_time_difference"):
				if secret_sequence.get("start_time_difference") < 5 and secret_sequence.get("end_time_difference") < 5:
					access = "granted"
				else:
					access = "denied"
				secret_sequence["wrong_attempts"] = secret_sequence.get("wrong_attempts") + 1
			print("SECRET_A:", secret_sequence.get("button_a").get("secret"))
			print("SECRET_B:", secret_sequence.get("button_b").get("secret"))
			print("START_A:", secret_sequence.get("button_a").get("start"))
			print("START_B:", secret_sequence.get("button_b").get("start"))
			print("END_A:", secret_sequence.get("button_a").get("end"))
			print("END_B:", secret_sequence.get("button_b").get("end"))
			print("START_DIFFERENCE:", secret_sequence.get("start_time_difference"))
			print("END_DIFFERENCE:", secret_sequence.get("end_time_difference"))
		else:
			if access == "granted":
				print("ACCESS GRANTED")
			elif access == "denied":
				print("ACCESS DENIED")


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
if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		print("========= REPORTING STOPPED =========")
