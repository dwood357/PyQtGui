# This Python file uses the following encoding: utf-8
import sys
import os
import serial
import time
import resource_rc
from struct import pack
import pyqtgraph as pg
import numpy as np
from dataclasses import dataclass
from pyqtgraph import PlotWidget, plot

from PySide2.QtWidgets import QApplication, QMainWindow
from PySide2.QtCore import QFile, QIODevice
from PySide2.QtUiTools import QUiLoader
from PySide2.QtGui import QAction

from CAN_TOOL import CAN_TOOL

x = 0
y = 0


@dataclass
class dataMSG:
    # pythonic way to do a C like struct
    mode: int = 1  # default is mode 1
    deratePercentage: int = 0  # middle frequency in Hz
    driveCMD: int = 0 # middle duration in ms
    distance: int = 135 #distance in feet for the start of radar sensing
    derate: int = 0 #Which derate mode, 0 is slow (default), 1 is fast
    controllerClock: int = 0

class radar(QMainWindow):

    def __init__(self, _port=None):
        super(radar, self).__init__()
        self.dataMsg = dataMSG()
        self._port = _port
        self.x = 0
        self.y = 0
        self.n = 0
        self.currentMode = 1

        self.load_ui()
        self.configureButtons()
        self.configureSliders()

        time.sleep(3)
        self.serialInit()
        self.bus = CAN_TOOL.CAN_TOOL('PCAN')
        timer = pg.QtCore.QTimer(self)
        timer.timeout.connect(self.update)
        timer.start(750)  # number of seconds (every 1000) for next update

        print(_port)
        self.ui.canDialog.setText(self._port)

    def configureButtons(self):
        self.ui.push_mode1.clicked.connect(self.setMode1)
        self.ui.push_mode2.clicked.connect(self.setMode2)
        self.ui.push_mode3.clicked.connect(self.setMode3)
        self.ui.push_mode4.clicked.connect(self.setMode4)

        self.ui.derateSlow.clicked.connect(self.setDerateModeSlow)
        self.ui.derateFast.clicked.connect(self.setDerateModeFast)


    def configureSliders(self):
        self.ui.freqSlider.valueChanged.connect(self.freqSliderChange)
        self.ui.freqSlider.setValue(self.dataMsg.deratePercentage)

        self.ui.periodSlider.valueChanged.connect(self.periodSliderChange)
        self.ui.periodSlider.setValue(self.dataMsg.driveCMD)

        self.ui.distanceSlider.valueChanged.connect(self.distanceSliderChange)
        self.ui.distanceSlider.setValue(self.dataMsg.distance)

        self.ui.freqLabel.setText(str(self.dataMsg.deratePercentage) + '%')
        self.ui.periodLabel.setText(str(self.dataMsg.driveCMD))
        self.ui.distanceLabel.setText(str(np.round(self.dataMsg.distance/30.48,1)) + 'ft')

    def serialInit(self):
        try:
            self.ser = serial.Serial(self._port, 115200, timeout=0.5)
            self.ser.flushInput()
            time.sleep(1)
            self.waitForArduino()
            if self.ser.is_open:
                print("Arduino Ready")
                self.ui.modeDialog.setText("Arduino Ready")
        except Exception as e:
            print(repr(e))

    def waitForArduino(self):
        msg = ""
        while str(msg).find("Arduino is ready") == -1:
            while self.ser.inWaiting() == 0:
                print("inwaiting", end='\r')
#                self.ui.canDialog.setText("inwaiting")
                pass
            msg = self.recvFromArduino()

    def recvFromArduino(self):
        startMarker = 60
        endMarker = 62
    #        global startMarker, endMarker
        ck = b''
        x = "z"

        # wait for the start character
        while ord(x) != startMarker:
            x = self.ser.read()
            # print(ord(x))
#        print("Received Start Char")
    #        self.ui.canDialog.setText("Received Start Char")
        # save data until the end marker is found
        while ord(x) != endMarker:
            if ord(x) != startMarker:
                ck = ck + x
            x = self.ser.read()
#        print("Received End Char")
    #        self.ui.canDialog.setText("Received End Char")

        d = ck.decode('utf-8').split(' ')

        if len(d) == 2:
            x = d[0]
            y = d[1]
            print(d, x, y)
        else:
            x = 0
            y = 0
#        self.ui.canDialog.setText(int(self.x))
#        return(ck, int(self.x), int(self.y))
#        self.ui.modeDialog.setText(str(x) + ' ' + str(y))
        return(ck, x, y)

    def writeSerial(self):
        try:
            serialString = "mode=" + str(self.dataMsg.mode) + ";"
            serialString += "freq=" + str(self.dataMsg.deratePercentage) + ";"
            serialString += "pause=" + str(self.dataMsg.driveCMD) + ";"
            serialString += "distance=" + str(self.dataMsg.distance) + ";"
            serialString += "derate=" + str(self.dataMsg.derate) + ";"
            serialString += "controllerClock=" + str(self.dataMsg.controllerClock) + ";"
#            print(len(bytes(serialString, 'utf-8')))
            self.ser.write(bytes(serialString, 'utf-8'))
            time.sleep(0.2)
#            print("Sent data")
            self.ui.canDialog.setText(str(self.n))

        except Exception as e:
            print(repr(e))

    def readSerial(self):
        global x, y
        try:
            if self.ser.is_open:
                while self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8').rstrip()
                    inputs = line.split("=")
                    if len(inputs) == 2:
                        inputs[1] = inputs[1].strip()
                        if inputs[0] == "mode":
                            self.currentMode = int(inputs[1])
                        elif inputs[0] == "x":
                            self.x = int(inputs[1])
#                            self.x = map(self.x,0,1000,-16,16)
                            #Do nothing
                        elif inputs[0] == "y":
                            self.y = int(inputs[1])
#                            self.y = map(self.y,0,1000,0,20)
                            #Do nothing

            else:
                print("Serial port closed")

            
        except Exception as e:
            print(repr(e))

        x = self.map(self.x, 0, 1000, -16,16);
        y = self.map(self.y, 0, 1000, 0,20);

    def update(self):
        # This is the main update loop, handle your biz in here
        print(self.dataMsg)
        self.readSerial()
        self.writeSerial()
        self.dataMsg.controllerClock = self.n

        self.n += 1
        if self.n > 500:
            self.n = 0

        if self.currentMode == 1:
            self.ui.modeDialog.setText("Derate/Stop")
        elif self.currentMode == 2:
            self.ui.modeDialog.setText("Derate Only")
        elif self.currentMode == 3:
            self.ui.modeDialog.setText("Alert Only")
        elif self.currentMode == 4:
            self.ui.modeDialog.setText("Stop No Alert")
        else:
            self.ui.modeDialog.setText("No Mode")

        driveCMDMSG = [((self.dataMsg.driveCMD >> 8) & 0xFF), (self.dataMsg.driveCMD >> 4), 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
        self.bus.send(0x1CFFBB25, driveCMDMSG)

        time.sleep(0.005)

    def setMode1(self):
        self.dataMsg.mode = 1
        #self.ui.modeDialog.setText("Derate/Stop")
        print('SET MODE1')

    def setMode2(self):
        self.dataMsg.mode = 2
        #self.ui.modeDialog.setText("Derate Only")
        print('SET MODE2')

    def setMode3(self):
        self.dataMsg.mode = 3
        #self.ui.modeDialog.setText("Alert Only")
        print('SET MODE3')

    def setMode4(self):
        self.dataMsg.mode = 4
        #self.ui.modeDialog.setText("Derate No Alert")
        print('SET MODE4')

    def setDerateModeSlow(self):
        self.dataMsg.derate = 0

    def setDerateModeFast(self):
        self.dataMsg.derate = 1

    def load_ui(self):

        ui_file_name = "form.ui"
        ui_file = QFile(ui_file_name)
        if not ui_file.open(QIODevice.ReadOnly):
            print(f"Cannot open {ui_file_name}: {ui_file.errorString()}")
            sys.exit(-1)
        loader = QUiLoader()
        loader.registerCustomWidget(CustomWidget)
        self.ui = loader.load(ui_file)
        ui_file.close()
        if not self.ui:
            print(loader.errorString())
            sys.exit(-1)

        if platform == "linux" or platform == "linux2":
            # linux
            self.ui.showFullScreen()
        elif platform == "win32":
            self.ui.showMaximized()

        shutdown = QAction("Shutdown", self)
        self.ui.menuIP.addAction(shutdown)
        self.ui.menuIP.triggered.connect(self.shutdownTrigger)

        quit = QAction("Quit", self)
        self.ui.menuFile.addAction(quit)
        self.ui.menuFile.triggered.connect(self.processtrigger)
#        self.ui.menuFile.triggered[QAction].connect(self.processtrigger)
        self.IPstr = self.getIP()
        self.ui.menuIP.setTitle(self.IPstr)

    def updateLabel(self, value):

        self.label.setText(str(value))

    def getIP(self):
        if platform == "linux" or platform == "linux2":
            # linux
            IP = os.popen('hostname -I').read()
            IP = IP.split(' ')[0]
            IPstr = '&' + IP

        elif platform == "win32":
            import socket
            hostname = socket.gethostname()
            IP = socket.gethostbyname(hostname)
            IPstr = '&' + IP

        return IPstr

    def freqSliderChange(self):
        updatedValue = self.ui.freqSlider.value()
        self.dataMsg.deratePercentage = updatedValue
        self.ui.freqLabel.setText(str(updatedValue) + 'Hz')

    def periodSliderChange(self):
        updatedValue = self.ui.periodSlider.value()
        self.dataMsg.driveCMD = updatedValue
        self.ui.periodLabel.setText(str(updatedValue))

    def distanceSliderChange(self):
        updatedValue = self.ui.distanceSlider.value()
        self.dataMsg.distance = updatedValue
        updatedValue = np.round(updatedValue/30.48, 1)
        self.ui.distanceLabel.setText(str(updatedValue) + 'ft')

    def shutdownTrigger(self):
        os.system("shutdown now")
        print("Should Shutdown")

    def processtrigger(self):
        sys.exit()

    def serial_close(self):
        if self.ser.open:
            self.ser.close()

    def map(self, x, in_min, in_max, out_min, out_max):
        return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)


class CustomWidget(pg.GraphicsWindow):

    pg.setConfigOption('background', 'k')
    pg.setConfigOption('foreground', 'k')
    ptr1 = 0

    def __init__(self, parent=radar, **kargs):
        pg.GraphicsWindow.__init__(self, **kargs)
        self.setParent(parent)

        self.p1 = self.addPlot()  # labels = {'left':'Voltage','bottom':'Time'}
        self.p1.setAspectLocked()
        self.p1.setMouseEnabled(x=False,y=False)

        self.p1.setXRange(-20, 20, 0.001)
        self.p1.setYRange(0, 20, 0.001)

        timer = pg.QtCore.QTimer(self)
        timer.timeout.connect(self.update)
        timer.start(750)  # number of seconds (every 1000) for next update

    def update(self):
        global x, y
        """
        MAIN UPDATE FUNCTION FOR PLOT:
        This is a dumbass way to do it,
        redrawing the entire circles and lines each pass,
        couldnt figure it out otherwise.
        """
        self._x = x
        self._y = y

        print(self._x,self._y)
        try:
            self.p1.plot([self._x], [self._y], clear=True,pen=pg.mkPen('y'), symbol='s')
        except Exception as e:
            print(repr(e))

        self.p1.addLine(x=0, pen=0.2)
        self.p1.addLine(y=0, pen=0.2)
        for r in range(2, 24, 2):
            circle = pg.QtGui.QGraphicsEllipseItem(-r, -r, r * 2, r * 2)
            circle.setPen(pg.mkPen(0.2))
            self.p1.addItem(circle)

        # Create Left Boundary Line
        x = [-5, -16]
        y = [0, 16]
        self.p1.plot(x, y)

        # Create Right Boundary Line
        x = [5, 16]
        y = [0, 16]
        self.p1.plot(x, y)


if __name__ == "__main__":
    app = QApplication([])
    from sys import platform
    if platform == "linux" or platform == "linux2":
        # linux
        widget = radar('/dev/ttyACM0')
    elif platform == "win32":
        widget = radar('COM5')
    elif platform == "Darwin":
        widget = radar('/dev/disk4')

    sys.exit(app.exec_())
    widget.serial_close()
