from pyfirmata import Arduino , OUTPUT
import time

# create an Arduino board instance
board = Arduino("COM4")
# digital pin number
led_pin = 13

# set it as an output pin
board.digital[led_pin].mode = OUTPUT

# blink the LED
while True:
	print("blink!")
	board.digital[led_pin].write(1)
	time.sleep(1)
	board.digital[led_pin].write(0)
	time.sleep(1)
