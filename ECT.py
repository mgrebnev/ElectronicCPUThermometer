#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
	Arduino | Atmega - PC(Linux) serial communication
	Show Celsius temeperature in 7 segment 4 digit display. Principal model : sh5461as

	PROTOCOL: Begin digit - SYMBOL|ACTIVE|DOT_, End digit - SYMBOL|ACTIVE|DOT\r\n

	SYMBOL ACCEPT DATA:

	 SYMBOL    LED SYMBOL
	0,...,9  -  0,...,9
	     10  -  "-"

	Example.
	Number - "-1.23" - [ 10|1|0_1|1|1_2|1|0_3|1|0 ]
	Number - "56.3"  - [  0|0|0_5|1|0_6|1|1_3|1|0 ]
'''

import serial
import subprocess
import numpy as np
import time
import re
import threading
import argparse

from time import sleep
from threading import Event, Thread, Timer

class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

class SensorsParser:
	@staticmethod
	def getTemperature(firstSymbols):
		currentTemperature = None
		sensorsData = str(subprocess.check_output(["sensors"])).split("\n")
		for currentLine in sensorsData:
			isRequiredLine = currentLine.startswith(firstSymbols)
			if isRequiredLine:
				startTemperatureIndex,endTemperatureIndex = re.search('\d+[.]\d+', currentLine).span()
				currentTemperature = currentLine[int(startTemperatureIndex):int(endTemperatureIndex)]
		return currentTemperature

class LEDEncoder:
	def getCompleteNumber(self,number):
		counter = 0;

		resultNumber = ""
		for symbol in number:
			currentSymbol = str(symbol)
			if currentSymbol.isdigit() or currentSymbol == "-" or currentSymbol == ".":
				if currentSymbol != ".":
					counter = counter + 1
				resultNumber = resultNumber + currentSymbol

		if counter > 4 or resultNumber.count(".") > 4:
			resultNumber = "0000"
		else:
			countCompleteZeros = 4 - counter

			temporaryNumber = ""
			for i in range(0,countCompleteZeros):
				temporaryNumber = temporaryNumber + "D"

			resultNumber = temporaryNumber + resultNumber

		return resultNumber
	

	def getEncodedData(self,number):
		completeNumber = str(self.getCompleteNumber(number))
		
		index = 0
		encodedData = ""
		while index < len(completeNumber):
			currentSymbol = completeNumber[index]
			if currentSymbol == ".":
				encodedData = encodedData + "0|1|1_"
				index = index + 1
				continue
			else:
				if currentSymbol == "D":
					encodedData = encodedData + "0|0|0_"
				else:
					firstNumber = currentSymbol

					if currentSymbol == "-":
						firstNumber = "10"

					encodedData = encodedData + firstNumber + "|1"
					if index + 1 < len(completeNumber) and completeNumber[index + 1] == ".":
						encodedData = encodedData + "|1_"
						index = index + 1
					else:
						encodedData = encodedData + "|0_"
			
			index = index + 1
					
		return encodedData[0:len(encodedData) - 1]


class SerialPortHandler:
	def __init__(self):
		self.ledEncoder = LEDEncoder()

	def initConnection(self,port,baudrate):
		serialConnection = serial.Serial(
			port=port,
			baudrate=baudrate,
			parity=serial.PARITY_ODD,
			stopbits=serial.STOPBITS_ONE,
			bytesize=serial.EIGHTBITS
		)
		self.serialConnection = serialConnection
		return serialConnection

	def sendTemperatureData(self,isSilenceMode, parseLineStartSymbols):
		currentTemperature = SensorsParser.getTemperature(parseLineStartSymbols)
		if isSilenceMode == False:
			print "Current temperature: " + currentTemperature + " °C"
		encodedTemperature = self.ledEncoder.getEncodedData(currentTemperature)
		self.serialConnection.write(encodedTemperature+ "\r\n")

def getConsoleArgs():
    parser = argparse.ArgumentParser(prog="ElectronicCPUThermometer")
    parser.add_argument('-p',required=True,default="/dev/ttyACM0",help="[Port to which the device is connected]",metavar="",dest="port")
    parser.add_argument('-d',required=True,default="1.5",help="[Delay between repeat temperature sending (seconds)]",metavar="",dest="refreshTime")
    parser.add_argument('-b',required=True,default="9600",help="[Data transfer speed]",metavar="",dest="baudrate")
    parser.add_argument('-w',required=False,default="Core 0",help="[First words of the required line]",metavar="",dest="parseLineStartSymbols")
    return parser.parse_args();

try:
	consoleArgs = getConsoleArgs()

	port = str(consoleArgs.port)
	refreshTime = float(consoleArgs.refreshTime)
	baudrate = int(consoleArgs.baudrate)
	parseLineStartSymbols = str(consoleArgs.parseLineStartSymbols)
	
	serialPortHandler = SerialPortHandler()
	serialConnection = serialPortHandler.initConnection(port,baudrate)

	print "Please, wait..."
	sleep(2.5)

	repeatedTimer = RepeatedTimer(refreshTime, serialPortHandler.sendTemperatureData, True, parseLineStartSymbols)
	welcomeMessages = ["Connection accept!",
	                  "  [q] - Close connection and quit",
				      "  [r] - Reconnect",
				      "  [Enter] - Resending temperature"]
	
	for message in welcomeMessages:
		print message

	while True:
		inputData = raw_input('')
		
		if inputData == "q":
			repeatedTimer.stop()
			serialConnection.close()
			exit()
		if inputData == "r":
			serialConnection.close()
			serialConnection = serialPortHandler.initConnection(port,baudrate)
			print "Reconnect. Please, wait..."
			sleep(2.5)
			print "Connection accept!"
		if inputData == "":
			serialPortHandler.sendTemperatureData(False,parseLineStartSymbols)
			
except Exception as e:
	print e
	exit() # lol, required