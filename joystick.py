#!/usr/bin/env python3
import threading, struct, time, yaml, sys, collections, os

DEBUG_MODE = True
REGISTER_MODE = False

EVENT_FORMAT = "llHHI"
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)
MAX = 4294967296
BUTTON = 1
AXIS = 3

_path = __file__.split("/")
_path.pop(len(_path)-1)
_path = "/".join(_path) + "/"

class Button:
	_current  = False
	_pressed  = False
	_down     = False
	_released = False

	def update(self, current):
		self._current = current

	def poll(self):
		self._pressed  = (self._current and not self._down)
		self._released = (not self._current and self._down)
		self._down = self._current

	def isDown(self):
		return self._down

	def isPressed(self):
		return self._pressed

	def isReleased(self):
		return self._released

	def getValue(self):
		return int(self._down)

class Axis:
	_current = 0
	_value = 0

	def update(self, value):
		if(isinstance(value, bool)):
			value = int(value)
		self._current = value

	def poll(self):
		self._value = self._current

	def getValue(self):
		return self._value

class Stick:
	def __init__(self, X, Y, button):
		self._X = X
		self._Y = Y
		self.Button = button

	def getX(self):
		return self._X.getValue()

	def getY(self):
		return self._Y.getValue()

class joystick:
	_buffer = {}
	connected = False
	updateThread = None

	def __init__(self, path, layout = None, getRaw = False): #Layout will be used to specify a button mapping (eg, Nintendo or Xbox ABXY)
		#Save the paramaters for later use
		self.path = path
		self.handler = self.path[11:]
		self.name = getDeviceName(self.handler)

		self.bindings, self.settings = self.readBindings(self.name)

		if(self.waitForConnection()):
			raise PermissionError

		#Run normal thread or just output raw values from the handler
		if(getRaw):
			self.updateThread = threading.Thread(target=self._readRaw, daemon=True)
		else:
			self.updateThread = threading.Thread(target=self._read, daemon = True)

		self.updateThread.start()

	def readBindings(self, name):
		with open(_path + "Bindings/Default.yaml", 'rb') as bindingsFile:
			defaultBindings = yaml.load(bindingsFile)
			#Load the default bindings and settings
			bindings = defaultBindings["Bindings"]
			settings = defaultBindings["Settings"]

		with open(_path + "Bindings/" + name + ".yaml") as bindingsFile:
			specificBindings = yaml.load(bindingsFile)
			#Merge the default bindings with the bindings for this controller
			#If there are conflicts, the ones for the controller wins
			try:
				bindings = update(bindings, specificBindings["Bindings"])
			except KeyError:
				pass
			try:
				settings = update(settings, specificBindings["Settings"])
			except KeyError:
				pass

		return (bindings, settings)

	def getBinding(self, key):
		return self.bindings[key]

	#Save the current value from the buffer to the list used for output.
	#This way the value of a button won't change until the caller is ready
	def poll(self):
		for key,value in self._buffer.items():
			value.poll()

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
				(time, _, type, key, value) = struct.unpack(EVENT_FORMAT, self.inputFile.read(EVENT_SIZE))
			except OSError:
				self.connected = False
				self.waitForConnection()

			try:
				if(key in self.bindings):
					keyName = self.bindings[key]

					if("Keys that look like axes" in self.settings and keyName in self.settings["Keys that look like axes"]):
						type = BUTTON

					if(type == BUTTON):
						if(REGISTER_MODE):
							print(str(key) + " : " + str(bool(value)))
						if("Trigger" in keyName and self.settings["Triggers are Buttons"]):
							self._buffer[keyName].update(float(value))
						else:
							self._buffer[keyName].update(bool(value))

					elif(type == AXIS):
						value = signInt(value)
						if("DPad" not in keyName and "Touchpad" not in keyName):
							value = value-self.settings["Analog Center"][keyName]

						if(self.settings["D-Pad is Axis"] and "DPad" in keyName):
							if(keyName == "DPad X"):
								if(value < 0):
									self._buffer["Right"].update(False)
									self._buffer["Left"].update(True)
								elif(value > 0):
									self._buffer["Right"].update(True)
									self._buffer["Left"].update(False)
								else:
									self._buffer["Right"].update(False)
									self._buffer["Left"].update(False)
							elif(keyName == "DPad Y"):
								if(self.settings["Inverted Y"] ):
									value = -value
								if(value < 0):
									self._buffer["Up"].update(False)
									self._buffer["Down"].update(True)
								elif(value > 0):
									self._buffer["Up"].update(True)
									self._buffer["Down"].update(False)
								else:
									self._buffer["Up"].update(False)
									self._buffer["Down"].update(False)
						elif("Touchpad" in keyName):
							if("Release" in keyName):
								self._buffer["Touchpad Touched"].update(bool(value + 1))
							else:
								self._buffer[keyName].update(value)
						elif(key in [40,41,42]):
							self._buffer[keyName].update(value)
						elif(self.settings["Inverted Y"] and "Y" in keyName):
							self._buffer[keyName].update(-adjust(value, self.settings["Analog Max"][keyName]))
						else:
							self._buffer[keyName].update(adjust(value, self.settings["Analog Max"][keyName]))

				else:
					if(DEBUG_MODE and key not in [43,44,45]):
						print("Unbound key: " + str(key) + " with value of " + str(value) + " (type " + str(type) + ")")
			except KeyError:
				pass

class GenericNoSticks(joystick): #Like an SNES Controller
	_buffer = { "A":Button(), "B":Button(), "X":Button(), "Y":Button(), "L":Button(), "R":Button(), "Start":Button(), "Select":Button(), "Home":Button(), "Up":Button(), "Down":Button(), "Left":Button(), "Right":Button()}

	A =  _buffer["A"]
	B =  _buffer["B"]
	X =  _buffer["X"]
	Y =  _buffer["Y"]
	L =  _buffer["L"]
	R =  _buffer["R"]

	Start = _buffer["Start"]
	Select = _buffer["Select"]
	Home = _buffer["Home"]

class GenericTwoStickGamepad(joystick): #Like a modern console controller
	_buffer = { "A":Button(), "B":Button(), "X":Button(), "Y":Button(), "L":Button(), "R":Button(), "Left Trigger":Axis(), "Right Trigger":Axis(), "Start":Button(), "Select":Button(), "Home":Button(), "Up":Button(), "Down":Button(), "Left":Button(), "Right":Button(), "Left X":Axis(), "Left Y":Axis(), "Left Stick Button":Button(), "Right X":Axis(), "Right Y":Axis(), "Right Stick Button":Button()}

	A =  _buffer["A"]
	B =  _buffer["B"]
	X =  _buffer["X"]
	Y =  _buffer["Y"]
	L =  _buffer["L"]
	R =  _buffer["R"]
	ZL = _buffer["Left Trigger"]
	ZR = _buffer["Right Trigger"]

	Start = _buffer["Start"]
	Select = _buffer["Select"]
	Home = _buffer["Home"]

	Up    = _buffer["Up"]
	Down  = _buffer["Down"]
	Left  = _buffer["Left"]
	Right = _buffer["Right"]

	LeftStick  = Stick(_buffer["Left X"],  _buffer["Left Y"],  _buffer["Left Stick Button"])
	RightStick = Stick(_buffer["Right X"], _buffer["Right Y"], _buffer["Right Stick Button"])

class WiiUProController(joystick):
	_buffer = { "A":Button(), "B":Button(), "X":Button(), "Y":Button(), "L":Button(), "R":Button(), "Left Trigger":Button(), "Right Trigger":Button(), "Up":Button(), "Down":Button(), "Left":Button(), "Right":Button(), "Left X":Axis(), "Left Y":Axis(), "Left Stick Button":Button(), "Right X":Axis(), "Right Y":Axis(), "Right Stick Button":Button()}

	A =  _buffer["A"]
	B =  _buffer["B"]
	X =  _buffer["X"]
	Y =  _buffer["Y"]
	L =  _buffer["L"]
	R =  _buffer["R"]
	ZL = _buffer["Left Trigger"]
	ZR = _buffer["Right Trigger"]

	Up    = _buffer["Up"]
	Down  = _buffer["Down"]
	Left  = _buffer["Left"]
	Right = _buffer["Right"]

	LeftStick  = Stick(_buffer["Left X"],  _buffer["Left Y"],  _buffer["Left Stick Button"])
	RightStick = Stick(_buffer["Right X"], _buffer["Right Y"], _buffer["Right Stick Button"])

class PS4Controller(joystick):
	_buffer = { "A":Button(), "B":Button(), "X":Button(), "Y":Button(), "L":Button(), "R":Button(), "Left Trigger":Axis(), "Right Trigger":Axis(), "Up":Button(), "Down":Button(), "Left":Button(), "Right":Button(), "Left X":Axis(), "Left Y":Axis(), "Left Stick Button":Button(), "Right X":Axis(), "Right Y":Axis(), "Right Stick Button":Button()}

	A =  _buffer["A"]
	B =  _buffer["B"]
	X =  _buffer["X"]
	Y =  _buffer["Y"]
	L =  _buffer["L"]
	R =  _buffer["R"]
	ZL = _buffer["Left Trigger"]
	ZR = _buffer["Right Trigger"]

	Up    = _buffer["Up"]
	Down  = _buffer["Down"]
	Left  = _buffer["Left"]
	Right = _buffer["Right"]

	LeftStick  = Stick(_buffer["Left X"],  _buffer["Left Y"],  _buffer["Left Stick Button"])
	RightStick = Stick(_buffer["Right X"], _buffer["Right Y"], _buffer["Right Stick Button"])

def update(d, u):
	for k, v in u.items():
		if(isinstance(v, collections.Mapping)):
			r = update(d.get(k, {}), v)
			d[k] = r
		else:
			d[k] = u[k]
	return d

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

def getDevices(includeUnsupported=True):
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
	EXTENSION = ".yaml"
	controllers = []
	for filename in os.listdir(_path + "Bindings/"):
		if(filename.endswith(EXTENSION)):
			controllers.append(filename[:-len(EXTENSION)])
	return controllers
SUPPORTED_CONTROLLERS = getSupportedControllers()


#if((DEBUG_MODE or REGISTER_MODE) and __name__ == "__main__"):
#	js = joystick(promptForController(includeUnsupported = True)[0], getRaw = True)
#	input("Press enter to quit.\n")

if(__name__ == "__main__"):
	print("Connecting")
	js = WiiUProController(getAController())
	print("Connected")
	while(True):
		js.poll()
		print(js.LeftStick.Button.isDown())
		time.sleep(0.01)
