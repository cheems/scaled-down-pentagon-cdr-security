# Title: Temperature Monitoring for Fire Detection
# Developed by Group 40-A for GP106 Project - The Pentagon
# Written was done according to PEP8 guidelines
# Repo can be found here: https://github.com/cheems/scaled-down-pentagon-cdr-security/

# Imports
try:
	from pyfirmata import Arduino, util
except ImportError:
	import pip
	pip.main(['install', 'pyfirmata'])
from pyfirmata import Arduino, util
from math import log
import time

# Setup
board = Arduino("COM4")

# Start the utilization service
iterator = util.Iterator(board)
iterator.start()

# Define pins
thermistor_pin = board.get_pin('a:0:i')     # Define thermistor pin as analog input pin 0
led_g_pin = board.get_pin('d:12:o')         # Define green LED pin as digital output pin 12
alarm_led_pin = board.get_pin('d:10:o')     # Define alarm(red) LED pin as digital output pin 10
alarm_buzz_pin = board.get_pin('d:2:o')     # Define alarm buzzer pin as digital output pin 10

# Variables, Most are declared with dummy values
start_time = time.time() + (3600 * 5.5)     # Time which program is started running
previous_temperature = 0                    # Temperature value that was before a certain time period
temperature_difference = 0                  # Maximum temperature difference recorded
temperature_difference_refresh_time = 0     # Used to refresh maximum temperature difference once a certain time period
lockdown = 0                                # Lockdown status
alarm_timestamp = 0                         # Last time that alarm was triggered
alarm = 0                                   # Value to be written on the alarm pins


# this function checks for temperature fluctuations occure in a time period
def check_temperature_difference(thermistor_value):
	# Taking variables from the outer scope
	global previous_temperature, temperature_difference,\
		temperature_difference_refresh_time, start_time
	if not temperature_difference_refresh_time:             # If this has the dummy value "0"
		# Record current time, This is used as the last refreshed time
		temperature_difference_refresh_time = time.time() + (3600 * 5.5)
	else:
		# If it is still been less than three seconds from the time program started working, make the temperature difference 0
		# Usually the thermistor shows very high fluctuations during first few seconds. Doing this can avoid invalid fluctuations
		if abs(start_time - (time.time() + (3600 * 5.5))) < 3:
			temperature_difference = 0
		# If it's been more than 10 seconds from the time temperature difference was refreshed, refresh the maximum tempurature difference
		# and record the curren time as the last refreshed time
		if abs(temperature_difference_refresh_time - (time.time() + (3600 * 5.5))) > 10:
			temperature_difference = 0
			temperature_difference_refresh_time = time.time() + (3600 * 5.5)
	current_temperature = 25        # Record the current temperature. This is a dummy value
	if not thermistor_value:
		# If the value got from thermistor is not valid (None type) {this happens in the first few miliseconds}
		# Return followings with the last recorded values
		return temperature_difference, current_temperature
	# =============================
	# Calculate current temperature
	VR2 = thermistor_value      # Potential drop across the
	R1 = 10000                  # Known resistance of through hole resistor
	T0 = 25 + 273.15            # Room temperature in Kelvin
	R2 = R1 * (1 / VR2 - 1)     # Resistance provided by thermistor
	try:
		logR2 = log(R2 / 1000)
	except ValueError:
		# If it gets ValueError, return followings with the last recorded values
		return temperature_difference, current_temperature
	TK = 1 / ((logR2 / 3455) + (1 / T0))    # Current temperature in Kelvin
	TC = TK - 273.15                        # Current temperature in Celsius degrees
	# ===========================
	# Find temperature difference
	current_temperature = TC        # Record current temperature
	if not previous_temperature:
		# If this has the dummy value "0"
		# Record current temperature. This will be used as the last recorded tempurature
		previous_temperature = current_temperature
		# Return followings with the last recorded values
		return temperature_difference, current_temperature
	# Since we need the maximum tempurature difference in a time period, 0 as the difference would be useless
	# Therefore, tempurature difference is recorded only if the current temperature is different from previous tempurature recorded
	# and the difference between them is larger than the previously recorded maximum temperature difference.
	if previous_temperature != current_temperature:
		if temperature_difference < abs(previous_temperature - current_temperature):
			temperature_difference = abs(previous_temperature - current_temperature)
	# Record current temperature. This will be used as the last recorded tempurature
	previous_temperature = current_temperature
	# Return followings with the last recorded values
	return temperature_difference, current_temperature


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
	global thermistor_pin, lockdown
	print("==== REPORTING STARTED ====")
	while True:
		# Hancle LEDs and buzzer depending on lockdown status
		lights()
		# Get maximum temperature difference and current temperature value using check_temperature_difference()
		temperature_difference_, current_temperature = check_temperature_difference(thermistor_pin.read())
		if temperature_difference_ > 5 and lockdown == 0:
			# If maximum temperature difference detected is larger than 5 celsius degrees, turn system into a lockdown
			lockdown = 1
		# Send obtained values to server for further actions.
		# (Since here it is in the basic level, it just prints values)
		print("TEMPERATURE\t\t\t\t\t\t:\t", current_temperature)
		print("MAX TEMPERATURE DIFFERENCE\t\t:\t", temperature_difference_)
		print("LOCKDOWN\t\t\t\t\t\t:\t", bool(lockdown))


# This boilerplate is used here to turn off all indicatorswhen stopping the program manually
if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		led_g_pin.write(0)
		alarm_led_pin.write(0)
		alarm_buzz_pin.write(0)
