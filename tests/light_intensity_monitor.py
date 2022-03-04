# Title: Light Intensity Monitoring for Unusual Activities
# Developed by Group 40-A for GP106 Project - The Pentagon
# Written according to PEP8 guidelines
# Repo can be found here: https://github.com/cheems/scaled-down-pentagon-cdr-security/

# Imports
try:
	from pyfirmata import Arduino, util
except ImportError:
	import pip
	pip.main(['install', 'pyfirmata'])
from pyfirmata import Arduino, util
import time

# Setup
board = Arduino("COM4")

# Start the utilization service
iterator = util.Iterator(board)
iterator.start()

# Define pins
ldr_pin = board.get_pin('a:1:i')            # Define LDR pin as analog input pin 1
led_g_pin = board.get_pin('d:12:o')         # Define green LED pin as digital output pin 12
alarm_led_pin = board.get_pin('d:10:o')     # Define alarm(red) LED pin as digital output pin 10
alarm_buzz_pin = board.get_pin('d:2:o')     # Define alarm buzzer pin as digital output pin 2

# Define variables, most are declared with dummy values
previous_light_intensity = 0                # Light intensity percentage that was before a certain time period
light_intensity_difference = 0              # Maximum light intensity difference recorded
start_time = time.time() + (3600 * 5.5)     # Time which program is started running
lockdown = 0                                # Lockdown status
alarm_timestamp = 0                         # Last time that the alarm was triggered
alarm = 0                                   # Value to be written on the alarm pins


# this function checks for light intensity differences occure in a certain time period
def check_light_intensity_difference(ldr_value):
	# Taking variables from the outer scope
	global previous_light_intensity, light_intensity_difference, start_time
	current_light_intensity = 0     # Record the current light intensity. This is a dummy value
	if not ldr_value:
		# If the value got from the LDR is not valid (None type) {this happens in the first few miliseconds}
		# Return followings with the last recorded values
		return light_intensity_difference, current_light_intensity
	# =============================
	# Calculate current light intensity
	current_light_intensity = ldr_value / 1.023 * 100       # Current light intensiy as a percentage
	# If it is still been less than three seconds from the time program started working, make the light intensity difference 0
	# Usually the LDR shows very high differences during first few seconds. Doing this can avoid invalid fluctuations
	if abs(start_time - (time.time() + (3600 * 5.5))) < 3:
		light_intensity_difference = 0
		# Return followings with the last recorded values
		return light_intensity_difference, current_light_intensity
	if not previous_light_intensity:
		# If this has the dummy value "0"
		# Record current light intensity. This will be used as the last recorded light intensity
		previous_light_intensity = current_light_intensity
		# Return followings with the last recorded values
		return light_intensity_difference, current_light_intensity
	# Since we need the maximum light intensity difference in a time period, 0 as the difference would be useless
	# Therefore, light intensity difference is recorded only if the current light intensity is different from the previous light intensity percentage recorded
	# and the difference between them is larger than the previously recorded maximum light intensity difference.
	if previous_light_intensity != current_light_intensity:
		if light_intensity_difference < abs(previous_light_intensity - current_light_intensity):
			light_intensity_difference = abs(previous_light_intensity - current_light_intensity)
	# Record current light intensity. This will be used as the last recorded light intensity
	previous_light_intensity = current_light_intensity
	# Return followings with the last recorded values
	return light_intensity_difference, current_light_intensity


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
	global ldr_pin, lockdown
	print("==== REPORTING STARTED ====")
	while True:
		# Handle LEDs and buzzer depending on lockdown status
		lights()
		# Get maximum light intensity difference and current light intensity percentage using check_temperature_difference()
		light_intensity_difference_, current_light_intensity = check_light_intensity_difference(ldr_pin.read())
		if light_intensity_difference_ > 10 and lockdown == 0:
			# If maximum light intensity difference detected is larger than 12%, turn system into a lockdown
			lockdown = 1
		# Send obtained values to server for further actions.
		# (Since here it is in the basic level, it just prints values)
		print("LIGHT INTENSITY\t\t\t\t\t:\t", current_light_intensity, "%")
		print("MAX LIGHT INTENSITY DIFFERENCE\t:\t", light_intensity_difference_, "%")
		print("LOCKDOWN\t\t\t\t\t\t:\t", bool(lockdown))


# This boilerplate is used here to turn off all indicators when stopping the program manually
if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		led_g_pin.write(0)
		alarm_led_pin.write(0)
		alarm_buzz_pin.write(0)
