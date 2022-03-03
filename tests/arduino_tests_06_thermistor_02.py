from pyfirmata import Arduino, util, OUTPUT
import time
from math import log

# initial configuration
board = Arduino("COM4")
thermistor_pin = board.get_pin('a:0:i')

# start the utilization service
it = util.Iterator(board)
it.start()


def main():
	print("========= STARTED =========")
	while True:
		R1 = 10000
		T0 = 25 + 273.15
		VR2 = thermistor_pin.read()
		try:
			R2 = R1 * (1 / VR2 - 1)
		except TypeError:
			continue
		logR2 = log(R2 / 1000)
		TK = 1 / ((logR2 / 3455) + (1 / T0))
		Tc = TK - 273.15
		print("Temp value:", Tc)
		time.sleep(1)


if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		print("========= STOPPED =========")
