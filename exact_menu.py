import subprocess
import sys
import datetime as dt
from shutil import copy

from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QApplication
from qfluentwidgets import FluentWindow, setTheme, Theme, FluentIcon as fIcon, setThemeColor, ComboBox, \
    PrimaryPushButton, Flyout, FlyoutAnimationType, InfoBarIcon, ListWidget, LineEdit, ToolButton, HyperlinkButton
from win32 import win32api

import conf
import list
import menu

filename = conf.read_conf('General', 'schedule')
current_week = dt.datetime.today().weekday()
temp_schedule = {'schedule': {}}


class ExactMenu(FluentWindow):
    def __init__(self):
        super().__init__()
        self.interface = uic.loadUi('exact_menu.ui')
        self.initUI()
        self.init_interface()

    def init_interface(self):
        select_temp_week = self.findChild(ComboBox, 'select_temp_week')  # 选择替换日期
        select_temp_week.addItems(list.week)
        select_temp_week.setCurrentIndex(current_week)

        tmp_schedule_list = self.findChild(ListWidget, 'schedule_list')  # 换课列表
        tmp_schedule_list.addItems(conf.load_from_json(filename)['schedule'][str(current_week)])
        tmp_schedule_list.itemChanged.connect(self.upload_item)

        class_kind_combo = self.findChild(ComboBox, 'class_combo')  # 课程类型
        class_kind_combo.addItems(list.class_kind)

        set_button = self.findChild(ToolButton, 'set_button')
        set_button.setIcon(fIcon.EDIT)
        set_button.clicked.connect(self.edit_item)

        save_temp_conf = self.findChild(PrimaryPushButton, 'save_temp_conf')  # 保存设置
        save_temp_conf.clicked.connect(self.save_temp_conf)

        redirect_to_settings = self.findChild(HyperlinkButton, 'redirect_to_settings')
        redirect_to_settings.clicked.connect(self.open_settings)

    def open_settings(self):
        self.menu = menu.desktop_widget()
        self.menu.show()

    def save_temp_conf(self):
        if temp_schedule != {'schedule': {}}:
            copy(f'config/schedule/{filename}', f'config/schedule/backup.json')  # 备份课表配置
            conf.write_conf('Temp', 'temp_schedule', filename)
            conf.save_data_to_json(temp_schedule, filename)
        temp_week = self.findChild(ComboBox, 'select_temp_week')
        conf.write_conf('Temp', 'set_week', str(temp_week.currentIndex()))
        Flyout.create(
            icon=InfoBarIcon.SUCCESS,
            title='保存成功',
            content=f"已保存至 ./config.ini \n重启后失效。",
            target=self.findChild(PrimaryPushButton, 'save_temp_conf'),
            parent=self,
            isClosable=True,
            aniType=FlyoutAnimationType.PULL_UP
        )

    def upload_item(self):
        global temp_schedule
        se_schedule_list = self.findChild(ListWidget, 'schedule_list')
        cache_list = []
        for i in range(se_schedule_list.count()):
            item_text = se_schedule_list.item(i).text()
            cache_list.append(item_text)
        temp_schedule['schedule'][str(current_week)] = cache_list

    def edit_item(self):
        tmp_schedule_list = self.findChild(ListWidget, 'schedule_list')
        class_combo = self.findChild(ComboBox, 'class_combo')
        custom_class = self.findChild(LineEdit, 'custom_class')
        selected_items = tmp_schedule_list.selectedItems()

        if selected_items:
            selected_item = selected_items[0]
            if class_combo.currentIndex() != 0:
                selected_item.setText(class_combo.currentText())
            else:
                if custom_class.text() != '':
                    selected_item.setText(custom_class.text())

    def initUI(self):
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        screen_width = win32api.GetSystemMetrics(0)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        setTheme(Theme.AUTO)

        self.resize(1000, 700)
        self.setWindowTitle('Class Widgets - 更多功能')
        self.setWindowIcon(QIcon('img/favicon-exmenu.ico'))
        self.move(int(screen_width/2-500), 150)  # 窗体居中，但不完全居中

        self.addSubInterface(self.interface, fIcon.INFO, '更多设置')

    def closeEvent(self, event):
        event.ignore()
        self.hide()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    if sys.platform == 'win32' and sys.getwindowsversion().build >= 22000:  # 修改在win11高版本阴影异常
        app.setStyle("fusion")
    ex = ExactMenu()
    ex.show()
    sys.exit(app.exec())
