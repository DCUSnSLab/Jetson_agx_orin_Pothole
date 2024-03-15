from time import sleep

from videograbber import VideoGrabber
from numpysocket import NumpySocket

class GrabberServer(VideoGrabber):
    def __init__(self, key):
        super().__init__(key, False)

    def preProc(self):
        print('init Process Server Cam!!')

    def runProc(self):
        with NumpySocket() as s:
            s.bind(("", 9999))

            while True:
                try:
                    s.listen()
                    conn, addr = s.accept()

                    #logger.info(f"connected: {addr}")
                    print('connected.',addr)
                    while conn:
                        frame = conn.recv()
                        if len(frame) == 0:
                            break

                        if self.isGrab is True:
                            print('server - send data')
                            self.grabber_signal.emit(frame)
                    #logger.info(f"disconnected: {addr}")
                    print('disconnected: ',addr)
                except ConnectionResetError:
                    pass
