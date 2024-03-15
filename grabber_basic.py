from videograbber import VideoGrabber
import cv2
import numpy as np

class GrabberBasic(VideoGrabber):
    def __init__(self, key, c_width, c_height):
        super().__init__(key, True, c_width, c_height)

    def preProc(self):
        print('init Basic Cam!!')


