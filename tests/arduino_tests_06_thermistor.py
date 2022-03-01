from pyfirmata import Arduino, util, OUTPUT, PWM
import time
from math import log

# initial configuration
board = Arduino("COM4")
thermistor_pin = board.get_pin('a:0:i')

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
		R1 = 50000
		c1, c2, c3 = 1.009249522e-03, 2.378405444e-04, 2.019202697e-07
		Vo = thermistor_pin.read()
		try:
			R2 = R1 * (1 / float(Vo) - 1.0)
		except TypeError:
			continue
		logR2 = log(R2)
		T = 1.0 / (c1 + c2 * logR2 + c3 * logR2 * logR2 * logR2)
		T = T - 273.15
		print("Analog value:", T)
		time.sleep(1)


if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		turnOffAllPins()
		print("========= STOPPED =========")
