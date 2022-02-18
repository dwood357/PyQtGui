class CustomWidget(pg.GraphicsWindow):
#class CustomWidget(QMainWindow):

#    pg.setConfigOption('background', 'k')
#    pg.setConfigOption('foreground', 'd')
    ptr1 = 0
    def __init__(self, parent=None, **kargs):
        pg.GraphicsWindow.__init__(self, **kargs)
        self.setParent(parent)

        self.setWindowTitle('pyqtgraph example: Scrolling Plots')
        p1 = self.addPlot(labels =  {'left':'Voltage', 'bottom':'Time'})
#        p1.setAspectLocked()
#        self.data1 = np.random.normal(size=10)
#        self.data2 = np.random.normal(size=10)
#        self.curve1 = p1.plot(self.data1, pen=(3,3))
#        self.curve2 = p1.plot(self.data2, pen=(2,3))

        for r in range(2, 20, 2):
            circle = pg.QtGui.QGraphicsEllipseItem(-r, -r, r * 2, r * 2)
            circle.setPen(pg.mkPen(0.2))
            self.p1.addItem(circle)

#        timer = pg.QtCore.QTimer(self)
#        timer.timeout.connect(self.update)
#        timer.start(2000) # number of seconds (every 1000) for next update

    def update(self):
        self.data1[:-1] = self.data1[1:]  # shift data in the array one sample left
                            # (see also: np.roll)
        self.data1[-1] = np.random.normal()
        self.ptr1 += 1
        self.curve1.setData(self.data1)
        self.curve1.setPos(self.ptr1, 0)
        self.data2[:-1] = self.data2[1:]  # shift data in the array one sample left
                            # (see also: np.roll)
        self.data2[-1] = np.random.normal()
        self.curve2.setData(self.data2)
        self.curve2.setPos(self.ptr1,0)

#    def plotFunc(self):
##        self.plot = pg.plot()
##        self.plot.setAspectLocked()
#        self.graphWidget.plot.setAspectLocked()

#        # Add polar grid lines
#        self.graphWidget.plot.addLine(x=0, pen=0.2)
#        self.graphWidget.plot.addLine(y=0, pen=0.2)
#        for r in range(2, 20, 2):
#            circle = pg.QtGui.QGraphicsEllipseItem(-r, -r, r * 2, r * 2)
#            circle.setPen(pg.mkPen(0.2))
#            self.graphWidget.plot.addItem(circle)

#        # make polar data
#        theta = np.linspace(135*np.pi/180, np.pi/4, 100)
#        radius = np.random.normal(loc=15, size=100)

#        x = [0,-20]
#        y = [0,20]
#        self.graphWidget.plot(x,y)

if __name__ == '__main__':
    w = CustomWidget()
    w.show()
    QtGui.QApplication.instance().exec_()
