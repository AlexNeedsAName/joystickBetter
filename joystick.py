#!/usr/bin/env python3
import threading, struct, time, yaml, sys

DEBUG_MODE = False

EVENT_FORMAT = "llHHI"
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)
MAX = 4294967296
BUTTON = 1
AXIS = 3

class joystick():
	_buffer = { "A":False, "B":False, "X":False, "Y":False, "L":False, "R":False, "Left Trigger":0.0, "Right Trigger":0.0, "Select":False, "Start":False, "Home":False, "Left Stick Button":False, "Right Stick Button":False, "Up":False, "Down":False, "Left":False, "Right":False, "Left X":0, "Left Y":0, "Right X":0, "Right Y":0, "C":False, "Z":False}
	_pressed = _buffer
	ABSwitch = False
	joystickMax = 32768
	triggerMax = 255

	connected = False

	updateThread = None

	def __init__(self, path, layout = None, getRaw = False): #Layout will be used to specify a button mapping (eg, Nintendo or Xbox ABXY)
		#Save the paramaters for later use
		self.path = path
		self.handler = self.path[11:]
		self.name = getDeviceName(self.handler)

		self.bindings, self.settings = self.getBindings(self.name)

		#Change a few settings for specific controllers
		if(self.name == "Nintendo Wii Remote Pro Controller"):
			self.joystickMax = 1024
			self.ABSwitch = True
		elif(self.name == "Nintendo Wii Remote Classic Controller"):
			self.joystickMax = 32
		elif(self.name == "Nintendo Wii Remote Nunchuk"):
			self.joystickMax = 64

		if(self.waitForConnection()):
			raise PermissionError

		#Run normal thread or just output raw values from the handler
		if(getRaw):
			self.updateThread = threading.Thread(target=self._readRaw, daemon=True)
		else:
			self.updateThread = threading.Thread(target=self._read, daemon = True)

		self.updateThread.start()

	def getBindings(self, name):
		with open("bindings.yaml", 'rb') as bindingsFile:
			allBindings = yaml.load(bindingsFile)
			#Load the default bindings and settings
			bindings = allBindings["Default"]["Bindings"]
			settings = allBindings["Default"]["Settings"]

			#Merge the default bindings with the bindings for this controller
			#If there are conflicts, the ones for the controller wins
			try:
				bindings.update(allBindings[name]["Bindings"])
			except KeyError:
				pass
			try:
				settings.update(allBindings[name]["Settings"])
			except KeyError:
				pass

			return (bindings, settings)


	#Save the current value from the buffer to the list used for output.
	#This way the value of a button won't change until the caller is ready
	def poll(self):
		self._pressed = self._buffer

	def waitForConnection(self):
		if(self.connected == True):
			return 0
		else:
			while True:
				try:
					self.inputFile = open(self.path, "rb")
					self.connected = True
					return 0
				except PermissionError:
					return 1
				except OSError:
					self.connected = False
					time.sleep(.1)

	def _readRaw(self):
		while(True):
			try:
				(time, idkWhatThisIs, type, key, value) = struct.unpack(EVENT_FORMAT, self.inputFile.read(EVENT_SIZE))
			except OSError:
				self.connected = False
				self.waitForConnection()
			if(type != 0):
				try:
					print(str(key) + " (" + self.bindings[key] + "):" + str(value))
				except KeyError:
					print(str(key) + ":" + str(value))

	def _read(self):
		while(True):
			try:
				(time, idkWhatThisIs, type, key, value) = struct.unpack(EVENT_FORMAT, self.inputFile.read(EVENT_SIZE))
			except OSError:
				self.connected = False
				self.waitForConnection()
			try:
				keyName = self.bindings[key]
				if(type == BUTTON):
					self._buffer[keyName] = bool(value)

				elif(type == AXIS):
					value = signInt(value)
					max = self.settings["Analog Max"][keyName]
					if(self.settings["Inverted Y"] and "Y" in keyName):
						self._buffer[keyName] = -adjust(value, max)
					else:
						self._buffer[keyName] = adjust(value, max)

			except KeyError:
				if(DEBUG_MODE):
					print("Unbound key: " + str(key))
				pass

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
		return self._pressed["Left Trigger"]
	def getRightTrigger(self):
		return self._pressed["Right Trigger"]
	def getLeftBumper(self):
		return self._pressed["L"]
	def getRightBumper(self):
		return self._pressed["R"]
	def getLeftX(self):
		return self._pressed["Left X"]
	def getLeftY(self):
		return self._pressed["Left Y"]
	def getRightX(self):
		return self._pressed["Right X"]
	def getRightY(self):
		return self._pressed["Right Y"]
	def getLeftStickButton(self):
		return self._pressed["Left Stick Button"]
	def getRightStickButton(self):
		return self._pressed["Right Stick Button"]
	def getName(self):
		return self.name

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
			if(name in SUPPORTED_CONTROLLERS or (includeUnsupported is True and handlers is not None)):
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

def getSupportedControllers():
	controllers = []
	with open("bindings.yaml", 'rb') as bindingsFile:
		allBindings = yaml.load(bindingsFile)
		for binding in allBindings:
			if(binding != "Default"):
				controllers.append(binding)
	return controllers

SUPPORTED_CONTROLLERS = getSupportedControllers()
if(DEBUG_MODE and __name__ == "__main__"):
	js = joystick(promptForController(includeUnsupported = False)[0], getRaw = True)
	input("Press enter to quit.\n")

