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
CAM_SCALE = float(3 / 2)
# 미리보기 해상도 1280 * 720 (66.6%) 고정
PREVIEW_WIDTH = int(1280)
PREVIEW_HEIGHT = int(720)
PREVIEW_SCALE = float(2 / 3)

ROI_WIDTH = int(1024 * PREVIEW_SCALE)
ROI_HEIGHT = int(512 * PREVIEW_SCALE)

WIDGET_HEIGHT = int(60)
WIDGET_MARGIN = int(15)
FLIP = 0
START = 1
STOP = 2
SELECT = 3
DOWN = 4
SHUTDOWN = 5

FROM_PATH = "./Result"

class MyMainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.child_process = None
        self.child_pid = None
        self.to_path = ".."
        self.data_list = []
        self.is_it_reversed = 0

        self.btn_list = [QPushButton("HORIZONTAL FLIP", self),
                         QPushButton("START", self), QPushButton("STOP", self),
                         QPushButton("SELECT PATH", self), QPushButton("DOWNLOAD", self),
                         QPushButton("SHUTDOWN", self)]
        self.btn_list[0].clicked.connect(self.click_flip)
        self.btn_list[1].clicked.connect(self.click_start)
        self.btn_list[1].setStyleSheet("background-color: white; color: black; font-size: 20px; font-weight: bold;")
        self.btn_list[2].clicked.connect(self.click_stop)
        self.btn_list[2].setEnabled(False)  # STOP 버튼 비활성화
        self.btn_list[2].setStyleSheet("background-color: red; color: black; font-size: 20px; font-weight: bold;")
        self.btn_list[3].clicked.connect(self.click_select)
        self.btn_list[4].clicked.connect(self.click_download)
        self.btn_list[4].setStyleSheet("background-color: #686868; color: white; font-size: 20px; font-weight: bold;")
        self.btn_list[5].clicked.connect(self.click_shutdown)

        self.label_list = [QLabel("> ROI Box Coordinates: (   \t\t, \t\t   )", self),
                           QLabel("> Path to Download Data Files to", self)]
        self.x_info = QLineEdit("", self)
        self.x_info.setReadOnly(True)
        self.y_info = QLineEdit("", self)
        self.y_info.setReadOnly(True)
        self.path_info = QLineEdit("", self)
        self.path_info.setReadOnly(True)

        self.init_UI()
    def init_UI(self):
        self.img_label = QLabel(self)
        self.img_label.setGeometry(0, 0, 1280, 720)
        self.img_label.installEventFilter(self)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(10)
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(Qt.transparent)  # 배경을 투명하게 설정
        self.view = QGraphicsView(self.scene, self)
        self.view.setStyleSheet("background: transparent;")  # 배경을 투명하게 설정
        self.view.setSceneRect(0, 0, PREVIEW_WIDTH, PREVIEW_HEIGHT)
        self.view.setGeometry(0, 0, PREVIEW_WIDTH, PREVIEW_HEIGHT)
        self.view.setFixedSize(PREVIEW_WIDTH, PREVIEW_HEIGHT)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.clk_x = int((PREVIEW_WIDTH - ROI_WIDTH) / 2)
        self.clk_y = int(PREVIEW_HEIGHT - ROI_HEIGHT)
        self.roi_box = QGraphicsRectItem(QRectF(self.clk_x, self.clk_y, ROI_WIDTH, ROI_HEIGHT))
        self.roi_box.setBrush(QBrush(Qt.transparent))
        self.roi_box.setPen(QPen(Qt.green, 10, Qt.SolidLine))
        self.roi_coord = [int(self.clk_x * CAM_SCALE), int(self.clk_y * CAM_SCALE)]
        self.scene.addItem(self.roi_box)

        self.x_info.setText(str(self.clk_x))
        self.y_info.setText(str(self.clk_y))
        self.path_info.setText(str(os.path.abspath(self.to_path)))

        self.label_list[0].setGeometry(1320, 20, 480, WIDGET_HEIGHT)
        self.x_info.setGeometry(1320 + 180, 30, 100, WIDGET_HEIGHT - 20)
        self.y_info.setGeometry(1320 + 320, 30, 100, WIDGET_HEIGHT - 20)
        self.btn_list[0].setGeometry(1320, 20 + (WIDGET_HEIGHT + WIDGET_MARGIN) * 1, 480, WIDGET_HEIGHT)
        self.btn_list[1].setGeometry(1320, 20 + (WIDGET_HEIGHT + WIDGET_MARGIN) * 2, 235, WIDGET_HEIGHT * 2)
        self.btn_list[2].setGeometry(1320 + 245, 20 + (WIDGET_HEIGHT + WIDGET_MARGIN) * 2, 235, WIDGET_HEIGHT * 2)
        self.label_list[1].setGeometry(1320, 20 + (WIDGET_HEIGHT + WIDGET_MARGIN) * 3 + WIDGET_HEIGHT, 480, WIDGET_HEIGHT)
        self.path_info.setGeometry(1320, 20 + (WIDGET_HEIGHT + WIDGET_MARGIN) * 4 + WIDGET_HEIGHT, 480, WIDGET_HEIGHT - 20)
        self.btn_list[3].setGeometry(1320, 20 + (WIDGET_HEIGHT + WIDGET_MARGIN) * 5 + WIDGET_HEIGHT, 480, WIDGET_HEIGHT)
        self.btn_list[4].setGeometry(1320, 20 + (WIDGET_HEIGHT + WIDGET_MARGIN) * 6 + WIDGET_HEIGHT, 480, WIDGET_HEIGHT * 2)
        self.btn_list[5].setGeometry(1320, 20 + (WIDGET_HEIGHT + WIDGET_MARGIN) * 7 + (WIDGET_HEIGHT) * 2, 480, WIDGET_HEIGHT)

        self.logo = QLabel(self)
        self.logo.setGeometry(int((1920 - int(1920 * 0.6)) / 2), 980 - int(350 * 0.6), int(1920 * 0.6), int(350 * 0.6))
        self.logo.setPixmap(QPixmap.fromImage(QImage("logo.png").scaled(self.logo.size())))

        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowTitle("POTHOLE DETECTION")
        self.setFont(QFont("Arial", 11))
        self.showMaximized()
    def click_flip(self):
        if self.is_it_reversed == 1:
            self.is_it_reversed = 0
        elif self.is_it_reversed == 0:
            self.is_it_reversed = 1
    def click_start(self):
        # 좌표는 1920 * 1080 사이즈에 맞게 좌표 보정되어 self.roi_coord 리스트에 저장되므로, 따로 보정할 필요 없음.
        # self.roi_coord[0]이 x 좌표, self.roi_coord[1]이 y 좌표임.
        # self.is_it_reversed 변수는 정수 형태의 이진 변수로, 1이면 상하반전된 상태, 0이면 정방향 상태임.
        # 자식 프로세스는 매개변수로 x/y좌표, 상하반전여부를 받아가야 함. 자식 프로세스에서 실행할 스크립트에 맞게 매개변수 작성할 것.
        self.timer.stop()
        self.capture.release()
        command = ["python3", "./test/segnet-camera_last_last.py", "--network=fcn-resnet18-cityscapes-1024x512",
                   f"--x_coord={str(self.roi_coord[0])}", f"--y_coord={str(self.roi_coord[1])}",
                   f"--reversed={str(self.is_it_reversed)}"]
        self.child_process = subprocess.Popen(command)
        self.child_pid = self.child_process.pid

        self.img_label.setVisible(False)
        self.roi_box.setVisible(False)
        self.btn_list[START].setEnabled(False)
        self.btn_list[STOP].setEnabled(True)
    def click_stop(self):
        self.timer.start(10)
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
        if self.child_pid:
            os.kill(self.child_pid, signal.SIGTERM)
        else:
            print("Child process PID not available")
        self.img_label.setVisible(True)
        self.roi_box.setVisible(True)
        self.btn_list[START].setEnabled(True)
        self.btn_list[STOP].setEnabled(False)
    def click_select(self):
        self.timer.stop()
        self.capture.release()
        self.to_path = QFileDialog.getExistingDirectory(None, "USB-Path to COPY(MOVE) Data File", ".")
        self.path_info.setText(self.to_path)
        self.timer.start(10)
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
    def click_download(self):
        self.timer.stop()
        self.capture.release()
        self.data_list = []
        for file in os.listdir(FROM_PATH + "/Excel"):
            if file.endswith(".xls") or file.endswith(".xlsx"):
                self.data_list.append(file)
        download_window = DownloadWindow(self.data_list, self.to_path)
        if download_window.exec_() == QDialog.Accepted:
            self.timer.start(10)
            self.capture = cv2.VideoCapture(0)
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
        else:
            self.timer.start(10)
            self.capture = cv2.VideoCapture(0)
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
    def click_shutdown(self):
        if self.child_pid:
            os.kill(self.child_pid, signal.SIGTERM)
            QMessageBox.about(self, "Notice", "Script is killed.\nExit GUI program and shut down the computer.")
        else:
            print("Child process PID not available")
            QMessageBox.about(self, "Notice", "No script to kill.\nExit GUI program and shut down the computer.")
        self.timer.stop()
        self.capture.release()
        # tmp = input("SHUTDOWN?")
        os.system("shutdown -h now")
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
            self.img_label.setPixmap(QPixmap.fromImage(q_img))
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.img_label.geometry().contains(event.pos()):
                if event.pos().x() > 1280 - ROI_WIDTH and event.pos().y() > 720 - ROI_HEIGHT:
                    self.clk_x = 1280 - ROI_WIDTH
                    self.clk_y = 720 - ROI_HEIGHT
                elif event.pos().x() > 1280 - ROI_WIDTH and not event.pos().y() > 720 - ROI_HEIGHT:
                    self.clk_x = 1280 - ROI_WIDTH
                    self.clk_y = event.pos().y()
                elif not event.pos().x() > 1280 - ROI_WIDTH and event.pos().y() > 720 - ROI_HEIGHT:
                    self.clk_x = event.pos().x()
                    self.clk_y = 720 - ROI_HEIGHT
                else:
                    self.clk_x = event.pos().x()
                    self.clk_y = event.pos().y()
                self.scene.removeItem(self.roi_box)
                self.roi_box = QGraphicsRectItem(QRectF(self.clk_x, self.clk_y, ROI_WIDTH, ROI_HEIGHT))
                self.roi_box.setBrush(QBrush(Qt.transparent))
                self.roi_box.setPen(QPen(Qt.green, 10, Qt.SolidLine))
                self.scene.addItem(self.roi_box)
                self.roi_coord = [int(self.clk_x * CAM_SCALE), int(self.clk_y * CAM_SCALE)]
                self.x_info.setText(str(self.roi_coord[0]))
                self.y_info.setText(str(self.roi_coord[1]))
                self.update()
                super().mousePressEvent(event)
class DownloadWindow(QDialog):
    def __init__(self, data_list: list, to_path: str):
        super().__init__()
        self.checked_num = int(0)
        self.data_list = data_list
        self.to_path = to_path
        print(to_path)
        self.init_UI()
    def init_UI(self):
        self.data_model = QStandardItemModel()
        self.data_model.setColumnCount(1)
        self.data_model.setHorizontalHeaderLabels(["Select", "File Name"])
        for file in self.data_list:
            item = QStandardItem(file)
            item.setCheckable(True)
            self.data_model.appendRow(item)

        self.select_all_btn = QPushButton("Select All", self)
        self.select_all_btn.clicked.connect(self.select_all)
        self.refresh_btn = QPushButton("REFRESH", self)
        self.refresh_btn.clicked.connect(self.refresh_list)
        self.tool_layout = QHBoxLayout()
        self.tool_layout.addWidget(self.select_all_btn)
        self.tool_layout.addWidget(self.refresh_btn)

        self.copy_btn = QPushButton("COPY", self)
        self.copy_btn.clicked.connect(self.click_copy)
        self.move_btn = QPushButton("MOVE", self)
        self.move_btn.clicked.connect(self.click_move)
        self.delete_btn = QPushButton("DELETE", self)
        self.delete_btn.clicked.connect(self.click_delete)
        self.finish_btn = QPushButton("FINISH", self)
        self.finish_btn.clicked.connect(self.click_finish)

        self.btn_layout = QHBoxLayout()
        self.btn_layout.addWidget(self.copy_btn)
        self.btn_layout.addWidget(self.move_btn)
        self.btn_layout.addWidget(self.delete_btn)
        self.btn_layout.addWidget(self.finish_btn)

        self.list_view = QListView()
        self.list_view.setModel(self.data_model)

        main_layout = QVBoxLayout(self)
        # main_layout.addWidget(QLabel(self.from_path.split('/')[-1] + " -> " + self.to_path.split('/')[-1]))
        main_layout.addLayout(self.tool_layout)
        main_layout.addWidget(self.list_view)
        main_layout.addLayout(self.btn_layout)

        self.setLayout(main_layout)
        self.setWindowTitle("COPY or MOVE DATA FILES to USB")
        self.setFixedSize(1800, 1000)
        self.setFont(QFont("Arial", 10))
        self.show()
    def set_window_center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    def count_checks(self):
        for i in range(len(self.data_list)):
            if self.data_model.item(i, 0).checkState() == 2:
                self.checked_num += 1
    def lock_buttons(self):
        self.copy_btn.setEnabled(False)
        self.move_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.select_all_btn.setEnabled(False)
        self.finish_btn.setEnabled(False)
    def unlock_buttons(self):
        self.copy_btn.setEnabled(True)
        self.move_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.select_all_btn.setEnabled(True)
        self.finish_btn.setEnabled(True)
    def click_copy(self):
        self.count_checks()
        self.lock_buttons()
        for i in range(len(self.data_list)):
            if self.data_model.item(i, 0).checkState() == 2:
                try:
                    su.copy(os.path.join(FROM_PATH + "/Excel", self.data_model.item(i, 0).text()), os.path.join(self.to_path, self.data_model.item(i, 0).text()))
                except FileNotFoundError:
                    QMessageBox.about(self, "Error !", "File {0} not found.\nProceed to next task without copying this file.".format(self.data_model.item(i, 0).text()))
                    print("File not found")
                except Exception as e:
                    QMessageBox.about(self, "Error !", "An error occurred while copying file {0}.\nProceed to next task without copying this file.".format(self.data_model.item(i, 0).text()))
                    print("An error occurred", e)
                except PermissionError:
                    QMessageBox.about(self, "Error !", "Permission denied!\nProceed to next task without copying this file.")
                    print("Permission denied !")
                try:
                    su.copytree(FROM_PATH + "/full_frame_detect/" + self.data_model.item(i, 0).text().split('.')[0], self.to_path + "/" + self.data_model.item(i, 0).text().split('.')[0])
                except FileNotFoundError:
                    QMessageBox.about(self, "Error !", "Directory {0} not found.\nProceed to next task without copying directory connected this file.".format(self.data_model.item(i, 0).text().split('.')[0]))
                    print("Directory not found")
                except Exception as e:
                    QMessageBox.about(self, "Error !", "An error occurred while copying directory {0}.\nProceed to next task without copying this directory.".format(self.data_model.item(i, 0).text().split('.')[0]))
                    print("An error occurred", e)
                except PermissionError:
                    QMessageBox.about(self, "Error !", "Permission denied!\nProceed to next task without copying directory connected this file.")
                    print("Permission denied !")
        self.unlock_buttons()
        QMessageBox.about(self, "Copy", "Finished!")
    def click_move(self):
        self.count_checks()
        self.lock_buttons()
        for i in range(len(self.data_list)):
            if self.data_model.item(i, 0).checkState() == 2:
                try:
                    su.move(os.path.join(FROM_PATH + "/Excel", self.data_model.item(i, 0).text()), os.path.join(self.to_path, self.data_model.item(i, 0).text()))
                except FileNotFoundError:
                    QMessageBox.about(self, "Error !", "File {0} not found.\nProceed to next task without moving this file.".format(self.data_model.item(i, 0).text()))
                    print("File not found")
                except Exception as e:
                    QMessageBox.about(self, "Error !", "An error occurred while moving file {0}.\nProceed to next task without moving this file.".format(self.data_model.item(i, 0).text()))
                    print("An error occurred", e)
                except PermissionError:
                    QMessageBox.about(self, "Error !", "Permission denied!\nProceed to next task without moving this file.")
                    print("Permission denied !")
                try:
                    su.move(FROM_PATH + "/full_frame_detect/" + self.data_model.item(i, 0).text().split('.')[0], self.to_path + "/" + self.data_model.item(i, 0).text().split('.')[0])
                except FileNotFoundError:
                    QMessageBox.about(self, "Error !", "Directory {0} not found.\nProceed to next task without moving directory connected this file.".format(self.data_model.item(i, 0).text().split('.')[0]))
                    print("Directory not found")
                except Exception as e:
                    QMessageBox.about(self, "Error !", "An error occurred while moving directory {0}.\nProceed to next task without moving this directory.".format(self.data_model.item(i, 0).text().split('.')[0]))
                    print("An error occurred", e)
                except PermissionError:
                    QMessageBox.about(self, "Error !", "Permission denied!\nProceed to next task without moving directory connected this file.")
                    print("Permission denied !")
        self.unlock_buttons()
        self.refresh_list() # 파일 목록을 새로고침합니다.
        QMessageBox.about(self, "Move", "Finished!")
    def click_delete(self):
        self.count_checks()
        self.lock_buttons()
        for i in range(len(self.data_list)):
            if self.data_model.item(i, 0).checkState() == 2:
                try:
                    os.remove(os.path.join(FROM_PATH + "/Excel", self.data_model.item(i, 0).text()))
                except FileNotFoundError:
                    QMessageBox.about(self, "Error !", "File {0} not found.\nProceed to next task without deleting this file.".format(self.data_model.item(i, 0).text()))
                    print("File not found")
                except Exception as e:
                    QMessageBox.about(self, "Error !", "An error occurred while deleting file {0}.\nProceed to next task without deleting this file.".format(self.data_model.item(i, 0).text()))
                    print("An error occurred", e)
                except PermissionError:
                    QMessageBox.about(self, "Error !", "Permission denied!\nProceed to next task without deleting this file.")
                    print("Permission denied !")
                try:
                    su.rmtree(FROM_PATH + "/full_frame_detect/" + self.data_model.item(i, 0).text().split('.')[0])
                except FileNotFoundError:
                    QMessageBox.about(self, "Error !", "Directory {0} not found.\nProceed to next task without deleting directory connected this file.".format(self.data_model.item(i, 0).text().split('.')[0]))
                    print("Directory not found")
                except Exception as e:
                    QMessageBox.about(self, "Error !", "An error occurred while deleting directory {0}.\nProceed to next task without deleting this directory.".format(self.data_model.item(i, 0).text().split('.')[0]))
                    print("An error occurred", e)
                except PermissionError:
                    QMessageBox.about(self, "Error !", "Permission denied!\nProceed to next task without deleting directory connected this file.")
                    print("Permission denied !")
        self.unlock_buttons()
        self.refresh_list()  # 파일 목록을 새로고침합니다.
        QMessageBox.about(self, "Delete", "Finished!")
    def click_finish(self):
        self.accept()
    def select_all(self):
        for i in range(len(self.data_list)):
            self.data_model.item(i, 0).setCheckState(Qt.Checked)
    def refresh_list(self):
        self.get_data_files()
        self.data_model.clear()
        for file in self.data_list:
            item = QStandardItem(file)
            item.setCheckable(True)
            self.data_model.appendRow(item)
    def get_data_files(self):
        self.data_list = []
        for file in os.listdir(FROM_PATH + "/Excel"):
            if file.endswith(".xls") or file.endswith(".xlsx"):
                self.data_list.append(file)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MyMainWindow()
    sys.exit(app.exec_())
