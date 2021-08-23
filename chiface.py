import sys
import cv2
import json
import sys
import time
import webbrowser
from PyQt5.QtCore import QSize, QPoint, Qt
from PyQt5.QtGui import QMouseEvent, QImage, QPixmap
from PyQt5.QtWidgets import QWidget, QMessageBox, QApplication, QMenu, qApp
from threading import Thread
from qtpy import QtWidgets, QtCore
from actor import Actor
from camera import camera
from emote_detect import EmoteDetection, get_shapes, FaceDetection
from base_logger import logger


class RunningConfig:
    FILENAME = 'chiface.json'
    def __init__(self) -> None:
        self.config = {
            'offset': [0, -50],
            'max_fps': 10,
            'target': 'mahilo'
        }
        self.load()
    
    def load(self):
        try:
            with open(self.FILENAME, "r", encoding="utf-8") as f:
                c = json.load(f)
                self.config.update(c)
        except FileNotFoundError:
            pass
        self.save()
    
    def save(self):
        with open(self.FILENAME, "w", encoding="utf-8") as f:
            json.dump(self.config, f, sort_keys=True, indent=2, ensure_ascii=False)


class Main(QWidget):
    _startPos = None
    _endPos = None
    _isTracking = False
    _isQuiting = False
    last_frame = None
    max_fps = 30

    def __init__(self):
        super().__init__()

        try:
            self.running_config = RunningConfig()
        except json.decoder.JSONDecodeError as e:
            msg_box = QtWidgets.QMessageBox
            msg_box.critical(self, f"配置文件{RunningConfig.FILENAME}错误", str(e), msg_box.Yes)
            sys.exit(1)
        
        self.max_fps = self.running_config.config['max_fps']

        self.setWindowFlags(Qt.FramelessWindowHint |
                            QtCore.Qt.WindowStaysOnTopHint | Qt.Tool)
        # 设置窗口背景透明
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.img = QtWidgets.QLabel(self)
        self.img.setAlignment(QtCore.Qt.AlignCenter)
        self.img.setObjectName("img")
        self.show()

        try:
            self.actor: Actor = Actor()
            self.actor.load(self.running_config.config['target'])
        except Exception as e:
            msg_box = QtWidgets.QMessageBox
            msg_box.critical(self, f"无法加载{self.running_config.config['target']}", str(e), msg_box.Yes | msg_box.Ignore)
            if msg_box.Ignore:
                self.actor.load(self.running_config.config['target'], generate=True)
            else:
                sys.exit(1)
        camera.open()
        im = self.actor.get_image()
        self.setFixedSize(QSize(im.shape[1], im.shape[0]))
        self.img.setGeometry(QtCore.QRect(0, 0, im.shape[1], im.shape[0]))
        self.img.setMinimumSize(QtCore.QSize(im.shape[1], im.shape[0]))
        self.img.setBaseSize(QtCore.QSize(im.shape[1], im.shape[0]))

        screen_rect = app.desktop().screenGeometry()
        width, height = screen_rect.width(), screen_rect.height()
        self.move(width - im.shape[1] + self.running_config.config['offset'][0],
                  height - im.shape[0] + self.running_config.config['offset'][1])

        self.th_loop = Thread(target=self.loop, daemon=True)
        self.th_loop.start()

    # 重写移动事件
    def mouseMoveEvent(self, e: QMouseEvent):
        self._endPos = e.pos() - self._startPos
        self.move(self.pos() + self._endPos)

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self._isTracking = True
            self._startPos = QPoint(e.x(), e.y())

        if e.button() == Qt.RightButton:
            menu = QMenu(self)
            quitAction = menu.addAction("退出")
            aboutAction = menu.addAction("关于")
            action = menu.exec_(self.mapToGlobal(e.pos()))
            if action == quitAction:
                self._isQuiting = True
                qApp.quit()
            if action == aboutAction:
                webbrowser.open('https://github.com/chiro2001')

    def mouseReleaseEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self._isTracking = False
            self._startPos = None
            self._endPos = None
        if e.button() == Qt.RightButton:
            self._isTracking = False
            self._startPos = None
            self._endPos = None

    def loop(self):
        try:
            while True:
                if self.last_frame == None:
                    self.last_frame = time.time()
                    continue
                frame_time = time.time()
                while frame_time - self.last_frame < 1 / self.max_fps:
                    frame_time = time.time()
                    time.sleep(0.01)
                self.last_frame = frame_time
                frame = camera.read()
                faces = FaceDetection.detect_faces(frame)
                shapes = get_shapes(frame, faces=faces)
                emotes = EmoteDetection.parse(shapes[:1], faces)
                # logger.info(emotes)
                for face in faces:
                    cv2.rectangle(frame, face[0:2], face[2:4], (0, 0, 255), 2)
                for shape in shapes:
                    for point in shape:
                        cv2.circle(frame, point, 3, (0, 255, 0), -1)
                if len(emotes) == 1:
                    emote = emotes[0]
                    EmoteDetection.act(self.actor, emote)
                    im = self.actor.get_image()
                    im = cv2.cvtColor(im, cv2.COLOR_RGBA2BGRA)
                    if self._isQuiting:
                        break
                    image = QImage(
                        im.data, im.shape[1], im.shape[0], im.shape[1] * 4, QImage.Format_RGBA8888)
                    self.img.setPixmap(QPixmap.fromImage(image))
                    self.img.show()
        except Exception as e:
            msg_box = QtWidgets.QMessageBox
            msg_box.critical(self, f"未知错误({e.__class__.__name__})", str(e), msg_box.Yes)
            self._isQuiting = True
            qApp.quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Main()
    sys.exit(app.exec_())
