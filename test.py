import sys

from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsRectItem
from PyQt5.QtCore import Qt

class MyGraphicsView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # QGraphicsRectItem 생성
        self.rect_item = QGraphicsRectItem(0, 0, 100, 100)
        self.scene.addItem(self.rect_item)

        self.setDragMode(QGraphicsView.ScrollHandDrag)  # 드래그 모드 설정
        self.setRenderHint(QPainter.Antialiasing)  # 안티앨리어싱 활성화

    def mousePressEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            # 왼쪽 버튼을 눌렀을 때, 그래픽 항목 이동 시작
            self.orig_pos = event.pos()
            self.orig_rect_pos = self.rect_item.pos()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            # 왼쪽 버튼을 누른 상태에서 마우스 이동시, 그래픽 항목 이동
            delta = event.pos() - self.orig_pos
            new_pos = self.orig_rect_pos + delta
            self.rect_item.setPos(new_pos)

        super().mouseMoveEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    view = MyGraphicsView()
    view.show()
    sys.exit(app.exec_())