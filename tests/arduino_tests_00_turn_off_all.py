from pyfirmata import Arduino , OUTPUT
import time

# create an Arduino board instance
board = Arduino("COM4")
# digital pin number
led_pin_1 = 13

# set pins as output pins
board.digital[led_pin_1].mode = OUTPUT

# blink LEDs
while True:
	print("All TURNED OFF!")
	board.digital[led_pin_1].write(0)
	break
