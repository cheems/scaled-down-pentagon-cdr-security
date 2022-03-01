from pyfirmata import Arduino, util, OUTPUT
import time

# initial configuration
board = Arduino("COM4")
button_pin = board.get_pin('d:2:i')

# start the utilization service
it = util.Iterator(board)
it.start()


def turnOffAllPins():
	for i in range(2, 13):
		board.digital[i].mode = OUTPUT
		board.digital[i].write(0)
	print("\nALL PINS WERE TURNED OFF")


def main():
	while True:
		print("READ VALUE")
		button_val = button_pin.read()
		print("Analog value:", button_val)


if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		turnOffAllPins()
		print("========= STOPPED =========")
