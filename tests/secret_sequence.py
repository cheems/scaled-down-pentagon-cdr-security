# Title: Secret Entry Sequence
# for Unusual Activities
# Developed by Group 40-A for GP106 Project - The Pentagon
# Written according to PEP8 guidelines
# Repo can be found here: https://github.com/cheems/scaled-down-pentagon-cdr-security/

# Imports
try:
	from pyfirmata import Arduino, util
	import paho.mqtt.client as mqtt
except ImportError:
	import pip
	pip.main(['install', 'pyfirmata'])
from pyfirmata import Arduino, util
import time

# Setup
board = Arduino("COM4")

# start the utilization service
iterator = util.Iterator(board)
iterator.start()

# Define pins
button_a_pin = board.get_pin('d:9:i')       # define secret entry button A pin as digital input pin 9
button_b_pin = board.get_pin('d:8:i')       # define secret entry button B pin as digital input pin 8
led_g_pin = board.get_pin('d:12:o')         # Define green LED pin as digital output pin 12
led_o_pin = board.get_pin('d:11:o')         # Define orange LED pin as digital output pin 11
alarm_led_pin = board.get_pin('d:10:o')     # Define alarm(red) LED pin as digital output pin 10
alarm_buzz_pin = board.get_pin('d:2:o')     # Define alarm buzzer pin as digital output pin 2

# Define variables, most are declared with dummy values
lockdown = 0                                    # Lockdown status
alarm_timestamp = 0                             # Last time that the alarm was triggered
alarm = 0                                       # Value to be written on the alarm pins
incorrect_secret_timestamp = 0                  # Last time that an invalid secret entered
alert = 0                                       # Value to be written on the incorrect secret alert
access = ""                                     # Access status
access_level = ""                               # Access level
access_level_secrets = {                        # Secrets for different access levels
	"confidential": ".._.._",  # .._ | .._
	"secret": "._.._.",  # ._. | ._.
	"top_secret": ".___..___."  # .___. | .___.
}
secret_sequence = {                             # Data relevent to the secret entry buttons
	"button_a": {                               # Data collected using secret entry button A
		"previous_value": 0,                    # Button value that was recorded before a certain time period
		"previous_timestamp": 0,                # Time that button status was changed for the last time
		"start": 0,                             # Time that secret was started being entered
		"end": 0,                               # Time that secret was ended being entered
		"secret": ""                            # Entered secret using button A
	},
	"button_b": {                               # Data collected using secret entry button B
		"previous_value": 0,                    # Button value that was recorded before a certain time period
		"previous_timestamp": 0,                # Time that button status was changed for the last time
		"start": 0,                             # Time that secret was started being entered
		"end": 0,                               # Time that secret was ended being entered
		"secret": ""                            # Entered secret using button B
	},
	"start_time_difference": 0,                 # Time difference betweem secrert entering started times of two buttons
	"end_time_difference": 0,                   # Time difference betweem secrert entering ended times of two buttons
	"wrong_attempts": 0                         # Unseccessful attempts
}


# this function checks if secrets are being entered and records if secrets are being entered.
def record_secret(button_value, button_x):
	# Taking variables from the outer scope
	global secret_sequence
	x = button_x        # Button letter
	# Record the current time
	current_time = time.time() + (3600 * 5.5)
	if button_value:
		if secret_sequence.get("button_" + x).get("start") == 0:
			# If button is pressed and start time is still 0, that means this is the first time secret entry button is pressed
			# Record the time that secret entry key is pressed for the first time
			# Current button value and time are recorded to use later
			secret_sequence["button_" + x]["start"] = current_time
			secret_sequence["button_" + x]["previous_timestamp"] = current_time
			secret_sequence["button_" + x]["previous_value"] = button_value
		else:
			# If button is pressed but start time is 1, this means this is not the first time secret entry button is pressed
			# that means secret entry is being entered at the moment
			if secret_sequence.get("button_" + x).get("previous_value") != button_value:
				# If the current button value is not the same as previous that means button status has been changed
				# Current button value and time are recorded to use later
				secret_sequence["button_" + x]["previous_timestamp"] = current_time
				secret_sequence["button_" + x]["previous_value"] = button_value
	else:
		if secret_sequence.get("button_" + x).get("start") == 0:
			# If the button is not pressed and the start time is still 0, do nothing. Return None
			return
		else:
			# If button is not pressed but start time is 1, this means the secret sequence is started to be entered
			# and at this moment no button is pressed. So it is need to identify if the sequence is finished entring
			if secret_sequence.get("button_" + x).get("previous_value") == button_value:
				if current_time - secret_sequence.get("button_" + x).get("previous_timestamp") > 5:
					# If the button status has not been changed for more than last 5 seconds,
					# Consider that secret sequence is finished entering and record the end time.
					secret_sequence["button_" + x]["end"] = current_time
			else:
				if current_time - secret_sequence.get("button_" + x).get("previous_timestamp") < 1:
					# If the button status has been changed from previous value which is 1(pressed) before one second elapsed,
					# this means the entered value is a dot "."
					secret_sequence["button_" + x]["secret"] = secret_sequence.get("button_" + x).get("secret") + "."
					secret_sequence["button_" + x]["previous_timestamp"] = current_time
					secret_sequence["button_" + x]["previous_value"] = button_value
				else:
					# If the button status has been changed from previous value which is 1(pressed) after one second elapsed,
					# this means the entered value is a underscore "_"
					secret_sequence["button_" + x]["secret"] = secret_sequence.get("button_" + x).get("secret") + "_"
					secret_sequence["button_" + x]["previous_timestamp"] = current_time
					secret_sequence["button_" + x]["previous_value"] = button_value


# this function checks if secrets recorded are found in predefined secret sequences
def match_secrets(button_a_value, button_b_value):
	# Taking variables from the outer scope
	global access, access_level, access_level_secrets, secret_sequence, led_o_pin
	if not secret_sequence.get("button_a").get("end"):
		# If secret sequence entered by button a is't finished entering (end time is not available), record the secret entry
		record_secret(button_a_value, "a")
	if not secret_sequence.get("button_b").get("end"):
		# If secret sequence entered by button b is't finished entering (end time is not available), record the secret entry
		record_secret(button_b_value, "b")
	if secret_sequence.get("button_a").get("end") and secret_sequence.get("button_b").get("end"):
		# If secret sequences from both buttons are recorded
		if not secret_sequence.get("start_time_difference"):
			# started time difference between two buttons is calculated
			secret_sequence["start_time_difference"] = secret_sequence.get("button_a").get("start") - secret_sequence.get("button_b").get("start")
			if secret_sequence.get("start_time_difference") == 0.0:
				# if started time difference between two buttons is 0, make it 1. (Failsafe value)
				secret_sequence["start_time_difference"] = 1
		if not secret_sequence.get("end_time_difference"):
			# end time difference between two buttons is calculated
			secret_sequence["end_time_difference"] = secret_sequence.get("button_a").get("end") - secret_sequence.get("button_b").get("end")
			if secret_sequence.get("end_time_difference") == 0.0:
				# if end time difference between two buttons is 0, make it 1. (Failsafe value)
				secret_sequence["end_time_difference"] = 1
		if secret_sequence.get("start_time_difference") and secret_sequence.get("end_time_difference"):
			if secret_sequence.get("start_time_difference") < 5 and secret_sequence.get("end_time_difference") < 5:
				# if start time difference and end time difference, both are less than 5 seconds,
				# then it can be assumed sequence was entered in the expected way - no suspicious activity
				secret_entered = secret_sequence.get("button_a").get("secret") + secret_sequence.get("button_b").get("secret")
				# Secrets got from two buttons are concatenated and match with the pre defined secrets
				if secret_entered == access_level_secrets.get("confidential"):
					# if entered secret is matched with the confidential level predefined secret
					# grand access to the room and mark the access level as confidential to assign relevant permissions
					access = "granted"
					access_level = "confidential"
				elif secret_entered == access_level_secrets.get("secret"):
					# if entered secret is matched with the Secret level predefined secret
					# grand access to the room and mark the access level as secret to assign relevant permissions
					access = "granted"
					access_level = "secret"
				elif secret_entered == access_level_secrets.get("top_secret"):
					# if entered secret is matched with the top secret level predefined secret
					# grand access to the room and mark the access level as top secret to assign relevant permissions
					access = "granted"
					access_level = "top_secret"
				else:
					# if entered secret isn't matched with any predefined secret
					# deny access to the room and send an alert using orange LED to inform that entered secret sequence is invalid
					# Consider this as a unsuccessful attempt and record it
					# Values recorded should be emptied because it is need to accept another attempt if all three attempts are not used
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
				# if start time difference and end time difference, both are equal to or more than 5 seconds,
				# then it can be assumed sequence was entered suspicious.
				# Consider this as a unsuccessful attempt and record it
				# Values recorded should be emptied because it is need to accept another attempt if all three attempts are not used
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


# This function handles LEDs and the buzzer on incorrect entries
# This function doesn't use time.sleep() and
# instead, it counts time using a subtractive method that lets the code to excecute the rest without waiting
def incorrect_secret_alert(action):
	# Taking variables from the outer scope
	global incorrect_secret_timestamp, alert, led_o_pin
	if action == "start":
		# if an alert should be sent,
		# Record current time and store it as the last time that an invalid secret entered
		# and turn on the orange LED and the buzzer
		incorrect_secret_timestamp = time.time() + (3600 * 5.5)
		alert = 1                       # Set write value to 1
		led_o_pin.write(alert)          # Turn on orange LED
		alarm_buzz_pin.write(alert)     # Turn on buzzer
	else:
		if alert:
			# If alert is 1, then that means orange LED is turned on. If it is
			# and it's been ome second elapsed from the time that led and buzzer is turned on,
			# Turn of them
			if abs(incorrect_secret_timestamp - (time.time() + (3600 * 5.5))) > 1:
				incorrect_secret_timestamp = time.time() + (3600 * 5.5)
				alert = 0                           # Set write value to 0
				led_o_pin.write(alert)              # Turn on orange LED
				alarm_buzz_pin.write(alert)         # Turn on buzzer
				incorrect_secret_timestamp = 0      # Set this to 0 for the next time


# This function handles LEDs and the buzzer depending on lockdown status
# This function doesn't use time.sleep() and
# instead, it counts time using a subtractive method that lets the code to excecute the rest without waiting
def lights():
	# Taking variables from the outer scope
	global lockdown, led_g_pin, alarm_timestamp, alarm_led_pin, alarm, alarm_buzz_pin
	if not lockdown:
		# If lockdown isn't triggered
		# Keep Green LED turn on
		led_g_pin.write(1)
	else:
		# Else (If lockdown is triggered), turn off Green LED
		led_g_pin.write(0)
		if not alarm_timestamp:
			# If lockdown is triggered and if alarm_timestamp has the dummy value "0", that means this is not used before
			# Record current time, This is used as the last time that alarm was triggered
			alarm_timestamp = time.time() + (3600 * 5.5)
			alarm = 1                       # Set write value to 1
			alarm_led_pin.write(alarm)      # Turn on alarm(red) LED
			alarm_buzz_pin.write(alarm)     # Turn on buzzer
		else:
			# Else (If lockdown is triggered and if alarm_timestamp is used before)
			if alarm:
				# and value of alarm is not 0, that means alarm is working at this moment
				if abs(alarm_timestamp - (time.time() + (3600 * 5.5))) > 1:
					# If 1 second is elapsed since the alarm is started
					# Use current time as the last triggered time
					alarm_timestamp = time.time() + (3600 * 5.5)
					alarm = 0                       # Set alarm value to 0
					alarm_led_pin.write(alarm)      # Turn off alarm LED
					alarm_buzz_pin.write(alarm)     # Turn off buzzer
			else:
				# If alarm timestamp is used before but value of alarm is 0, that means alarm is triggered but in silent status
				if abs(alarm_timestamp - (time.time() + (3600 * 5.5))) > 0.2:
					# If 0.2 seconds are elapsed since alarm turn into silent position
					# Use current time as the last triggered time
					alarm_timestamp = time.time() + (3600 * 5.5)
					alarm = 1                       # Set alarm value to 1
					alarm_led_pin.write(alarm)      # Turn off alarm LED
					alarm_buzz_pin.write(alarm)     # Turn off buzzer


# This function is the main activity
def main():
	# Taking variables from the outer scope
	global lockdown, secret_sequence, access, access_level, button_a_pin, button_b_pin
	print("==== REPORTING STARTED ====")
	while True:
		# Handle LEDs and buzzer depending on lockdown status
		lights()
		# Stop incorrect secret alert if it's been one second from the time alert was sent
		incorrect_secret_alert("stop")
		if not access:
			# If access is still not given,
			# Match secrets entered with predefined ones
			match_secrets(button_a_pin.read(), button_b_pin.read())
			if not secret_sequence.get("wrong_attempts") < 3:
				# If unseccessful entry attempts are higere than 3 times, turn the system into a lockdown
				lockdown = 1
			# Send obtained values to server for further actions.
			# (Since here it is in the basic level, it just prints values)
			# This prints data once a 0.5 secs or more without using time.sleep() and this lets the code to excecute the rest without waiting
			if abs(int(time.time()) - time.time()) >= 0.9:
				print(secret_sequence.get("button_a").get("secret"), secret_sequence.get("button_b").get("secret"))
				print("UNSUCCESSFULL ENTRY ATTEMPTS\t:\t", secret_sequence.get("wrong_attempts"))
				print("LOCKDOWN\t\t\t\t\t\t:\t", bool(lockdown))
		else:
			# If access is given,
			# Send obtained values to server for further actions.
			# (Since here it is in the basic level, it just prints values)
			# This prints data once a 0.5 secs or more without using time.sleep() and this lets the code to excecute the rest without waiting
			if abs(int(time.time()) - time.time()) >= 0.9:  # Prints data once a 0.5 secs or more
				print("ACCESS LEVEL\t\t\t\t\t:\t", " ".join(access_level.upper().split("_")))
				print("UNSUCCESSFULL ENTRY ATTEMPTS\t:\t", secret_sequence.get("wrong_attempts"))
				print("LOCKDOWN\t\t\t\t\t\t:\t", bool(lockdown))


# This boilerplate is used here to turn off all indicators when stopping the program manually
if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		led_g_pin.write(0)
		led_o_pin.write(0)
		alarm_led_pin.write(0)
		alarm_buzz_pin.write(0)
