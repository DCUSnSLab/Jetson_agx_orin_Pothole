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

# ROI 영역 지정에 사용되는 카메라의 해상도입니다. 이 비율에 맞게 ROI 영역의 좌표가 보정됩니다.
# 기본 해상도는 1920 * 1080 (100%)입니다. 사용하는 모니터의 비율보다 한 단계 낮게 설정해주세요.
# 1920 * 1080 (1.0)
# 1280 * 720 (0.66)
# 960 * 540 (0.5)
CAM_WIDTH = int(1280)   # 1920 / 1280 / 960
CAM_HEIGHT = int(720)  # 1080 / 720 / 540
CAM_SCALE = float(2 / 3)  # 1.0 / 3분의2 / 0.5

# Excel/탐지 프레임(JPG) 데이터 파일들이 저장되어있는 경로입니다. 선택창 없이 코드 수정으로 변경합니다.
# 끝은 반드시 디렉토리여야 하며, 맨끝에 슬래시 붙이지 않습니다. 사용할 때 주의하시길 바랍니다.
FROM_PATH = "./Result"

# 수정할 필요없이 자동으로 정의되는 상수입니다.
ROI_WIDTH = int(1024 * CAM_SCALE)
ROI_HEIGHT = int(512 * CAM_SCALE)
ROI_SCALE = float(CAM_SCALE ** -1)

class MyMainWindow(QWidget):
    def __init__(self):
        super().__init__()
        # 스크립트 파일을 실행시킬 자식 프로세스입니다.
        self.child_process = None
        # 스크립트 파일에 매개변수(parameter)로 들어갈 변수 리스트입니다.
        self.script_param = []

        self.to_path = ".."         # 데이터 파일을 복사/이동할 USB의 경로입니다. 파일 선택창에서 선택하며, Excel 파일과 탐지 프레임(JPG) 디렉토리가 해당 경로로 옮겨집니다.
        self.data_list = []

        self.btn_list = [QPushButton("START"), QPushButton("STOP"), QPushButton("DOWNLOAD")]
        for btn in self.btn_list:
            btn.setMaximumWidth(250)
            btn.setMaximumHeight(150)
        self.btn_list[1].setStyleSheet("background-color: red; color: white")
        self.btn_list[2].setStyleSheet("background-color: black; color: white")

        # 스크립트를 실행시키는 역할입니다.
        # ROI 위치를 설정하는 GUI창이 뜨며, ROI 위치를 조정한 뒤 [OK] 버튼을 누르면, 해당 ROI 위치를 기반으로 스크립트가 실행됩니다.
        # [START] 버튼을 눌러 실행시킨 스크립트는 사용자가 [STOP] 버튼을 누를 때까지 종료되지 않습니다.
        self.btn_list[0].clicked.connect(self.click_start)
        # 자식 프로세스(스크립트 실행 중)를 kill하는 역할입니다. 활성화되었을 때만 작동합니다.
        self.btn_list[1].clicked.connect(self.click_stop)
        # 초기화면에서 [STOP] 버튼은 비활성화되어야 합니다.
        # [START] 버튼을 눌러 스크립트가 실행되면 [STOP] 버튼이 활성화됩니다.
        self.btn_list[1].setEnabled(False)
        # excel 로컬 파일의 일부(혹은 전체)를 다른 디렉토리로 복제하는 창을 띄웁니다.
        self.btn_list[2].clicked.connect(self.click_download)

        self.init_UI()

    def init_UI(self):
        self.btn_layout = QHBoxLayout()
        for btn in self.btn_list:
            self.btn_layout.addWidget(btn)
        self.status_label = QLabel("Press [START] to start recording . . .")
        self.main_layout = QVBoxLayout()
        self.main_layout.addLayout(self.btn_layout, 3)
        self.main_layout.addWidget(self.status_label, 1)
        self.setLayout(self.main_layout)
        self.setWindowTitle("POTHOLE DETECTION")
        self.setFixedSize(900, 300)
        self.set_window_center()
        self.setFont(QFont("Arial", 11))
        self.show()
    def set_window_center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    def exe_script(self):
        self.status_label.setText("SCRIPT RUNNING . . . YOU CAN STOP with [STOP] to SAVE DATA")
        # 실행할 파일의 경로를 입력하세요.
        # command = ["python3}, }./test/segnet-camera_last_last.py", "--network=fcn-resnet18-cityscapes-1024x512", f"--x_coord={str(self.roi_box[0])}", f"--y_coord={str(self.roi_box[1])}", f"--reversed={str(self.roi_box[2])}"]
        command = ["python3", "./test/segnet-camera_last_last.py", "--network=fcn-resnet18-cityscapes-1024x512",
                   f"--x_coord={str(self.roi_box[0])}", f"--y_coord={str(self.roi_box[1])}",
                   f"--reversed={str(self.roi_box[2])}"]  # 실행할 파일의 경로를 입력하세요.
        self.child_process = subprocess.Popen(command)
        self.child_pid = self.child_process.pid
        print("CHILD PID : {0}".format(self.child_pid))
        print("CHILD PROCESS: {0}".format(os.getpid()))
    def click_start(self):
        ROI_window = ROIWindow()
        if ROI_window.exec_() == QDialog.Accepted:
            self.roi_box = ROI_window.get_coordinates()
        self.btn_list[0].setEnabled(False)
        self.btn_list[1].setEnabled(True)
        self.exe_script()
    def click_stop(self):
        # 스크립트가 돌아가는 child_process를 kill합니다.
        print(self.child_pid)
        if self.child_pid:
            os.kill(self.child_pid, signal.SIGTERM)
        else:
            print("Child process PID not available")
        # self.child_process.terminate()
        # 각 버튼의 활성 상태를 바꿉니다.
        self.status_label.setText("EXCEL FILE SAVED ! Press [START] to start recording . . .")
        self.btn_list[0].setEnabled(True)
        self.btn_list[1].setEnabled(False)
    def click_download(self):
        self.to_path = QFileDialog.getExistingDirectory(self, "USB-Path to COPY(MOVE) Data File", ".")
        self.get_data_files()
        download_window = DownloadWindow(self.data_list, self.to_path)
        if download_window.exec_() == QDialog.Accepted:
            pass
    def get_data_files(self):
        self.data_list = []
        for file in os.listdir(FROM_PATH + "/Excel"):
            if file.endswith(".xls") or file.endswith(".xlsx"):
                self.data_list.append(file)

class ROIWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.init_UI()
    def init_UI(self):
        # 확인 버튼입니다.
        self.ok_btn = QPushButton("OK", self)
        self.ok_btn.clicked.connect(self.click_ok)
        # self.ok_btn.setGeometry(int(CAM_WIDTH / 2) - 70, CAM_HEIGHT + 45, 200, 60) 중앙 버튼
        self.ok_btn.setGeometry(CAM_WIDTH - 170, CAM_HEIGHT + 45, 200, 60)

        self.img_label = QLabel(self)        # 실시간 카메라 영상을 띄울 공간입니다.
        self.img_label.setGeometry(30, 30, CAM_WIDTH, CAM_HEIGHT)   # 이 좌표를 기반으로 ROI의 좌표 보정이 들어갑니다.
        self.img_label.resize(CAM_WIDTH, CAM_HEIGHT)    # 카메라 해상도입니다.
        self.installEventFilter(self)   # 영상에 마우스 이벤트 필터를 추가합니다.

        timer = QTimer(self)    # 실시간 카메라 영상의 프레임을 업데이트하는 타이머입니다.
        timer.timeout.connect(self.update_frame)
        timer.start(10) # 초당 10 프레임입니다.

        self.capture = cv2.VideoCapture(0)  # 카메라를 연결합니다.
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)

        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(Qt.transparent)  # 배경을 투명하게 설정
        self.view = QGraphicsView(self.scene, self)
        self.view.setStyleSheet("background: transparent;")  # 배경을 투명하게 설정
        self.view.setSceneRect(0, 0, CAM_WIDTH + 60, CAM_HEIGHT + 120)
        self.view.setGeometry(0, 0, CAM_WIDTH + 60, CAM_HEIGHT + 120)
        self.view.setFixedSize(CAM_WIDTH + 60, CAM_HEIGHT + 120)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.roi_box = QGraphicsRectItem(QRectF(int(30 + float(CAM_WIDTH / 2) - float(ROI_WIDTH / 2)), int(30 + float(CAM_HEIGHT / 2) - float(ROI_HEIGHT / 2)), int(1024 * CAM_SCALE), int(512 * CAM_SCALE)))
        self.roi_box.setBrush(QBrush(Qt.transparent))
        self.roi_box.setPen(QPen(Qt.green, 10, Qt.SolidLine))
        self.clk_x = int(30 + float(CAM_WIDTH / 2) - float(ROI_WIDTH / 2))
        self.clk_y = int(30 + float(CAM_HEIGHT / 2) - float(ROI_HEIGHT / 2))
        self.scene.addItem(self.roi_box)

        self.is_it_reversed = int(0)    # 카메라의 반전 여부를 의미하는 이진 변수입니다.

        # 상단에 띄울 상하반전 버튼과 좌표 레이블입니다.
        self.rvs_btn = QPushButton("UP-DOWN REVERSE", self)
        self.rvs_btn.setGeometry(CAM_WIDTH - 485, CAM_HEIGHT + 45, 300, 60)
        self.rvs_btn.clicked.connect(self.click_rvs)
        self.coord_label = QLabel("p1(x, y) : (" + str(self.clk_x) + ", " + str(self.clk_y) + ")", self)
        self.coord_label.setGeometry(30, CAM_HEIGHT + 45, 500, 60)

        self.setWindowTitle("SET ROI POSITION > >")
        self.setFixedSize(CAM_WIDTH + 60, CAM_HEIGHT + 120)
        self.set_window_center()
        self.show()
    def set_window_center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    def click_ok(self):
        self.capture.release()
        self.accept()
    def click_rvs(self):
        if self.is_it_reversed == 1:
            self.is_it_reversed = 0
        elif self.is_it_reversed == 0:
            self.is_it_reversed = 1
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
            # QLabel에 이미지를 표시합니다.
            self.img_label.setPixmap(QPixmap.fromImage(q_img))
    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:  # 좌클릭인 경우
            if self.ok_btn.geometry().contains(ev.pos()):   # OK 버튼을 클릭한 경우
                self.ok_btn.click()
            elif self.rvs_btn.geometry().contains(ev.pos()):   # 반전 버튼을 클릭한 경우
                self.rvs_btn.click()
            else:   # 버튼이 아닌 영역을 클릭한 경우
                self.scene.removeItem(self.roi_box)
                self.clk_x = ev.pos().x()
                self.clk_y = ev.pos().y()
                self.roi_box = QGraphicsRectItem(QRectF(self.clk_x, self.clk_y, ROI_WIDTH, ROI_HEIGHT))
                print("[Click] x: {0} , y: {1}".format(ev.pos().x() - 30, ev.pos().y() - 30))
                self.roi_box.setBrush(QBrush(Qt.transparent))
                self.roi_box.setPen(QPen(Qt.green, 10, Qt.SolidLine))
                self.scene.addItem(self.roi_box)
                self.update()
                self.coord_label.setText("p1(x, y) : (" + str(self.clk_x - 30) + ", " + str(self.clk_y - 30) + ")")
                super().mousePressEvent(ev)
    def get_coordinates(self):
        return [self.clk_x - 30, self.clk_y - 30, self.is_it_reversed]

class DownloadWindow(QDialog):
    def __init__(self, data_list: list, to_path: str):
        super().__init__()
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
        self.finish_btn = QPushButton("FINISH", self)
        self.finish_btn.clicked.connect(self.click_finish)

        self.btn_layout = QHBoxLayout()
        self.btn_layout.addWidget(self.copy_btn)
        self.btn_layout.addWidget(self.move_btn)
        self.btn_layout.addWidget(self.finish_btn)

        self.list_view = QListView()
        self.list_view.setModel(self.data_model)

        main_layout = QVBoxLayout(self)
        # main_layout.addWidget(QLabel(self.from_path.split('/')[-1] + " -> " + self.to_path.split('/')[-1]))
        main_layout.addLayout(self.tool_layout)
        main_layout.addWidget(self.list_view)
        main_layout.addLayout(self.btn_layout)

        self.setLayout(main_layout)
        self.setWindowTitle("COPY or MOVE DATA FILES to USB > >")
        self.setFixedSize(1000, 800)
        self.set_window_center()
        self.setFont(QFont("Arial", 10))
        self.show()
    def set_window_center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    def click_copy(self):
        for i in range(len(self.data_list)):
            if self.data_model.item(i, 0).checkState() == 2:
                try:
                    su.copy(os.path.join(FROM_PATH + "/Excel", self.data_model.item(i, 0).text()), os.path.join(self.to_path, self.data_model.item(i, 0).text()))
                    su.copytree(FROM_PATH + "/full_frame_detect/" + self.data_model.item(i, 0).text().split('.')[0], self.to_path + "/" + self.data_model.item(i, 0).text().split('.')[0])
                except FileNotFoundError:
                    print("File not found")
                except Exception as e:
                    print("An error occurred", e)
                except PermissionError:
                    print("Permission denied !")
    def click_move(self):
        for i in range(len(self.data_list)):
            if self.data_model.item(i, 0).checkState() == 2:
                try:
                    su.move(os.path.join(FROM_PATH + "/Excel", self.data_model.item(i, 0).text()), os.path.join(self.to_path, self.data_model.item(i, 0).text()))
                    su.move(FROM_PATH + "/full_frame_detect/" + self.data_model.item(i, 0).text().split('.')[0], self.to_path + "/" + self.data_model.item(i, 0).text().split('.')[0])
                    self.refresh_list() # 파일 목록을 새로고침합니다.
                except FileNotFoundError:
                    print("File not found")
                except Exception as e:
                    print("An error occurred", e)
                except PermissionError:
                    print("Permission denied !")
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
