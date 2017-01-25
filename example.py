#!/usr/bin/env python3
import joystick
import time

print(joystick.getDevices())

js = joystick.joystick(joystick.getAController())
while True:
	js.poll() #Grab to the most recent values
	print(chr(27) + "[2J" + chr(27) + "[H") #Clear the screen
	print("LX: " + str(js.getLeftX()))
	print("LY: " + str(js.getLeftY()))
	print("RX: " + str(js.getRightX()))
	print("RY: " + str(js.getRightY()))

	print("")
	print("Left Stick Button:  " + str(js.getLeftStickButton()))
	print("Right Stick Button: " + str(js.getRightStickButton()))

	print("")
	print("A: " + str(js.getA()))
	print("B: " + str(js.getB()))
	print("X: " + str(js.getX()))
	print("Y: " + str(js.getY()))

	print("")
	print("Up:    " + str(js.getUp()))
	print("Down:  " + str(js.getDown()))
	print("Left:  " + str(js.getLeft()))
	print("Right: " + str(js.getRight()))

	print("")
	print("Start:  " + str(js.getStart()))
	print("Select: " + str(js.getSelect()))
	print("Home:   " + str(js.getHome()))

	print("")
	print("Left Bumper:   " + str(js.getLeftBumper()))
	print("Right Bumper:  " + str(js.getRightBumper()))
	print("Left Trigger:  " + str(js.getLeftTrigger()))
	print("Right Trigger: " + str(js.getRightTrigger()))

	print("")
	print(js.getName())
	time.sleep(.1)
