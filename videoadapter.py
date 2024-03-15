import numpy as np
from PyQt5.QtCore import pyqtSignal, QObject


class VideoAdapter(QObject):
    changed_pixmap_sig = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.grabbers = dict()
        self.activeKey = None

    def runAdapter(self):
        for gr in self.grabbers.values():
            gr.grabber_signal.connect(self.execute)
            gr.start()

    def execute(self, data):
            self.changed_pixmap_sig.emit(data)

    def addVideoGrabber(self, grabber):
        if not grabber.key in self.grabbers:
            self.grabbers[grabber.key] = grabber

            if self.activeKey is None:
                self.activeGrabber(grabber.key)


    def activeGrabber(self, key):
        if self.activeKey is not key:
            if self.activeKey is not None:
                prevgr = self.grabbers[self.activeKey]
                prevgr.releaseGrab()
            self.activeKey = key
            gr = self.grabbers[self.activeKey]
            gr.setGrab()
