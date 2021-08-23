# -*- coding: utf-8 -*-
import time
import webbrowser

from PyQt5.QtCore import QSize, QPoint, Qt
from PyQt5.QtGui import QMouseEvent, QMovie, QCursor
from PyQt5.QtWidgets import QWidget, QMessageBox, QApplication, QMenu, qApp
# net_io_counters 网络输入与输出 如果需要获取单个网卡的io信息，加上pernic=True参数。
from psutil import net_io_counters
from threading import Thread
import sys
from qtpy import QtWidgets, QtCore


def gsh(count):
    if count < 1024:
        return "%.2f B/s" % count
    if count < 1048576:
        return "%.2f KB/s" % (count / 1024)
    count >>= 10
    if count < 1048576:
        return "%.2f MB/s" % (count / 1024)
    count >>= 10
    return "%.2f GB/s" % (count / 1024)


def get_data():
    old = [0, 0]
    new = [0, 0]
    net_info = net_io_counters()  # 获取流量统计信息
    recv_bytes = net_info.bytes_recv
    sent_bytes = net_info.bytes_sent
    old[0] += recv_bytes
    old[1] += sent_bytes
    time.sleep(1)

    # 当前所收集的数据
    net_info = net_io_counters()  # 获取流量统计信息
    recv_bytes = net_info.bytes_recv
    sent_bytes = net_info.bytes_sent
    new[0] += recv_bytes
    new[1] += sent_bytes
    info = []
    for i in range(2):
        info.append(new[i] - old[i])
    return info


class Main(QWidget):
    _startPos = None
    _endPos = None
    _isTracking = False
    all_bytes = 0
    about = "监控电脑网络的上传跟下载网速。\n统计网络使用总流量！\n作者：旋凯凯旋"

    def __init__(self):
        super().__init__()
        self._initUI()
        # with open('流量使用情况.txt', 'r') as f:
        #     self.all_bytes = int(f.read())
        self.all_bytes = 0

    def _initUI(self):
        self.setFixedSize(QSize(259, 270))
        self.setWindowFlags(Qt.FramelessWindowHint |
                            QtCore.Qt.WindowStaysOnTopHint | Qt.Tool)

        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)  # 设置窗口背景透明

        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(QtCore.QRect(0, 0, 259, 111))
        self.label.setMinimumSize(QtCore.QSize(259, 111))
        self.label.setBaseSize(QtCore.QSize(259, 111))
        self.label.setStyleSheet(
            "font: 75 20pt \"Adobe Arabic\";color:rgb(255,0,0)")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")

        self.label2 = QtWidgets.QLabel(self)
        self.label2.setGeometry(QtCore.QRect(10, 110, 259, 161))
        self.label2.setMinimumSize(QtCore.QSize(259, 161))
        self.label2.setBaseSize(QtCore.QSize(259, 161))
        self.label2.setAlignment(QtCore.Qt.AlignCenter)
        self.gif = QMovie('1271.gif')
        self.label2.setMovie(self.gif)
        self.label2.setObjectName("label2")
        self.gif.start()

        self.timer = QtCore.QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.start)

        self.setCursor(QCursor(Qt.PointingHandCursor))

        self.show()

    def start(self):
        Thread(target=self.setSpeed, daemon=True).start()

    def setSpeed(self):
        info = get_data()
        recv_bytes = gsh(info[0])  # 每秒接收的字节
        sent_bytes = gsh(info[1])  # 每秒发送的字节
        self.all_bytes += sum(info)
        if self.all_bytes < 1073741824:
            all_bytes = self.all_bytes / 1048576
            strs = "已使用：%.2f Mb" % all_bytes
        else:
            all_bytes = self.all_bytes / 1073741824
            strs = "已使用：%.2f Gb" % all_bytes
        self.label.setText("上传：%s\n下载：%s\n%s" % (sent_bytes, recv_bytes, strs))

    def mouseMoveEvent(self, e: QMouseEvent):  # 重写移动事件
        self._endPos = e.pos() - self._startPos
        self.move(self.pos() + self._endPos)

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self._isTracking = True
            self._startPos = QPoint(e.x(), e.y())

        if e.button() == Qt.RightButton:
            menu = QMenu(self)
            quitAction = menu.addAction("退出程序")
            aboutAction = menu.addAction("关于程序")
            action = menu.exec_(self.mapToGlobal(e.pos()))
            if action == quitAction:
                # with open('流量使用情况.txt', 'w') as f:
                #     f.write(str(self.all_bytes))
                qApp.quit()
            if action == aboutAction:
                msg_box = QtWidgets.QMessageBox
                msg_box.question(self, "关于", self.about,
                                 msg_box.Yes | msg_box.Cancel)
                if QMessageBox.Yes:
                    webbrowser.open('https://me.csdn.net/Cxk___',
                                    new=0, autoraise=True)

    def mouseReleaseEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self._isTracking = False
            self._startPos = None
            self._endPos = None
        if e.button() == Qt.RightButton:
            self._isTracking = False
            self._startPos = None
            self._endPos = None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Main()
    sys.exit(app.exec_())
