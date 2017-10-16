#!/usr/bin/env python3
import joystick
import time
import sys

ESC = chr(27)
RED   = ESC + "[31m"
GREEN = ESC + "[32m"
RESET = ESC + "[39m"

def write(x,y, message):
	if(isinstance(message, int)):
		if(message):
			message = GREEN + "True" + RESET
		else:
			message = RED + "False" + RESET
	sys.stdout.write("\x1b[{};{}H\x1b[K{}".format(x,y,message))


def main():
	js = joystick.WiiUProController(joystick.getAController())

	print("\x1b[?47h\x1b[2J\x1b[HA:")
	print("B:")
	print("X:")
	print("Y:")
	print()
	print("L:")
	print("R:")
	print("ZL:")
	print("ZR:")
	print()
	print("Up:")
	print("Down:")
	print("Left:")
	print("Right:")
	print()
	print("Left X:")
	print("Left Y:")
	print("Left B:")
	print()
	print("Right X:")
	print("Right Y:")
	print("Right B:")

	while(True):
		js.poll()
		write(1,4,js.A.isDown())
		write(2,4,js.B.isDown())
		write(3,4,js.X.isDown())
		write(4,4,js.Y.isDown())

		write(6,4,js.L.isDown())
		write(7,4,js.R.isDown())
		write(8,5,js.ZL.isDown())
		write(9,5,js.ZR.isDown())

		write(11,8,js.Up.isDown())
		write(12,8,js.Down.isDown())
		write(13,8,js.Left.isDown())
		write(14,8,js.Right.isDown())

		write(16,9,js.LeftStick.getX())
		write(17,9,js.LeftStick.getY())
		write(18,9,js.LeftStick.Button.isDown())

		write(20,10,js.RightStick.getX())
		write(21,10,js.RightStick.getY())
		write(22,10,js.RightStick.Button.isDown())

		sys.stdout.flush()

if(__name__ == "__main__"):
	try:
		main()
	except KeyboardInterrupt:
		sys.stdout.write("\x1b[?47l")
		sys.stdout.flush()
