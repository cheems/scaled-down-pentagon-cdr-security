# Imports
try:
	from pyfirmata import Arduino, util
	import paho.mqtt.client as mqtt
except ImportError:
	import pip
	pip.main(['install', 'pyfirmata', 'paho-mqtt'])
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
thermistor_pin = board.get_pin('a:0:i')  # define THERMISTOR pin as Analog Input Pin 0
ldr_pin = board.get_pin('a:1:i')  # define LDR pin as Analog Input Pin 1
button_a_pin = board.get_pin('d:9:i')  # define BUTTON A pin as Digital Input Pin 9
button_b_pin = board.get_pin('d:8:i')  # define BUTTON B pin as Digital Input Pin 8
button_p_a_pin = board.get_pin('d:5:i')  # define PRESSURE BUTTON pin as Digital Input Pin 6
led_g_pin = board.get_pin('d:12:o')  # define LED pin as Digital Output Pin 12
led_o_pin = board.get_pin('d:11:o')
alarm_led_pin = board.get_pin('d:10:o')  # define ALARM LED pin as Digital Output Pin 6
alarm_buzz_pin = board.get_pin('d:2:o')


def check_temperature_difference(thermistor_value):
	global previous_temperature, temperature_difference, temperature_difference_refresh_time, start_time
	if not temperature_difference_refresh_time:
		temperature_difference_refresh_time = time.time() + (3600 * 5.5)
	else:
		if abs(start_time - (time.time() + (3600 * 5.5))) < 3:
			temperature_difference = 0
		if abs(temperature_difference_refresh_time - (time.time() + (3600 * 5.5))) > 10:
			temperature_difference = 0
			temperature_difference_refresh_time = time.time() + (3600 * 5.5)
	current_temperature = 25
	if not thermistor_value:
		return temperature_difference, current_temperature
	# Get temperature
	VR2 = thermistor_value
	R1 = 10000
	T0 = 25 + 273.15
	R2 = R1 * (1 / VR2 - 1)
	try:
		logR2 = log(R2 / 1000)
	except ValueError:
		return temperature_difference, current_temperature
	TK = 1 / ((logR2 / 3455) + (1 / T0))
	TC = TK - 273.15
	# Find temperature difference
	current_temperature = TC
	if not previous_temperature:
		previous_temperature = current_temperature
		return temperature_difference, current_temperature
	if previous_temperature != current_temperature:
		if temperature_difference < abs(previous_temperature - current_temperature):
			temperature_difference = abs(previous_temperature - current_temperature)
	previous_temperature = current_temperature
	return temperature_difference, current_temperature


def check_light_intensity_difference(ldr_value):
	global previous_light_intensity, light_intensity_difference, start_time
	current_light_intensity = 0
	if not ldr_value:
		return light_intensity_difference, current_light_intensity
	# Find light intensity difference
	current_light_intensity = ldr_value / 1.023 * 100
	# If it is still been less than three seconds from the time program started working, make the light intensity difference 0
	# Usually the LDR shows very high differences during first few seconds. Doing this can avoid invalid fluctuations
	if abs(start_time - (time.time() + (3600 * 5.5))) < 3:
		light_intensity_difference = 0
	# Return followings with the last recorded values
	if not previous_light_intensity:
		previous_light_intensity = current_light_intensity
		return light_intensity_difference, current_light_intensity
	if previous_light_intensity != current_light_intensity:
		if light_intensity_difference < abs(previous_light_intensity - current_light_intensity):
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
	global access, access_level, access_level_secrets, secret_sequence, led_o_pin
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
				secret_entered = secret_sequence.get("button_a").get("secret") + secret_sequence.get("button_b").get("secret")
				if secret_entered == access_level_secrets.get("confidential"):
					access = "granted"
					access_level = "confidential"
				elif secret_entered == access_level_secrets.get("secret"):
					access = "granted"
					access_level = "secret"
				elif secret_entered == access_level_secrets.get("top_secret"):
					access = "granted"
					access_level = "top_secret"
				else:
					access = ""
					secret_sequence["wrong_attempts"] = secret_sequence.get("wrong_attempts") + 1
					incorrect_secret_alert("start")
					secret_sequence = {
						"button_a": {"previous_value": 0, "previous_timestamp": 0, "start": 0, "end": 0, "secret": ""},
						"button_b": {"previous_value": 0, "previous_timestamp": 0, "start": 0, "end": 0, "secret": ""},
						"start_time_difference": 0,
						"end_time_difference": 0,
						"wrong_attempts": secret_sequence.get("wrong_attempts")
					}
			else:
				access = ""
				secret_sequence["wrong_attempts"] = secret_sequence.get("wrong_attempts") + 1
				secret_sequence["button_a"]["secret"], secret_sequence["button_b"]["secret"] = "", ""
				incorrect_secret_alert("start")
				secret_sequence = {
					"button_a": {"previous_value": 0, "previous_timestamp": 0, "start": 0, "end": 0, "secret": ""},
					"button_b": {"previous_value": 0, "previous_timestamp": 0, "start": 0, "end": 0, "secret": ""},
					"start_time_difference": 0,
					"end_time_difference": 0,
					"wrong_attempts": secret_sequence.get("wrong_attempts")
				}


def incorrect_secret_alert(action):
	global incorrect_secret_timestamp, incorrect_secret, alert, led_o_pin
	if action == "start":
		incorrect_secret_timestamp = time.time() + (3600 * 5.5)
		alert = 1
		led_o_pin.write(alert)
		alarm_buzz_pin.write(alert)
	else:
		if alert:
			if abs(incorrect_secret_timestamp - (time.time() + (3600 * 5.5))) > 1:
				incorrect_secret_timestamp = time.time() + (3600 * 5.5)
				alert = 0
				led_o_pin.write(alert)
				alarm_buzz_pin.write(alert)
				incorrect_secret_timestamp = 0


def lights():
	global secret_sequence, lockdown, led_g_pin, alarm_timestamp, alarm_led_pin, alarm, alarm_buzz_pin
	if not lockdown:
		led_g_pin.write(1)
	else:
		led_g_pin.write(0)
		if not alarm_timestamp:
			alarm_timestamp = time.time() + (3600 * 5.5)
			alarm = 1
			alarm_led_pin.write(alarm)
			alarm_buzz_pin.write(alarm)
		else:
			if alarm:
				if abs(alarm_timestamp - (time.time() + (3600 * 5.5))) > 1:
					alarm_timestamp = time.time() + (3600 * 5.5)
					alarm = 0
					alarm_led_pin.write(alarm)
					alarm_buzz_pin.write(alarm)
			else:
				if abs(alarm_timestamp - (time.time() + (3600 * 5.5))) > 0.2:
					alarm_timestamp = time.time() + (3600 * 5.5)
					alarm = 1
					alarm_led_pin.write(alarm)
					alarm_buzz_pin.write(alarm)


def main():
	global secret_sequence, access, access_level, lockdown, pressure_increased,\
		thermistor_pin, ldr_pin, button_a_pin, button_b_pin, button_p_a_pin
	print("=================== REPORTING STARTED ===================")
	print(f"================== {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time() + (3600 * 5.5)))} ==================")
	print("=" * 57)
	while True:
		currentTime = time.time() + (3600 * 5.5)
		if abs(int(time.time()) - time.time()) >= 0.9:
			print(f"================== {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(currentTime))} ==================")
		# Read values from sensors
		lights()
		incorrect_secret_alert("stop")
		if not access:
			temperature_difference_, current_temperature = check_temperature_difference(thermistor_pin.read())
			light_intensity_difference_, current_light_intensity = check_light_intensity_difference(ldr_pin.read())
			match_secrets(button_a_pin.read(), button_b_pin.read())
			if button_p_a_pin.read():
				pressure_increased = 1
				lockdown = 1
			# if temperature_difference_ > 3 and lockdown == 0:
			# 	lockdown = 1
			if light_intensity_difference_ > 12 and lockdown == 0:
				lockdown = 1
			if not secret_sequence.get("wrong_attempts") < 3:
				lockdown = 1

			if abs(int(time.time()) - time.time()) >= 0.9:  # Prints data once a 0.5 secs or more
				print("TEMPERATURE\t\t\t\t\t\t:\t", current_temperature)
				print("MAX TEMPERATURE DIFFERENCE\t\t:\t", temperature_difference_)
				print("LIGHT INTENSITY\t\t\t\t\t:\t", current_light_intensity, "%")
				print("MAX LIGHT INTENSITY DIFFERENCE\t:\t", light_intensity_difference_, "%")
				print("FLOOR PRESSURE DIFFERENCE\t\t:\t", pressure_increased)
				print("=" * 57)
				print(secret_sequence.get("button_a").get("secret"), secret_sequence.get("button_b").get("secret"))
				print("UNSUCCESSFULL ENTRY ATTEMPTS\t:\t", secret_sequence.get("wrong_attempts"))
				print("LOCKDOWN\t\t\t\t\t\t:\t", bool(lockdown))
		if access:
			if abs(int(time.time()) - time.time()) >= 0.9:  # Prints data once a 0.5 secs or more
				print("ACCESS LEVEL\t\t\t\t\t:\t", " ".join(access_level.upper().split("_")))
				print("UNSUCCESSFULL ENTRY ATTEMPTS\t:\t", secret_sequence.get("wrong_attempts"))
				print("LOCKDOWN\t\t\t\t\t\t:\t", bool(lockdown))


start_time = time.time() + (3600 * 5.5)
previous_temperature = 0
temperature_difference = 0
temperature_difference_refresh_time = 0
previous_light_intensity = 0
light_intensity_difference = 0
pressure_increased = 0
alarm_timestamp = 0
alarm = 0
incorrect_secret_timestamp = 0
incorrect_secret = 0
alert = 0
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

access = ""
access_level = ""
access_level_secrets = {
	"confidential": ".._.._",  # .._ | .._
	"secret": "._.._.",  # ._. | ._.
	"top_secret": ".___..___."  # .___. | .___.
}
lockdown = 0

if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		led_g_pin.write(0)
		led_o_pin.write(0)
		alarm_led_pin.write(0)
		alarm_buzz_pin.write(0)
		print("=================== REPORTING STOPPED ===================")
		print(f"================== {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time() + (3600 * 5.5)))} ==================")
