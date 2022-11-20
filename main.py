import sys
import os
import time
import threading
import serial
import re
from dataclasses import dataclass

baudrateUART = 115200
portUART = 'COM4'
thread_flag = None

global UARTState
UARTState = "wait"
global RxBuff
global TxBuff
RxBuff = ""
TxBuff = ""


@dataclass
class LEDState:
    state: str
    brightness: int
    frequency: float


global ledState
ledState = LEDState(state="", brightness=0, frequency=0.0)


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
    else:
        print("Status failed")

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
        print("RESET successful")
    else:
        print("RESET failed")


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
    else:
        print("set value failed")


def CommTask():

    global ledState
    for line in sys.stdin:
        string = line.rstrip()
        if 'q' == string:
            break
        elif "help" == string:
            print('help: \r\n')
            print('status - get status of the device')
            print('status - get status of the device')
        elif "status" == string:
            print('Status')
            stateCmd()
            print("STATUS:", "state is", ledState.state, "brightness is", ledState.brightness, "%",
                  "frequency is", ledState.frequency, "Hz")
        elif "reset"== string:
            resetCmd()
        setCmd = string.split("=")
        if "state" == setCmd[0]:
            if len(setCmd) == 2:
                print('STATE')
                if setCmd[1] == "off" or setCmd[1] == "on" or setCmd[1] == "blink":
                    setValueCmd(string)
                else:
                    print('wrong input in state comand')



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
                print("RX", data)
                if UARTState == "read":
                    RxBuff = data.decode("utf-8")
                    UARTState = "wait"

            time.sleep(0.2)
    else:
        print("sestatusrialUART not open")


def Main():
    global ledState
    t1 = threading.Thread(target=CommTask, args=())
    t2 = threading.Thread(target=UARTTask, args=())
    t1.start()
    t2.start()
    global UARTState
    print("type help for mode info")
    stateCmd()
    print("Initial device status:", "state is", ledState.state, "brightness is", ledState.brightness, "%",
          "frequency is", ledState.frequency, "Hz")
    while True:
        time.sleep(0.1)



if __name__ == '__main__':

    Main()
