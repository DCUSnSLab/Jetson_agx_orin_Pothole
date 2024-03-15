import sys
import time
from PyQt5.QtCore import QThread, pyqtSignal
import cv2
from time import sleep
import numpy as np

class VideoGrabber(QThread):
    grabber_signal = pyqtSignal(np.ndarray)
    def __init__(self, key, useCam=False, c_width=1920, c_height=1080):
        super().__init__()
        self.key = key
        self.isGrab = False
        self.useCam = useCam
        self.cap = None
        self.c_width = c_width
        self.c_height = c_height

    def run(self):
        self.preProc()
        if self.useCam is True:
            while True:
                if self.isGrab is True:
                    try:
                        ret, cv_img = self.cap.read()
                        if ret:
                            self.grabber_signal.emit(cv_img)
                    except Exception as e:
                        print('Exception', e)
                        #print('cvimage type error : ', type(cv_img), file=sys.stderr)
                else:
                    sleep(0.1)
                    continue
        else:
            self.runProc()

    def preProc(self):
        pass
    def runProc(self):
        pass

    def setGrab(self):
        if self.useCam is True and self.isGrab is False:
            self.setCamUsage(True)

        self.isGrab = True

    def releaseGrab(self):
        self.isGrab = False
        if self.useCam is True and self.isGrab is False:
            self.setCamUsage(False)


    def setCamUsage(self, isbool):
        if isbool is True:
            print('set CAM')
            time.sleep(3)
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.c_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.c_height)
        else:
            print('relase CAM')
            self.cap.release()
