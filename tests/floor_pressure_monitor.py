# Title: Floor Pressure Monitoring for Security Breaches
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
button_p_a_pin = board.get_pin('d:5:i')     # Define pressure button as digital output pin 5
led_g_pin = board.get_pin('d:12:o')         # Define green LED pin as digital output pin 12
alarm_led_pin = board.get_pin('d:10:o')     # Define alarm(red) LED pin as digital output pin 10
alarm_buzz_pin = board.get_pin('d:2:o')     # Define alarm buzzer pin as digital output pin 2

# Define variables, most are declared with dummy values
pressure_increased = 0                      # Pressure difference identification status
lockdown = 0                                # Lockdown status
alarm_timestamp = 0                         # Last time that the alarm was triggered
alarm = 0                                   # Value to be written on the alarm pins


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
	global lockdown, pressure_increased
	print("==== REPORTING STARTED ====")
	while True:
		# Handle LEDs and buzzer depending on lockdown status
		lights()
		if button_p_a_pin.read():
			# If the push button placed to detect floor pressure difference is pushed, turn system into a lockdown
			# and mark that pressure difference is detected
			pressure_increased = 1
			lockdown = 1
		# Send obtained values to server for further actions.
		# (Since here it is in the basic level, it just prints values)
		print("FLOOR PRESSURE DIFFERENCE\t\t:\t", pressure_increased)
		print("LOCKDOWN\t\t\t\t\t\t:\t", bool(lockdown))


# This boilerplate is used here to turn off all indicators when stopping the program manually
if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		led_g_pin.write(0)
		alarm_led_pin.write(0)
		alarm_buzz_pin.write(0)
