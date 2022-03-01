from pyfirmata import Arduino , OUTPUT
import time

# create an Arduino board instance
board = Arduino("COM4")
# digital pin number
led_pin_1 = 13
led_pin_2 = 7

# set pins as output pins
board.digital[led_pin_1].mode = OUTPUT
board.digital[led_pin_2].mode = OUTPUT

# blink LEDs
while True:
	print("blink!")
	board.digital[led_pin_1].write(1)
	board.digital[led_pin_2].write(1)
	time.sleep(1)
	board.digital[led_pin_1].write(0)
	board.digital[led_pin_2].write(0)
	time.sleep(1)
