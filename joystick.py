#!/usr/bin/env python3
import threading, struct, time
import time
SUPPORTED_CONTROLLERS = ["Nintendo Wii", "Logitech Gamepad F310"]
EVENT_FORMAT = "llHHI"
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)
DEBUG_MODE = True
MAX = 4294967296

class joystick():
	_buffer = { "B":False, "A":False, "X":False, "Y":False, "LeftBumper":False, "RightBumper":False, "LeftTrigger":0.0, "RightTrigger":0.0, "Select":False, "Start":False, "Home":False, "LeftStickButton":False, "RightStickButton":False, "Up":False, "Down":False, "Left":False, "Right":False, "LeftX":0, "LeftY":0, "RightX":0, "RightY":0, "C":False, "Z":False}
	_pressed = _buffer
	ABSwitch = False
	joystickMax = 32768
	triggerMax = 255

	connected = False

	def __init__(self, path, layout = None, getRaw = False): #Layout will be used to specify a button mapping (eg, Nintendo or Xbox ABXY)
		#Save the paramaters for later use
		self.path = path
		self.handler = self.path[11:]
		self.name = getDeviceName(self.handler)

		#Change a few settings for specific controllers
		if(self.name == "Nintendo Wii Remote Pro Controller"):
			self.joystickMax = 1024
			self.ABSwitch = True
		elif(self.name == "Nintendo Wii Remote Classic Controller"):
			self.joystickMax = 32
		elif(self.name == "Nintendo Wii Remote Nunchuk"):
			self.joystickMax = 64

		self.waitForConnection()

		#Run normal thread or just output raw values from the handler
		if(getRaw):
			self.updateThread = threading.Thread(target=self._readRaw, daemon=True)
		else:
			self.updateThread = threading.Thread(target=self._read, daemon = True)

		self.updateThread.start()

	#Save the current value from the buffer to the list used for output.
	#This way the value of a button won't change until the caller is ready
	def poll(self):
		self._pressed = self._buffer

	#All the getter functions for inputs, settings, status, etc
	def isConnected(self):
		return self.connected
	def getA(self):
		return self._pressed["A"]
	def getB(self):
		return self._pressed["B"]
	def getC(self):
		return self._pressed["C"]
	def getX(self):
		return self._pressed["X"]
	def getY(self):
		return self._pressed["Y"]
	def getZ(self):
		return self._pressed["Z"]
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
	def _readRaw(self):
		while(True):
			(time, idk, hasInfo, key, value) = struct.unpack(EVENT_FORMAT, self.inputFile.read(EVENT_SIZE))
			if(hasInfo):
				print(str(key) + ":" + str(value))
	def waitForConnection(self):
		if(self.connected == True):
			return 0
		else:
			while True:
				try:
					self.inputFile = open(self.path, "rb")
					self.connected = True
					return 0
				except OSError:
					self.connected = False
					time.sleep(.1)

	def _read(self):
		while(True):
			try:
				(time, idk, hasInfo, key, value) = struct.unpack(EVENT_FORMAT, self.inputFile.read(EVENT_SIZE))
			except OSError:
				self.connected = False
				self.waitForConnection()

			if(hasInfo):
				if(key == 304 and self.ABSwitch == True):
					self._buffer["B"] = bool(value)
				elif(key == 304):
					self._buffer["A"] = bool(value)
				elif(key == 305 and self.ABSwitch == True):
					self._buffer["A"] = bool(value)
				elif(key == 305):
					self._buffer["B"] = bool(value)
				elif(key == 306):
					self._buffer["C"] = bool(value)
				elif(key == 307 or key == 257):
					self._buffer["X"] = bool(value)
				elif(key == 308 or key == 258):
					self._buffer["Y"] = bool(value)
				elif(key == 309):
					self._buffer["Z"] = bool(value)
				elif(key == 310):
					self._buffer["LeftBumper"] = bool(value)
				elif(key == 311):
					self._buffer["RightBumper"] = bool(value)
				elif(key == 312):
					self._buffer["LeftTrigger"] = float(value)
				elif(key == 313):
					self._buffer["RightTrigger"] = float(value)
				elif(key == 314 or key == 412):
					self._buffer["Select"] = bool(value)
				elif(key == 315 or key == 407):
					self._buffer["Start"] = bool(value)
				elif(key == 316):
					self._buffer["Home"] = bool(value)
				elif(key == 317):
					self._buffer["LeftStickButton"] = bool(value)
				elif(key == 318):
					self._buffer["RightStickButton"] = bool(value)
				elif(key == 544 or key == 103):
					self._buffer["Up"] = bool(value)
				elif(key == 545 or key == 108):
					self._buffer["Down"] = bool(value)
				elif(key == 546 or key == 105):
					self._buffer["Left"] = bool(value)
				elif(key == 547 or key == 106):
					self._buffer["Right"] = bool(value)
				elif(key == 0 and self.name != "Nintendo Wii Remote Nunchuk"):
					self._buffer["LeftX"] = adjust(signInt(value), self.joystickMax)
				elif(key == 1 and self.name != "Nintendo Wii Remote Nunchuk"):
					self._buffer["LeftY"] = -adjust(signInt(value), self.joystickMax)
				elif(key == 2 and self.name != "Nintendo Wii Remote Nunchuk"):
					self._buffer["LeftTrigger"] = adjust(signInt(value), self.triggerMax)
				elif(key == 3 and self.name != "Nintendo Wii Remote Nunchuk"):
					self._buffer["RightX"] = adjust(signInt(value), self.joystickMax)
				elif(key == 4 and self.name != "Nintendo Wii Remote Nunchuk"):
					self._buffer["RightY"] = -adjust(signInt(value), self.joystickMax)
				elif(key == 5 and self.name != "Nintendo Wii Remote Nunchuk"):
					self._buffer["RightTrigger"] = adjust(signInt(value), self.triggerMax)
				elif(key == 16 and self.name == "Nintendo Wii Remote Nunchuk"):
					self._buffer["LeftX"] = adjust(signInt(value), self.joystickMax)
				elif(key == 17 and self.name == "Nintendo Wii Remote Nunchuk"):
					self._buffer["LeftY"] = -adjust(signInt(value), self.joystickMax)
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
				elif(self.name == "Nintendo Wii Remote Classic Controller"):
					if(key == 18):
						self._buffer["LeftX"] = signInt(value)
					elif(key == 19):
						self._buffer["LeftY"] = -signInt(value)
					elif(key == 20):
						self._buffer["RightX"] = signInt(value)
					elif(key == 21):
						self._buffer["RightY"] = -signInt(value)
				elif(DEBUG_MODE and key not in [3,4,5]):
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

def getDevices(includeUnsupported=False):
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
			if(name in SUPPORTED_CONTROLLERS or (includeUnsupported is True and handlers is not None) or (name is not None and "Wii" in name)):
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

def promptForController(connected = [], includeUnsupported=False):
	controllers = getDevices(includeUnsupported=includeUnsupported)
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

if(DEBUG_MODE and __name__ == "__main__"):
	js = joystick(promptForController(includeUnsupported = True)[0], getRaw = True)
	input("Press enter to quit.\n")

