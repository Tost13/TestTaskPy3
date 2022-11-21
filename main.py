import sys
import os
import time
import threading
import serial
import re
from dataclasses import dataclass

baudrateUART = 115200
portUART = 'COM4'

# global variables
global UARTState
UARTState = "wait"  # states for tasks (wait, send, wait, buttonReset)
global RxBuff
global TxBuff
RxBuff = ""
TxBuff = ""

# structure to store values from device


@dataclass
class LEDState:
    state: str
    brightness: int
    frequency: float


global ledState
ledState = LEDState(state="", brightness=0, frequency=0.0)

# Function to get status values on the device
# Output: Status


def stateCmd():
    global UARTState
    global RxBuff
    global TxBuff
    TxBuff = "status\r"
    UARTState = "send"
    while UARTState != "wait":
        time.sleep(0.1)
    data = RxBuff.split(";")
    if data[0] == "STATUS":
        state = int(re.search(r'\d+', data[1]).group())
        if state == 0:
            ledState.state = "off"
        elif state == 1:
            ledState.state = "on"
        elif state == 2:
            ledState.state = "blink"
        ledState.brightness = int(re.search(r'\d+', data[2]).group())
        frequencyData = data[3].split("=")
        ledState.frequency = float(frequencyData[1])
        return True
    else:
        return False

# Function to reset values on the device
# Output: Status


def resetCmd():
    global UARTState
    global RxBuff
    global TxBuff
    TxBuff = "reset\r"
    UARTState = "send"
    while UARTState != "wait":
        time.sleep(0.1)
    if RxBuff == "RESET\r\n":
        stateCmd()
        return True
    else:
        return False

# Function to set values on the device
# Input: string with command
# Output: Status


def setValueCmd(command):
    global UARTState
    global RxBuff
    global TxBuff
    TxBuff = command+"\r"
    UARTState = "send"
    while UARTState != "wait":
        time.sleep(0.1)
    data = RxBuff.split(";")
    if data[0] == "STATUS":
        state = int(re.search(r'\d+', data[1]).group())
        if state == 0:
            ledState.state = "off"
        elif state == 1:
            ledState.state = "on"
        elif state == 2:
            ledState.state = "blink"
        ledState.brightness = int(re.search(r'\d+', data[2]).group())
        frequencyData = data[3].split("=")
        ledState.frequency = float(frequencyData[1])
        return True
    else:
        return False

# Task responsible for user input


def CommTask():

    global ledState
    for line in sys.stdin:
        string = line.rstrip()
        setCmd = string.split("=")
        if "help" == string:
            print(
                '/***************************************************************************************/')
            print('help: \r\n')
            print('status - get status of the device')
            print('reset - reset values on the device')
            print(
                'state=value - set state on the device, options of value are on, off and blink')
            print('   example state=on')
            print(
                'brightness=value - set brightness on the device, options of value are from 0 to 100')
            print('   example brightness=50')
            print(
                'frequency=value - set frequency on the device, options of value are from 0.5 to 10.0')
            print('   example frequency=2.0')
            print(
                '   in float only 4 numbers  after zero are accepted, 1.23456 will be rounded to 1.2346')
            print(
                '/***************************************************************************************/')
        elif "status" == string:
            stateCmd()
            print("STATUS:", "state is", ledState.state, "; brightness is", ledState.brightness, "%",
                  "; frequency is", ledState.frequency, "Hz")
        elif "reset" == string:
            if resetCmd():
                print('reset PASSED')
            else:
                print('reset FAILED')
        elif len(setCmd) == 2:
            if "state" == setCmd[0]:
                if setCmd[1] == "off" or setCmd[1] == "on" or setCmd[1] == "blink":
                    if (setValueCmd(string)):
                        if ledState.state == setCmd[1]:
                            print('state command set value PASSED')
                        else:
                            print(
                                'ERROR: state command set value PASSED but value wasnt changed')
                    else:
                        print('ERROR: state command set value FAILED')
                else:
                    print('ERROR: wrong input in state command (off, on or blink)')
            elif "brightness" == setCmd[0]:
                try:
                    value = int(setCmd[1])
                except ValueError:
                    print('Int expected for brightness command')
                    value = 0xFF
                if value >= 0 and value <= 100:
                    if value == 0:
                        print(
                            'WARNING: value 0 is the same as state=off, use it insted')
                    if (setValueCmd(string)):
                        if ledState.brightness == value:
                            print('brightness command set value PASSED')
                        else:
                            print(
                                'ERROR: brightness command set value PASSED but value wasnt changed')
                    else:
                        print('ERROR: brightness command set value FAILED')
                else:
                    print('ERROR: wrong input in brightness command (from 0 to 100)')
            elif "frequency" == setCmd[0]:
                try:
                    value = float(setCmd[1])
                    valueStr = format(value, '.4f')
                    value = float(valueStr)
                except ValueError:
                    print('Float expected for frequency command')
                    value = 0xFF
                if value >= 0.5 and value <= 10.0:
                    if (setValueCmd(setCmd[0] + "=" + valueStr)):
                        if ledState.frequency == value:
                            print('frequency command set value PASSED')
                        else:
                            print(
                                'ERROR: frequency command set value PASSED but value wasnt changed')
                    else:
                        print('ERROR: frequency command set value FAILED')
                else:
                    print('ERROR: wrong input in frequency command (from 0.5 to 10.0)')
            else:
                print('INFO: unknown command with =, use help for more info')
        else:
            print('INFO: unknown command, use help for more info')

# Task responsible for UART comm


def UARTTask():
    global UARTState
    global RxBuff
    global TxBuff
    serialUART = serial.Serial(port=portUART, baudrate=baudrateUART)
    serialUART.timeout = 5
    if serialUART.is_open:
        while True:
            if UARTState == "send":
                serialUART.write(TxBuff.encode())
                UARTState = "read"
                time.sleep(0.1)
            size = serialUART.inWaiting()
            if size:
                data = serialUART.read(size)
                if UARTState == "read":
                    RxBuff = data.decode("utf-8")
                    UARTState = "wait"
                # received if button pressed
                elif data.decode("utf-8") == "BUTTON RESET\r\n":
                    UARTState = "buttonReset"

            time.sleep(0.2)
    else:
        print("ERROR: UART is not open")


def Main():
    global ledState
    global UARTState
    t1 = threading.Thread(target=CommTask, args=())
    t2 = threading.Thread(target=UARTTask, args=())
    t1.start()
    t2.start()
    global UARTState
    print("type help for more info")
    stateCmd()
    print("Initial device status:", "state is", ledState.state, "; brightness is", ledState.brightness, "%",
          "; frequency is", ledState.frequency, "Hz")
    while True:
        if UARTState == "buttonReset":
            print("INFO: device was reset using button")
            stateCmd()
            print("Status after reset:", "state is", ledState.state, "; brightness is", ledState.brightness, "%",
                  "; frequency is", ledState.frequency, "Hz")
        time.sleep(0.1)


if __name__ == '__main__':

    Main()
