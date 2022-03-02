# GP 106 Project
# Central Control Centre
# Group ES-38/02

# Morse Code Time Intervals
# '.' - 0.25s (0.1s-0.4s)
# '_' - 0.75s (0.6s-0.9s)
# '4' -(pause between two letters) (0.6s-0.9s)
# Considering the practical errors that can happen when reading the Torch ON/OFF intervals these were taken as ranges instead of the exact value

# import modules from Pyfirmata
from pyfirmata import Arduino, util, INPUT, OUTPUT

# import inbuilt time module
import time

# Variables for time measurements
t1 = 0
t2 = 0
t3 = 0
t4 = 0
list1 = []  # Create empty list for storing morse code
list_morse = ['.', '-', '4', '-', '-', '.',
              '.']  # Requierd morse code to unlock(AZ)('4' means seperation between two letters)

add = True
add2 = False
add3 = True
add4 = True

# initial configurations
board = Arduino("COM6")
ldr_pin = 0  # ldr connected to A0
thermo_pin = 1  # thermistor connected to A1
led_pin_1 = 13  # LED to indicate unlock(Digital  pin 13)
led_pin_2 = 12  # LED to indicate abnormal room temperatures(Digital  pin 12)
led_pin_3 = 11  # LED to indicate wrong morse code(Digital  pin 11)
led_pin_4 = 10  # LED to indicate clearing of the list after pressing push button(Digital  pin 10)

push_button = 2

# configure input and output modes
board.analog[ldr_pin].mode = INPUT
board.analog[thermo_pin].mode = INPUT
board.digital[push_button].mode = INPUT
board.digital[led_pin_1].mode = OUTPUT
board.digital[led_pin_2].mode = OUTPUT
board.digital[led_pin_3].mode = OUTPUT
board.digital[led_pin_4].mode = OUTPUT

# start the utilization service
it = util.Iterator(board)
it.start()

board.analog[ldr_pin].enable_reporting()
board.analog[thermo_pin].enable_reporting()

t = time.time()

while True:

	# clear the morse code that stored in the list1
	if board.digital[push_button].read() == 1:
		board.digital[led_pin_4].write(0)
	else:
		board.digital[led_pin_4].write(1)  # ON LED 3
		list1 = []  # clear list1

	# read values from ldr and thermistor
	ldr_val = board.analog[ldr_pin].read()
	thermo_val = board.analog[thermo_pin].read()

	if ldr_val == None:  # To skip initial 'None' readings from the sensors
		continue
	if thermo_val == None:
		continue

	print('LDR value :', ldr_val, 'thermo Value :', thermo_val, board.digital[push_button].read())

	# check room temperature
	if thermo_val < 0.079:

		board.digital[led_pin_2].write(1)  # switch on LED2
	else:
		board.digital[led_pin_2].write(0)

	# morse code reading

	if ldr_val <= 0.3:
		if add3 == True:
			t3 = time.time()
			add3 = False
		if time.time() - t3 > 7:
			add3 = True

			list1 = []

		if add == True:
			t1 = time.time()
			add = False
			add2 = True
			if t1 - t2 > 0.4 and t1 - t2 < 0.9:
				list1.append('4')
			if len(list1) >= 7:
				if list1 == list_morse:
					list1 = []  # clear list1

					if add4 == True:
						board.digital[led_pin_1].write(
							1)  # ON LED1 to indicate morse is correct, if above conditions true
						t4 = int(time.time())  # count time to switch off LED1 after 5s
						add4 = False



				else:
					list1 = []  # clear list1
					if add4 == True:
						board.digital[led_pin_3].write(1)  # ON LED3 to indicate morse code is wrong
						t4 = int(time.time())  # count time to switch off LED3 after 5s
						add4 = False

	if ldr_val > 0.3:
		if add2 == True:
			t2 = time.time()  # record the time when light is off

			add = True
			add2 = False
			if t2 - t1 < 0.4 and t2 - t1 > 0.1:
				list1.append('.')

			if t2 - t1 > 0.4 and t2 - t1 < 0.9:
				list1.append('-')
			if len(list1) >= 7:
				if list1 == list_morse:
					list1 = []
					if add4 == True:
						t4 = int(time.time())
						board.digital[led_pin_1].write(1)
						add4 = False



				else:
					list1 = []
					if add4 == True:
						t4 = int(time.time())
						board.digital[led_pin_3].write(1)
						add4 = False

	# Switch off LED1 and LED3 after 5s and clear list1(need to wait for 5s before entering the code again)
	if int(time.time()) - t4 == 5:
		add4 = True
		list1 = []
		board.digital[led_pin_1].write(0)
		board.digital[led_pin_3].write(0)

	print(list1)















