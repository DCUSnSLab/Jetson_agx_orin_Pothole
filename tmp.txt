#!/usr/bin/env python
import os
import sys
import shutil as su
import subprocess
import cv2
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QRectF, QTimer
from PyQt5.QtGui import *
import signal

# 모니터 해상도 1920 * 1080 (100%) 고정
CAM_WIDTH = int(1920)
CAM_HEIGHT = int(1080)
# 미리보기 해상도 1280 * 720 (66.6%) 고정
PREVIEW_WIDTH = int(1280)
PREVIEW_HEIGHT = int(720)
PREVIEW_SCALE = float(2 / 3)

ROI_WIDTH = int(1024 * PREVIEW_SCALE)
ROI_HEIGHT = int(512 * PREVIEW_SCALE)

FROM_PATH = "./Result"

class MyMainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.child_process = None
        self.to_path = ".."
        self.data_list = []
        self.clk_x = int(30 + float(PREVIEW_WIDTH / 2) - float(ROI_WIDTH / 2))
        self.clk_y = int(30 + float(PREVIEW_HEIGHT / 2) - float(ROI_HEIGHT / 2))

        self.top_list = [QPushButton("UP-DOWN REVERSE"), QPushButton("SHUTDOWN COMPUTER")]
        self.top_list[0].clicked.connect(self.click_reverse)
        self.coord_label = QLabel("p1(x, y) : (" + str(self.clk_x) + ", " + str(self.clk_y) + ")", self)
        self.top_list[1].clicked.connect(self.click_shutdown)

        self.btn_list = [QPushButton("START"), QPushButton("STOP"), QPushButton("DOWNLOAD")]
        self.btn_list[0].clicked.connect(self.click_start)
        self.btn_list[1].clicked.connect(self.click_stop)
        self.btn_list[2].clicked.connect(self.click_download)

        self.select_btn = QPushButton("SELECT")
        self.select_btn.clicked.connect(self.click_select)
        self.info_layout = QHBoxLayout()
        self.info_layout.addWidget(QLabel("Path to Download Data Files to"))
        self.info_layout.addWidget(self.select_btn)
        self.path_label = QLabel()
        self.path_label.setWindowFilePath(self.to_path)
        self.download_layout = QVBoxLayout()
        self.download_layout.addLayout(self.info_layout, 1)
        self.download_layout.addWidget(self.path_label, 1)

        # 크기 정책 설정
        for btn in self.top_list + self.btn_list + [self.select_btn]:
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.init_UI()

    def init_UI(self):
        self.top_layout = QHBoxLayout()
        self.top_layout.addWidget(self.top_list[0], 1)
        self.top_layout.addWidget(self.coord_label, 2)
        self.top_layout.addWidget(self.top_list[1], 1)

        self.cam_preview = QLabel()
        self.cam_preview.setGeometry(320, 200, PREVIEW_WIDTH, PREVIEW_HEIGHT)
        self.installEventFilter(self)
        timer = QTimer(self)
        timer.timeout.connect(self.update_frame)
        timer.start(10)
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(Qt.transparent)
        self.view = QGraphicsView(self.scene)
        self.view.setStyleSheet("background: transparent;")
        self.view.setSceneRect(0, 0, PREVIEW_WIDTH, PREVIEW_HEIGHT)
        self.view.setGeometry(320, 200, PREVIEW_WIDTH, PREVIEW_HEIGHT)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.roi_box = QGraphicsRectItem(QRectF(int(320 + float(PREVIEW_WIDTH / 2) - float(ROI_WIDTH / 2)), int(30 + float(PREVIEW_HEIGHT / 2) - float(ROI_HEIGHT / 2)), ROI_WIDTH, ROI_HEIGHT))
        self.roi_box.setBrush(QBrush(Qt.transparent))
        self.roi_box.setPen(QPen(Qt.green, 10, Qt.SolidLine))
        self.scene.addItem(self.roi_box)
        self.is_it_reversed = int(0)

        self.btn_layout = QHBoxLayout()
        self.btn_layout.addWidget(self.btn_list[0], 1)
        self.btn_layout.addWidget(self.btn_list[1], 1)
        self.btn_layout.addWidget(self.btn_list[2], 1)
        self.btn_layout.addLayout(self.download_layout, 4)

        self.main_layout = QVBoxLayout()
        self.main_layout.addLayout(self.top_layout, 1)
        self.main_layout.addWidget(self.cam_preview, 10)
        self.main_layout.addLayout(self.btn_layout, 1)

        self.setLayout(self.main_layout)
        self.setWindowTitle("POTHOLE DETECTION")
        self.setFont(QFont("Arial", 11))
        self.showMaximized()

    def click_reverse(self):
        print()
    def click_shutdown(self):
        print()
    def click_start(self):
        print()
    def click_stop(self):
        print()
    def click_download(self):
        print()
    def click_select(self):
        print()
    def update_frame(self):
        ret, frame = self.capture.read()  # 카메라에서 프레임을 읽습니다.
        if ret:
            # OpenCV의 BGR 이미지를 PyQt에서 표시 가능한 RGB 이미지로 변환합니다.
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if self.is_it_reversed == 1:
                frame_rgb = cv2.flip(frame_rgb, 0)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            q_img = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            # q_img.scaledToWidth(PREVIEW_WIDTH)
            # q_img.scaledToHeight(PREVIEW_HEIGHT)
            # QLabel에 이미지를 표시합니다.
            pixmap = QPixmap.fromImage(q_img)
            pixmap = pixmap.scaled(self.cam_preview.size())
            self.cam_preview.setPixmap(pixmap)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MyMainWindow()
    sys.exit(app.exec_())