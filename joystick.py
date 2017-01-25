#!/usr/bin/env python3
import threading, struct, time

SUPPORTED_CONTROLLERS = ["Nintendo Wii Remote Pro Controller", "Logitech Gamepad F310"]
EVENT_FORMAT = "llHHI"
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)
DEBUG_MODE = False
MAX = 4294967296

class joystick():
	def __init__(self, path, layout = None): #Layout will be used to specify a button mapping rather than the button names (eg, Nintendo ABXY or Xbox ABXY)
		self.name = getDeviceName(path[11:])
		self._buffer = { "B":False, "A":False, "X":False, "Y":False, "LeftBumper":False, "RightBumper":False, "LeftTrigger":0.0, "RightTrigger":0.0, "Select":False, "Start":False, "Home":False, "LeftStickButton":False, "RightStickButton":False, "Up":False, "Down":False, "Left":False, "Right":False, "LeftX":0, "LeftY":0, "RightX":0, "RightY":0}
		if(self.name == "Nintendo Wii Remote Pro Controller"):
			self.joystickMax = 1024
			self.ABSwitch = True
		else:
			self.joystickMax = 32768
			self.ABSwitch = False
		self.triggerMax = 255
		self._pressed = {}
		self.inputFile = open(path, "rb")
		self.updateThread = threading.Thread(target=self._read, daemon=True)
		self.updateThread.start()
	def poll(self):
		self._pressed = self._buffer
	def getA(self):
		return self._pressed["A"]
	def getB(self):
		return self._pressed["B"]
	def getX(self):
		return self._pressed["X"]
	def getY(self):
		return self._pressed["Y"]
	def getUp(self):
		return self._pressed["Up"]
	def getDown(self):
		return self._pressed["Down"]
	def getLeft(self):
		return self._pressed["Left"]
	def getRight(self):
		return self._pressed["Right"]
	def getSelect(self):
		return self._pressed["Select"]
	def getHome(self):
		return self._pressed["Home"]
	def getStart(self):
		return self._pressed["Start"]
	def getLeftTrigger(self):
		return self._pressed["LeftTrigger"]
	def getRightTrigger(self):
		return self._pressed["RightTrigger"]
	def getLeftBumper(self):
		return self._pressed["LeftBumper"]
	def getRightBumper(self):
		return self._pressed["RightBumper"]
	def getLeftX(self):
		return self._pressed["LeftX"]
	def getLeftY(self):
		return self._pressed["LeftY"]
	def getRightX(self):
		return self._pressed["RightX"]
	def getRightY(self):
		return self._pressed["RightY"]
	def getLeftStickButton(self):
		return self._pressed["LeftStickButton"]
	def getRightStickButton(self):
		return self._pressed["RightStickButton"]
	def getName(self):
		return self.name
	def _read(self):
		while(True):
			(time, idk, hasInfo, key, value) = struct.unpack(EVENT_FORMAT, self.inputFile.read(EVENT_SIZE))
			if(hasInfo):
				if(key == 304):
					if(self.ABSwitch):
						self._buffer["B"] = bool(value)
					else:
						self._buffer["A"] = bool(value)
				elif(key == 305):
					if(self.ABSwitch):
						self._buffer["A"] = bool(value)
					else:
						self._buffer["B"] = bool(value)
				elif(key == 307):
					self._buffer["X"] = bool(value)
				elif(key == 308):
					self._buffer["Y"] = bool(value)
				elif(key == 310):
					self._buffer["LeftBumper"] = bool(value)
				elif(key == 311):
					self._buffer["RightBumper"] = bool(value)
				elif(key == 312):
					self._buffer["LeftTrigger"] = float(value)
				elif(key == 313):
					self._buffer["RightTrigger"] = float(value)
				elif(key == 314):
					self._buffer["Select"] = bool(value)
				elif(key == 315):
					self._buffer["Start"] = bool(value)
				elif(key == 316):
					self._buffer["Home"] = bool(value)
				elif(key == 317):
					self._buffer["LeftStickButton"] = bool(value)
				elif(key == 318):
					self._buffer["RightStickButton"] = bool(value)
				elif(key == 544):
					self._buffer["Up"] = bool(value)
				elif(key == 545):
					self._buffer["Down"] = bool(value)
				elif(key == 546):
					self._buffer["Left"] = bool(value)
				elif(key == 547):
					self._buffer["Right"] = bool(value)
				elif(key == 0):
					self._buffer["LeftX"] = adjust(signInt(value), self.joystickMax)
				elif(key == 1):
					self._buffer["LeftY"] = -adjust(signInt(value), self.joystickMax)
				elif(key == 2):
					self._buffer["LeftTrigger"] = adjust(signInt(value), self.triggerMax)
				elif(key == 3):
					self._buffer["RightX"] = adjust(signInt(value), self.joystickMax)
				elif(key == 4):
					self._buffer["RightY"] = -adjust(signInt(value), self.joystickMax)
				elif(key == 5):
					self._buffer["RightTrigger"] = adjust(signInt(value), self.triggerMax)
				elif(key == 16):
					val = signInt(value)
					if(val == 0):
						self._buffer["Left"] = False
						self._buffer["Right"] = False
					elif(val == 1):
						self._buffer["Left"] = False
						self._buffer["Right"] = True
					elif(val == -1):
						self._buffer["Left"] = True
						self._buffer["Right"] = False
				elif(key == 17):
					val = signInt(value)
					if(val == 0):
						self._buffer["Up"] = False
						self._buffer["Down"] = False
					elif(val == 1):
						self._buffer["Up"] = False
						self._buffer["Down"] = True
					elif(val == -1):
						self._buffer["Up"] = True
						self._buffer["Down"] = False
				elif(DEBUG_MODE):
					print(str(key) + ":" + str(value))

def signInt(int):
	if(int > MAX/2):
		return int-MAX
	else:
		return int

def adjust(val, max):
	if(val > 0):
		max-=1
	val = float(val)/max
	if(val > 1.0):
		val = 1.0
	elif(val<-1.0):
		val = -1.0
	return val

def getDevices():
	controllers = {}
	with open("/proc/bus/input/devices", "rb") as deviceFile:
		devices = str(deviceFile.read()).split("\\n\\n")
		for device in devices:
			lines = device.split("\\n")
			name = None
			handlers = None
			for line in lines:
				if("N: Name=" in line):
					name = line[9:-1]
				elif("H: Handlers=" in line):
					handlers = line[12:-1].split(" ")
			if(name in SUPPORTED_CONTROLLERS):
				num = None
				for handler in handlers:
					if("event" in handler):
						path = "/dev/input/" + handler
						controllers[path] = name
	return controllers

def getDeviceName(handler):
	with open("/proc/bus/input/devices", "rb") as deviceFile:
		devices = str(deviceFile.read()).split("\\n\\n")
		for device in devices:
			if(handler in device):
				name = None
				lines = device.split("\\n")
				for line in lines:
					if("N: Name=" in line):
						name = line[9:-1]
				return name
	return None

def promptForController(connected = []):
	controllers = getDevices()
	available = []
	i = 1
	for controller in controllers:
		if(controller not in connected):
			available.append(controller)
			print("["+ str(i) + "] " + controllers[controller] + " on " + controller)
			i+=1
	if(available == []):
		print("No available controllers")
		return None, connected
	selection = 0
	while selection == 0:
		userString = input()
		try:
			selection = int(userString)
			if(not (0 < selection <= i-1)):
				print(str(selection) + " is not an available controller")
				selection = 0
		except ValueError:
			print("\"" + userString + "\" is not an integer")
	path = available[selection-1]
	connected.append(path)
	return path, connected

def getAController():
	devices = getDevices()
	if(len(devices) == 0):
		print("No controllers connected. Connect a controller")
		while True:
			devices = getDevices()
			if(len(devices) != 0):
				break
			time.sleep(1)
	if(len(devices) == 1):
		return list(devices.keys())[0]
	else:
		return promptForController()[0]
