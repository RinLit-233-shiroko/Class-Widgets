import ctypes
import subprocess
import time
from shutil import copy

from playsound import playsound

from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QProgressBar, QGraphicsBlurEffect, QPushButton, \
    QGraphicsDropShadowEffect, QSystemTrayIcon, QMenu
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QEasingCurve, QParallelAnimationGroup
from PyQt6.QtGui import QColor, QIcon
import sys
from qfluentwidgets import Theme, setTheme, setThemeColor
import datetime as dt
import list
import conf

today = dt.date.today()
filename = conf.read_conf('General', 'schedule')

# 存储窗口对象
windows = []

current_state = '课程表未加载'
current_time = dt.datetime.now().strftime('%H:%M:%S')
current_week = dt.datetime.now().weekday()
current_lessons = {}

timeline_data = {}
next_lessons = []

bkg_opacity = 165  # 模糊label的透明度(0~255)

attend_class = 'audio/attend_class.wav'
finish_class = 'audio/finish_class.wav'

attend_class_p_color = '#ff8800'
finish_class_p_color = '#5ADFAA'


# 获取课程上下午开始时间
def get_start_time():
    global morning_st, afternoon_st, timeline_data
    morning_st = 0
    afternoon_st = 0
    loaded_data = conf.load_from_json(filename)
    timeline = loaded_data.get('timeline')

    for item_name, item_time in timeline.items():
        if item_name == 'start_time_m':
            if timeline[item_name]:
                h, m = timeline[item_name]
                morning_st = dt.datetime.combine(today, dt.time(h, m))
        elif item_name == 'start_time_a':
            if timeline[item_name]:
                h, m = timeline[item_name]
                afternoon_st = dt.datetime.combine(today, dt.time(h, m))
        else:
            timeline_data[item_name] = item_time


# 获取当前活动
def get_current_lessons():
    global current_lessons

    loaded_data = conf.load_from_json(filename)
    timeline = loaded_data.get('timeline')
    schedule = loaded_data.get('schedule')
    class_count = 0
    for item_name, item_time in timeline.items():
        if item_name.startswith('am') or item_name.startswith('aa'):
            if schedule[str(current_week)]:
                if schedule[str(current_week)][class_count] != '未添加':
                    current_lessons[item_name] = schedule[str(current_week)][class_count]
                else:
                    current_lessons[item_name] = '暂无课程'
                class_count += 1
            else:
                current_lessons[item_name] = '暂无课程'
                class_count += 1


# 获取倒计时、弹窗提示
def get_countdown():
    current_dt = dt.datetime.combine(today, dt.datetime.strptime(current_time, '%H:%M:%S').time())  # 当前时间
    return_text = []
    if afternoon_st != 0 and current_dt > afternoon_st - dt.timedelta(minutes=30):
        c_time = afternoon_st  # 开始时间段
        if current_dt == c_time:
            tip_toast(1).show()  # 上课
        if current_dt >= afternoon_st:
            for item_name, item_time in timeline_data.items():
                if item_name.startswith('aa') or item_name.startswith('fa'):

                    add_time = int(item_time)
                    c_time += dt.timedelta(minutes=add_time)

                    # 判断时间是否上下课，发送通知
                    if current_dt == c_time:
                        if item_name.startswith('aa'):
                            toast = tip_toast(0)
                            toast.show()  # 下课
                        else:
                            toast = tip_toast(1)
                            toast.show()  # 上课

                    if c_time >= current_dt:
                        # 根据所在时间段使用不同标语
                        if item_name.startswith('aa'):
                            return_text.append('当前活动结束还有')
                        else:
                            return_text.append('课间时长还有')
                        time_diff = c_time - current_dt
                        minute, sec = divmod(time_diff.seconds, 60)
                        return_text.append(f'{minute:02d}:{sec:02d}')
                        # 进度条
                        seconds = time_diff.seconds
                        return_text.append(int(100 - seconds / (int(item_time) * 60) * 100))
                        break
            if not return_text:
                return_text = ['今日课程已结束', f'00:00', 100]
        else:
            time_diff = c_time - current_dt
            minute, sec = divmod(time_diff.seconds, 60)
            return_text = ['距离上课还有', f'{minute:02d}:{sec:02d}', 100]
    # 上午
    elif morning_st != 0:
        c_time = morning_st  # 复制 morning_st 时间
        if current_dt == c_time:
            tip_toast(1).show()  # 上课
        if current_dt >= morning_st:
            for item_name, item_time in timeline_data.items():
                if item_name.startswith('am') or item_name.startswith('fm'):

                    add_time = int(item_time)
                    c_time += dt.timedelta(minutes=add_time)

                    # 判断时间是否上下课，发送通知
                    if current_dt == c_time:
                        if item_name.startswith('am'):
                            toast = tip_toast(0)
                            toast.show()  # 下课
                        else:
                            toast = tip_toast(1)
                            toast.show()  # 上课
                    if c_time >= current_dt:
                        # 根据所在时间段使用不同标语
                        if item_name.startswith('am'):
                            return_text.append('当前活动结束还有')
                        else:
                            return_text.append('课间时长还有')
                        # 返回倒计时、进度条
                        time_diff = c_time - current_dt
                        minute, sec = divmod(time_diff.seconds, 60)
                        return_text.append(f'{minute:02d}:{sec:02d}')
                        # 进度条
                        seconds = time_diff.seconds
                        return_text.append(int(100 - seconds / (int(item_time) * 60) * 100))
                        break
            if not return_text:
                return_text = ['上午课程已结束', f'00:00', 100]
        else:
            time_diff = c_time - current_dt
            minute, sec = divmod(time_diff.seconds, 60)
            return_text = ['距离上课还有', f'{minute:02d}:{sec:02d}', 100]
    return return_text


# 获取将发生的活动
def get_next_lessons():
    global current_state
    global next_lessons
    next_lessons = []
    current_dt = dt.datetime.combine(today, dt.datetime.strptime(current_time, '%H:%M:%S').time())  # 当前时间

    if afternoon_st != 0 and current_dt > afternoon_st - dt.timedelta(minutes=30):
        c_time = afternoon_st  # 开始时间段
        for item_name, item_time in timeline_data.items():
            if item_name.startswith('aa') or item_name.startswith('fa'):
                if c_time > current_dt:
                    if item_name.startswith('aa'):
                        next_lessons.append(current_lessons[item_name])
                c_time += dt.timedelta(minutes=int(item_time))
    elif morning_st != 0:
        c_time = morning_st  # 开始时间段
        for item_name, item_time in timeline_data.items():
            if item_name.startswith('am') or item_name.startswith('fm'):
                if current_dt < c_time:
                    if item_name.startswith('am'):
                        next_lessons.append(current_lessons[item_name])
                c_time += dt.timedelta(minutes=int(item_time))


def get_next_lessons_text():
    if not next_lessons:
        cache_text = '当前暂无课程'
    else:
        cache_text = ''
        if len(next_lessons) >= 5:
            range_time = 5
        else:
            range_time = len(next_lessons)
        for i in range(range_time):
            if range_time > 2:
                if next_lessons[i] != '暂无课程':
                    cache_text += f'{list.get_subject_abbreviation(next_lessons[i])}  '  # 获取课程简称
                else:
                    cache_text += f'无  '
            else:
                if next_lessons[i] != '暂无课程':
                    cache_text += f'{next_lessons[i]}  '
                else:
                    cache_text += f'暂无  '
    return cache_text


# 获取当前活动
def get_current_state():
    global current_state
    current_dt = dt.datetime.combine(today, dt.datetime.strptime(current_time, '%H:%M:%S').time())  # 当前时间
    is_changed = False
    # 下午
    if afternoon_st != 0 and current_dt > afternoon_st:
        c_time = afternoon_st  # 开始时间段
        for item_name, item_time in timeline_data.items():
            if item_name.startswith('aa') or item_name.startswith('fa'):
                c_time += dt.timedelta(minutes=int(item_time))
                if c_time >= current_dt:
                    if item_name.startswith('aa'):
                        current_state = current_lessons[item_name]
                        is_changed = True
                    else:
                        current_state = '课间'
                        is_changed = True
                    break
    # 上午
    elif morning_st != 0 and current_dt > morning_st:
        c_time = morning_st  # 复制 afternoon_st 时间
        for item_name, item_time in timeline_data.items():
            if item_name.startswith('am') or item_name.startswith('fm'):
                add_time = int(item_time)
                c_time += dt.timedelta(minutes=add_time)
                if c_time >= current_dt:
                    if item_name.startswith('am'):
                        current_state = current_lessons[item_name]
                        is_changed = True
                    else:
                        current_state = '课间'
                        is_changed = True
                    break
    if not is_changed:
        current_state = '暂无课程'


get_start_time()
get_current_lessons()
get_current_state()
get_next_lessons()


class tip_toast(QWidget):  # 上下课提示
    def __init__(self, state=1):
        super().__init__()
        uic.loadUi('widget-toast-bar.ui', self)

        # 标题
        title = self.findChild(QPushButton, 'alert')
        # 虽然解体级音质，但能用，就没计较了
        if state:
            title.setText('  上课')
            playsound(attend_class, block=False)
            setThemeColor(attend_class_p_color)  # 主题色
        else:
            title.setText('  下课')
            playsound(finish_class, block=False)
            setThemeColor(finish_class_p_color)

        # 设置窗口无边框和透明背景
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 点击穿透
        hwnd = int(self.winId())
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, ctypes.windll.user32.GetWindowLongW(hwnd, -20) | 0x80000 | 0x20)

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

        # 设置窗口位置
        self.animate_window()

    def animate_window(self):
        # 设置窗口初始大小
        mini_size_x = 120
        mini_size_y = 20

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
        self.animation_group.finished.connect(self.close_window)

        self.animation_group.start()

    def close_window(self):
        time.sleep(0.7)
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


class DesktopWidget(QWidget):  # 主要小组件
    def __init__(self, path='widget-time.ui', pos=(100, 50), enable_tray=False):
        super().__init__()
        init_config()
        uic.loadUi(path, self)

        setTheme(Theme.LIGHT)
        setThemeColor('#0078d6')

        # 设置窗口无边框和透明背景
        if int(conf.read_conf('General', 'pin_on_top')):  # 置顶
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        else:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 点击穿透
        if sys.platform == 'win32' and path != 'widget-current-activity.ui':
            hwnd = int(self.winId())
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, ctypes.windll.user32.GetWindowLongW(hwnd, -20) | 0x80000 | 0x20)

        # 添加阴影效果
        shadow_effect = QGraphicsDropShadowEffect(self)
        shadow_effect.setBlurRadius(22)
        shadow_effect.setXOffset(0)
        shadow_effect.setYOffset(7)
        shadow_effect.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow_effect)

        if enable_tray:  # 托盘图标
            self.tray_icon = QSystemTrayIcon(QIcon("img/favicon.png"), self)
            self.tray_icon.setToolTip('Class Widgets')

            self.tray_menu = QMenu()
            self.tray_menu.addAction(
                '恢复不透明度', lambda: conf.write_conf('General', 'transparent', '240'))
            self.tray_menu.addAction(
                '降低不透明度', lambda: conf.write_conf('General', 'transparent', '185'))
            self.tray_menu.addAction('设置', lambda: subprocess.Popen(['Settings.exe']))
            self.tray_menu.addAction('强制退出', lambda: sys.exit())

            self.tray_icon.setContextMenu(self.tray_menu)

            # 显示托盘图标
            self.tray_icon.show()

        match path:
            case 'widget-time.ui':  # 日期显示
                self.date_text = self.findChild(QLabel, 'date_text')
                self.date_text.setText(f'{today.year} 年 {today.month} 月')
                self.day_text = self.findChild(QLabel, 'day_text')
                self.day_text.setText(f'{today.day}日  {list.week[today.weekday()]}')

            case 'widget-countdown.ui':  # 活动倒计时
                self.countdown_progress_bar = self.findChild(QProgressBar, 'progressBar')
                self.activity_countdown = self.findChild(QLabel, 'activity_countdown')
                self.ac_title = self.findChild(QLabel, 'activity_countdown_title')

            case 'widget-current-activity.ui':  # 当前活动
                self.current_state_text = self.findChild(QPushButton, 'subject')
                self.blur_effect_label = self.findChild(QLabel, 'blurEffect')
                # 模糊效果
                self.blur_effect = QGraphicsBlurEffect()
                button = self.findChild(QPushButton, 'subject')
                button.clicked.connect(lambda: subprocess.Popen(['Exact_menu.exe']))
            case 'widget-next-activity.ui':  # 接下来的活动
                self.nl_text = self.findChild(QLabel, 'next_lesson_text')

        # 设置窗口位置
        self.animate_window(pos)

        self.update_data(1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)

    def animate_window(self, target_pos):  # 窗口动画！
        # 创建位置动画
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(625)  # 持续时间
        self.animation.setStartValue(QRect(target_pos[0], -self.height(), self.width(), self.height()))
        self.animation.setEndValue(QRect(target_pos[0], target_pos[1], self.width(), self.height()))
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCirc)  # 设置动画效果
        self.animation.start()

    def update_data(self, first_setup=0):
        global current_time
        global current_week
        global filename
        global start_y

        current_time = dt.datetime.now().strftime('%H:%M:%S')
        filename = conf.read_conf('General', 'schedule')
        start_y = int(conf.read_conf('General', 'margin'))

        get_start_time()
        get_current_lessons()
        get_current_state()
        get_next_lessons()

        if not first_setup:  # 如果不是初次启动
            self.move(self.x(), start_y)

        if conf.is_temp_week():  # 调休日
            current_week = conf.read_conf('Temp', 'set_week')
        else:
            current_week = dt.datetime.now().weekday()

        filename = conf.read_conf('General', 'schedule')

        transparent = conf.read_conf('General', 'transparent')
        bkg = self.findChild(QLabel, 'label')
        bkg.setStyleSheet(f'background-color: rgba(242, 243, 245, {int(transparent)}); border-radius: 8px')  # 背景透明度

        # 说实在这到底是怎么跑起来的
        if hasattr(self, 'day_text'):
            self.date_text.setText(f'{today.year} 年 {today.month} 月')
            self.day_text.setText(f'{today.day} 日 {list.week[today.weekday()]}')

        if hasattr(self, 'current_state_text'):
            # 实时活动
            self.current_state_text.setText(f'  {current_state}')
            self.current_state_text.setIcon(QIcon(list.get_subject_icon(current_state)))

            self.blur_effect.setBlurRadius(35)  # 模糊半径
            self.blur_effect_label.setStyleSheet(
                f'background-color: rgba{list.subject_color(current_state)}, {bkg_opacity});'
            )
            self.blur_effect_label.setGraphicsEffect(self.blur_effect)

        if hasattr(self, 'next_lesson_text'):
            self.nl_text.setText(get_next_lessons_text())

        if hasattr(self, 'activity_countdown'):
            if get_countdown():
                self.activity_countdown.setText(get_countdown()[1])
                self.ac_title.setText(get_countdown()[0])
                self.countdown_progress_bar.setValue(get_countdown()[2])


def init_config():
    conf.write_conf('Temp', 'set_week', '')
    if conf.read_conf('General', 'temp_schedule'):
        copy('config/schedule/backup.json', f'config/schedule/{filename}')
        conf.write_conf('Temp', 'temp_schedule', '')


def show_window(path, pos, enable_tray=False):
    application = DesktopWidget(path, pos, enable_tray)
    application.show()
    windows.append(application)  # 将窗口对象添加到列表


if __name__ == '__main__':
    app = QApplication(sys.argv)
    if sys.platform == 'win32' and sys.getwindowsversion().build >= 22000:  # 修改在win11高版本阴影异常
        app.setStyle("Fusion")

    # 获取屏幕横向分辨率
    screen_geometry = app.primaryScreen().availableGeometry()
    screen_width = screen_geometry.width()

    window_width = [230, 200, 360, 290]  # 所有组件窗口的宽度
    spacing = -5
    total_width = sum(window_width, spacing * (len(window_width) - 1))

    start_x = int((screen_width - total_width) / 2)
    start_y = int(conf.read_conf('General', 'margin'))


    def cal_start_width(num):
        width = 0
        for i in range(num):
            width += window_width[i]
        return int(start_x + spacing * num + width)

    if conf.read_conf('Other', 'InitialStartUp'):  # 首次启动
        conf.add_shortcut('ClassWidgets.exe', 'img/favicon.ico')
        conf.add_shortcut_to_startmenu('ClassWidgets.exe', 'img/favicon.ico')
        conf.write_conf('Other', 'initialstartup', '')

    show_window('widget-time.ui', (start_x, start_y))
    show_window('widget-countdown.ui', (cal_start_width(1), start_y))
    show_window('widget-current-activity.ui', (cal_start_width(2), start_y), True)
    show_window('widget-next-activity.ui', (cal_start_width(3), start_y))

    sys.exit(app.exec())
