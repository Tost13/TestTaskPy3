# TestTaskPy3

Created with Python 3.11 using a virtual environment

Connect the STM32F3DISCOVERY device and wait for LED3 to start blinking. Connect UART to the USB connector to PC5(Rx) and PC4(Tx), change the portUART value to your COM port and start the main.py script.

Commands to use:
help - print help
status - get the status of the device
reset - reset values on the device
state=value - set the state on the device, options of value are on, off, and blink, example state=on
brightness=value - set brightness on the device, options of value are from 0 to 100, example brightness=50
frequency=value - set frequency on the device, options of value are from 0.5 to 10.0, example frequency=2.0 in float only 4 numbers after zero are accepted, 1.23456 will be rounded to 1.2346