import sys

from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QApplication, QPushButton
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, QParallelAnimationGroup, QTimer
from playsound import playsound
from qfluentwidgets import setThemeColor
from win32 import win32api

import conf
import list

attend_class = 'audio/attend_class.wav'
finish_class = 'audio/finish_class.wav'

attend_class_p_color = '#ff8800'
finish_class_p_color = '#5ADFAA'

window_list = []

# 重写力
class tip_toast(QWidget):
    def __init__(self, pos, width, state=1):
        super().__init__()
        uic.loadUi("widget-toast-bar.ui", self)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.move(pos[0], pos[1])
        self.resize(width, 125)

        # 标题
        title = self.findChild(QPushButton, 'alert')

        if state:
            title.setText('  上课')
            playsound(attend_class, block=False)
            setThemeColor(attend_class_p_color)  # 主题色
        else:
            title.setText('  下课')
            playsound(finish_class, block=False)
            setThemeColor(finish_class_p_color)

        # 设置样式表
        if state:
            title.setStyleSheet('border: none; color: rgba(255, 255, 255, 255); font-weight: bold; border-radius: 8px; '
                                'background-color: qlineargradient('
                                'spread:pad, x1:0, y1:0, x2:1, y2:1,'
                                ' stop:0 rgba(255, 200, 150, 255), stop:1 rgba(217, 147, 107, 255)'
                                ');'
                                )
        else:
            title.setStyleSheet('border: none; color: rgba(255, 255, 255, 255); font-weight: bold; border-radius: 8px; '
                                'background-color: qlineargradient('
                                'spread:pad, x1:0, y1:0, x2:1, y2:1,'
                                ' stop:0 rgba(166, 200, 140, 255), stop:1 rgba(107, 217, 170, 255)'
                                ');'
                                )
        # 设置窗口初始大小
        mini_size_x = 120
        mini_size_y = 20

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(1200)
        self.timer.timeout.connect(self.close_window)

        # 放大效果
        self.geometry_animation = QPropertyAnimation(self, b"geometry")
        self.geometry_animation.setDuration(350)  # 动画持续时间
        self.geometry_animation.setStartValue(
            QRect(int(start_x + mini_size_x / 2), int(start_y + mini_size_y / 2),
                  total_width - mini_size_x, 125 - mini_size_y)
        )
        self.geometry_animation.setEndValue(QRect(start_x, start_y, total_width, 125))
        self.geometry_animation.setEasingCurve(QEasingCurve.Type.InOutCirc)

        # 渐显
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(400)
        self.opacity_animation.setStartValue(0)
        self.opacity_animation.setEndValue(1)

        # 动画组
        self.animation_group = QParallelAnimationGroup(self)
        self.animation_group.addAnimation(self.opacity_animation)
        self.animation_group.addAnimation(self.geometry_animation)
        self.animation_group.finished.connect(self.timer.start)

        self.animation_group.start()

    def close_window(self):
        mini_size_x = 120
        mini_size_y = 20
        # 放大效果
        self.geometry_animation_close = QPropertyAnimation(self, b"geometry")
        self.geometry_animation_close.setDuration(350)  # 动画持续时间
        self.geometry_animation_close.setStartValue(QRect(start_x, start_y, total_width, 125))
        self.geometry_animation_close.setEndValue(
            QRect(int(start_x + mini_size_x / 2), int(start_y + mini_size_y / 2),
                  total_width - mini_size_x, 125 - mini_size_y))
        self.geometry_animation_close.setEasingCurve(QEasingCurve.Type.InOutCirc)

        self.opacity_animation_close = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation_close.setDuration(200)
        self.opacity_animation_close.setStartValue(1)
        self.opacity_animation_close.setEndValue(0)

        self.animation_group_close = QParallelAnimationGroup(self)
        self.animation_group_close.addAnimation(self.geometry_animation_close)
        self.animation_group_close.addAnimation(self.opacity_animation_close)
        self.animation_group_close.finished.connect(self.close)

        self.animation_group_close.start()


def main(state=1):
    global start_x, start_y, total_width

    screen_width = win32api.GetSystemMetrics(0)
    spacing = -5
    total_width = sum(list.window_width, spacing * (len(list.window_width) - 1))
    start_x = int((screen_width - total_width) / 2)
    start_y = int(conf.read_conf('General', 'margin'))

    window = tip_toast((start_x, start_y), total_width, state)
    window.show()
    window_list.append(window)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main(0)
    sys.exit(app.exec())
