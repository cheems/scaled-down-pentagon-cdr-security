from pyfirmata import Arduino, PWM
import time

# create an Arduino board instance
board = Arduino("COM4")
# digital pin number
led_pin = 11

# set it as an output pin
board.digital[led_pin].mode = PWM


def turnOffAllPins():
	board.digital[led_pin].write(0)
	print("ALL PINS WERE TURNED OFF")


def main():
	while True:
		# fade in
		print("FADE IN")
		for i in range(10):
			board.digital[led_pin].write(i / 10.0)
			time.sleep(0.3)
		# fade in
		print("FADE OUT")
		for i in range(10):
			board.digital[led_pin].write(1 - i / 10.0)
			time.sleep(0.3)


if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		turnOffAllPins()
