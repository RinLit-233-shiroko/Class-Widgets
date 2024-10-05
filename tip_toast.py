import sys

import sounddevice
import soundfile
from PyQt6 import uic
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, QParallelAnimationGroup, QTimer, QPoint, \
    pyqtProperty
from PyQt6.QtGui import QColor, QPainter, QBrush
from PyQt6.QtWidgets import QWidget, QApplication, QLabel, QFrame
from loguru import logger
from qfluentwidgets import setThemeColor, Theme, setTheme

import conf
import list

prepare_class = conf.read_conf('Audio', 'prepare_class')
attend_class = conf.read_conf('Audio', 'attend_class')
finish_class = conf.read_conf('Audio', 'finish_class')

# 波纹效果
attend_class_color = '#dd986f'
finish_class_color = '#79d4a1'
prepare_class_color = '#8073F9'
normal_color = '#73A0F9'

window_list = []  # 窗口列表


# 重写力
class tip_toast(QWidget):
    def __init__(self, pos, width, state=1, lesson_name='', title='', subtitle='', content=''):
        super().__init__()
        uic.loadUi("widget-toast-bar.ui", self)

        # 窗口位置
        if conf.read_conf('Toast', 'pin_on_top') == '1':
            self.setWindowFlags(
                Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        else:
            self.setWindowFlags(
                Qt.WindowType.WindowStaysOnBottomHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.move(pos[0], pos[1])
        self.resize(width, height)

        # 标题
        title_label = self.findChild(QLabel, 'title')
        backgnd = self.findChild(QFrame, 'backgnd')
        lesson = self.findChild(QLabel, 'lesson')
        subtitle_label = self.findChild(QLabel, 'subtitle')
        bg_color = []

        if state == 1:
            logger.info('上课铃声显示')
            title_label.setText('上课')
            subtitle_label.setText('当前课程')
            lesson.setText(lesson_name)  # 课程名
            playsound(attend_class)
            setThemeColor(f'#{conf.read_conf('Color', 'attend_class')}')  # 主题色
        elif state == 0:
            logger.info('下课铃声显示')
            title_label.setText('下课')
            subtitle_label.setText('下一节')
            lesson.setText(lesson_name)  # 课程名
            playsound(finish_class)
            setThemeColor(f'#{conf.read_conf('Color', 'finish_class')}')
        elif state == 2:
            logger.info('放学铃声显示')
            title_label.setText('放学')
            subtitle_label.setText('当前课程已结束')
            lesson.setText('')  # 课程名
            playsound(finish_class)
            setThemeColor(f'#{conf.read_conf('Color', 'finish_class')}')
        elif state == 3:
            logger.info('预备铃声显示')
            title_label.setText('即将上课')
            subtitle_label.setText('下一节')
            lesson.setText(lesson_name)
            playsound(prepare_class)
            setThemeColor(f'#{conf.read_conf('Color', 'prepare_class')}')
        elif state == 4:
            logger.info(f'通知显示: {title}')
            title_label.setText(title)
            subtitle_label.setText(subtitle)
            lesson.setText(content)
            playsound(prepare_class)

        # 设置样式表
        if state == 1:
            bg_color = ['rgba(255, 200, 150, 255)', 'rgba(220, 150, 110, 255)']
        elif state == 0 or state == 2:
            bg_color = ['rgba(165, 200, 140, 255)', 'rgba(110, 220, 170, 255)']
        elif state == 3:
            bg_color = ['rgba(165, 110, 210, 255)', 'rgba(120, 120, 225, 255)']
        elif state == 4:
            bg_color = ['rgba(110, 180, 210, 255)', 'rgba(80, 130, 215, 255)']
        else:
            bg_color = ['rgba(110, 180, 210, 255)', 'rgba(80, 130, 215, 255)']

        backgnd.setStyleSheet(f'font-weight: bold; border-radius: {radius}; '
                              'background-color: qlineargradient('
                              'spread:pad, x1:0, y1:0, x2:1, y2:1,'
                              f' stop:0 {bg_color[0]}, stop:1 {bg_color[1]}'
                              ');'
                              )
        # 设置窗口初始大小
        mini_size_x = 100
        mini_size_y = 10

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.close_window)

        # 放大效果
        self.geometry_animation = QPropertyAnimation(self, b"geometry")
        self.geometry_animation.setDuration(450)  # 动画持续时间
        self.geometry_animation.setStartValue(
            QRect(int(start_x + mini_size_x / 2), int(start_y + mini_size_y / 2),
                  total_width - mini_size_x, height - mini_size_y)
        )
        self.geometry_animation.setEndValue(QRect(start_x, start_y, total_width, height))
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
        self.geometry_animation_close.setStartValue(QRect(start_x, start_y, total_width, height))
        self.geometry_animation_close.setEndValue(
            QRect(int(start_x + mini_size_x / 2), int(start_y + mini_size_y / 2),
                  total_width - mini_size_x, height - mini_size_y))
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


class wave_Effect(QWidget):
    def __init__(self, state=1):
        super().__init__()

        if conf.read_conf('Toast', 'pin_on_top') == '1':
            self.setWindowFlags(
                Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        else:
            self.setWindowFlags(
                Qt.WindowType.WindowStaysOnBottomHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._radius = 0
        duration = 1350

        if state == 1:
            self.color = QColor(attend_class_color)
        elif state == 0 or state == 2:
            self.color = QColor(finish_class_color)
        elif state == 3:
            self.color = QColor(prepare_class_color)
        elif state == 4:
            self.color = QColor(normal_color)
        else:
            self.color = QColor(normal_color)

        screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geometry)

        self.animation = QPropertyAnimation(self, b'radius')
        self.animation.setDuration(duration)
        self.animation.setStartValue(50)
        self.animation.setEndValue(max(self.width(), self.height()) * 1.7)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCirc)
        self.animation.start()

        self.fade_animation = QPropertyAnimation(self, b'windowOpacity')
        self.fade_animation.setDuration(duration - duration // 5)

        self.fade_animation.setKeyValues([
            (0, 0),
            (0.06, 1),
            (1, 0)
        ])

        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutCirc)
        self.fade_animation.finished.connect(self.close)
        self.fade_animation.start()

    @pyqtProperty(int)
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        self._radius = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(self.color))
        painter.setPen(Qt.PenStyle.NoPen)
        center = self.rect().center()
        loc = QPoint(center.x(), self.rect().top() + start_y + 50)
        painter.drawEllipse(loc, self._radius, self._radius)


def playsound(filename):
    try:
        data, samplerate = soundfile.read(f'audio/{filename}')
        volume = int(conf.read_conf('Audio', 'volume')) / 100
        data *= volume
        sounddevice.play(data, samplerate)
    except Exception as e:
        logger.error(f'读取音频文件出错：{e}')


def main(state=1, lesson_name='', title='通知示例', subtitle='副标题',
         content='这是一条通知示例'):  # 0:下课铃声 1:上课铃声 2:放学铃声 3:预备铃 4:其他
    global start_x, start_y, total_width, height, radius

    if conf.read_conf('General', 'color_mode') == '2':
        setTheme(Theme.AUTO)
    elif conf.read_conf('General', 'color_mode') == '1':
        setTheme(Theme.DARK)
    else:
        setTheme(Theme.LIGHT)

    if conf.read_conf('General', 'enable_toast') == '1':
        theme = conf.read_conf('General', 'theme')
        height = conf.load_theme_config(theme)['height']
        radius = conf.load_theme_config(theme)['radius']

        screen_geometry = QApplication.primaryScreen().geometry()
        screen_width = screen_geometry.width()
        spacing = -5
        widgets = list.get_widget_config()
        total_width = total_width = sum((list.widget_width[key] for key in widgets), spacing * (len(widgets) - 1))

        start_x = int((screen_width - total_width) / 2)
        start_y = int(conf.read_conf('General', 'margin'))

        if conf.read_conf('Toast', 'wave') == '1':
            wave = wave_Effect(state)
            wave.show()
            window_list.append(wave)

        if state != 4:
            window = tip_toast((start_x, start_y), total_width, state, lesson_name)
        else:
            window = tip_toast((start_x, start_y), total_width, state, '', title, subtitle, content)
        window.show()
        window_list.append(window)
    else:
        return


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main(0, '测试课程')
    sys.exit(app.exec())
