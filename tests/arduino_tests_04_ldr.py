from pyfirmata import Arduino, util, INPUT, PWM
import time

# initial configuration
board = Arduino("COM4")
ldr_pin = 0
led_pin = 11
board.analog[ldr_pin].mode = INPUT
board.digital[led_pin].mode = PWM

# start the utilization service
it = util.Iterator(board)
it.start()
board.analog[ldr_pin].enable_reporting()


def turnOffAllPins():
	board.digital[led_pin].write(0 / 10.0)
	print("\nALL PINS WERE TURNED OFF")


def main():
	while True:
		print("READ VALUE")
		ldr_val = board.analog[ldr_pin].read()
		print("Analog value:", ldr_val)
		# if ldr_val:
		# 	board.digital[led_pin].write(ldr_val-0.3)
		if ldr_val:
			if ldr_val > 0.7:
				board.digital[led_pin].write(5 / 10.0)
			else:
				board.digital[led_pin].write(0 / 10.0)


if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		turnOffAllPins()
