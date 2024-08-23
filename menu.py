from PyQt6 import uic
from PyQt6.QtCore import Qt, QTime, QUrl
import sys

from PyQt6.QtGui import QIcon, QDesktopServices
from PyQt6.QtWidgets import QApplication, QHeaderView, QTableWidgetItem
from qfluentwidgets import (
    Theme, setTheme, setThemeColor, FluentWindow, FluentIcon as fIcon, ToolButton, ListWidget, ComboBox, CaptionLabel,
    SpinBox, TimePicker, LineEdit, PrimaryPushButton, TableWidget, Flyout, InfoBarIcon,
    FlyoutAnimationType, NavigationItemPosition, EditableComboBox, MessageBox, SubtitleLabel, PushButton, SwitchButton,
)
from copy import deepcopy
import datetime as dt
import list
import conf

today = dt.date.today()

width = 1200
height = 800

morning_st = 0
afternoon_st = 0

current_week = 0

filename = conf.read_conf('General', 'schedule')

schedule_dict = {}  # 对应时间线的课程表


class desktop_widget(FluentWindow):
    def __init__(self):
        super().__init__()
        # 设置窗口无边框和透明背景
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # 创建子页面
        self.spInterface = uic.loadUi('menu-preview.ui')
        self.spInterface.setObjectName("spInterface")
        self.teInterface = uic.loadUi('menu-timeline_edit.ui')  # 时间线编辑
        self.teInterface.setObjectName("teInterface")
        self.seInterface = uic.loadUi('menu-schedule_edit.ui')  # 课程表编辑
        self.seInterface.setObjectName("seInterface")
        self.adInterface = uic.loadUi('menu-advance.ui')
        self.adInterface.setObjectName("adInterface")
        self.ifInterface = uic.loadUi('menu-about.ui')
        self.ifInterface.setObjectName("ifInterface")

        self.init_nav()
        self.init_window()

    def load_all_item(self):
        self.setup_timeline_edit()
        self.setup_schedule_edit()
        self.setup_schedule_preview()
        self.setup_advance_interface()
        self.setup_about_interface()

    # 初始化界面
    def setup_about_interface(self):
        github_page = self.findChild(PushButton, "button_github")
        github_page.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(
            'https://github.com/RinLit-233-shiroko/Class-Widgets')))

        bilibili_page = self.findChild(PushButton, 'button_bilibili')
        bilibili_page.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(
            'https://space.bilibili.com/569522843')))

    def setup_advance_interface(self):
        margin_spin = self.findChild(SpinBox, 'margin_spin')
        margin_spin.setValue(int(conf.read_conf('General', 'margin')))
        margin_spin.valueChanged.connect(
            lambda: conf.write_conf('General', 'margin', str(margin_spin.value()))
        )  # 保存边距设定

        conf_combo = self.findChild(EditableComboBox, 'conf_combo')
        conf_combo.addItems(list.get_schedule_config())
        conf_combo.setCurrentIndex(list.get_schedule_config().index(conf.read_conf('General', 'schedule')))
        conf_combo.currentIndexChanged.connect(self.ad_change_file)  # 切换配置文件

        switch_pin_button = self.findChild(SwitchButton, 'switch_pin_button')
        switch_pin_button.setChecked(int(conf.read_conf('General', 'pin_on_top')))
        switch_pin_button.checkedChanged.connect(self.switch_pin)  # 置顶开关

        switch_startup = self.findChild(SwitchButton, 'switch_startup')
        switch_startup.setChecked(int(conf.read_conf('General', 'auto_startup')))
        switch_startup.checkedChanged.connect(self.switch_startup)  # 开机自启

    def setup_schedule_edit(self):
        self.se_load_item()
        se_set_button = self.findChild(ToolButton, 'set_button')
        se_set_button.setIcon(fIcon.EDIT)
        se_set_button.clicked.connect(self.se_edit_item)

        se_clear_button = self.findChild(ToolButton, 'clear_button')
        se_clear_button.setIcon(fIcon.DELETE)
        se_clear_button.clicked.connect(self.se_delete_item)

        se_custom_class_text = self.findChild(LineEdit, 'custom_class')

        se_class_kind_combo = self.findChild(ComboBox, 'class_combo')  # 课程类型
        se_class_kind_combo.addItems(list.class_kind)

        se_week_combo = self.findChild(ComboBox, 'week_combo')  # 星期
        se_week_combo.addItems(list.week)
        se_week_combo.currentIndexChanged.connect(self.se_upload_list)

        se_schedule_list = self.findChild(ListWidget, 'schedule_list')
        se_schedule_list.addItems(schedule_dict[str(current_week)])
        se_schedule_list.itemChanged.connect(self.se_upload_item)

        se_save_button = self.findChild(PrimaryPushButton, 'save_schedule')
        se_save_button.clicked.connect(self.se_save_item)

    def setup_timeline_edit(self):
        # teInterface
        te_add_button = self.findChild(ToolButton, 'add_button')  # 添加
        te_add_button.setIcon(fIcon.ADD)
        te_add_button.clicked.connect(self.te_add_item)

        te_edit_button = self.findChild(ToolButton, 'edit_button')  # 编辑
        te_edit_button.setIcon(fIcon.EDIT)
        te_edit_button.clicked.connect(self.te_edit_item)

        te_delete_button = self.findChild(ToolButton, 'delete_button')  # 删除
        te_delete_button.setIcon(fIcon.DELETE)
        te_delete_button.clicked.connect(self.te_delete_item)

        te_m_start_time = self.findChild(TimePicker, 'morningStartTime')
        te_m_start_time.timeChanged.connect(self.m_start_time_changed)
        te_a_start_time = self.findChild(TimePicker, 'afternoonStartTime')
        te_a_start_time.timeChanged.connect(self.a_start_time_changed)

        te_class_activity_combo = self.findChild(ComboBox, 'class_activity')  # 活动类型
        te_class_activity_combo.addItems(list.class_activity)
        te_class_activity_combo.currentIndexChanged.connect(self.te_sync_time)

        te_time_combo = self.findChild(ComboBox, 'time_period')  # 时段
        te_time_combo.addItems(list.time)

        te_save_button = self.findChild(PrimaryPushButton, 'save')  # 保存
        te_save_button.clicked.connect(self.te_save_item)
        self.te_load_item()

    def setup_schedule_preview(self):
        schedule_view = self.findChild(TableWidget, 'schedule_view')
        schedule_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # 使列表自动等宽

        subtitle = self.findChild(SubtitleLabel, 'subtitle_file')
        subtitle.setText(f'预览  -  {filename[:-5]}')

        # 设置表格
        schedule_view.setColumnCount(7)
        schedule_view.setHorizontalHeaderLabels(list.week[0:7])
        schedule_view.setRowCount(sp_get_class_num())
        schedule_view.setBorderVisible(True)
        schedule_view.verticalHeader().hide()
        schedule_view.setBorderRadius(8)
        self.sp_fill_grid_row()

    def switch_pin(self):
        switch_pin_button = self.findChild(SwitchButton, 'switch_pin_button')
        if switch_pin_button.isChecked():
            conf.write_conf('General', 'pin_on_top', '1')
        else:
            conf.write_conf('General', 'pin_on_top', '0')

    def switch_startup(self):
        switch_startup = self.findChild(SwitchButton, 'switch_startup')
        if switch_startup.isChecked():
            conf.write_conf('General', 'auto_startup', '1')
            conf.add_to_startup('ClassWidgets.exe', 'img/favicon.ico')
        else:
            conf.write_conf('General', 'auto_startup', '0')
            conf.remove_from_startup()

    def ad_change_file(self):
        conf_combo = self.findChild(EditableComboBox, 'conf_combo')
        # 添加新课表
        if conf_combo.currentText() not in list.get_schedule_config():
            if conf_combo.currentText().endswith('.json'):
                list.create_new_profile(conf_combo.currentText())
            else:
                list.create_new_profile(f'{conf_combo.currentText()}.json')
            if conf_combo.currentText().endswith('.json'):
                conf.write_conf('General', 'schedule', conf_combo.currentText())
            else:
                conf.write_conf('General', 'schedule', f'{conf_combo.currentText()}.json')
        # 添加新课表
        elif conf_combo.currentText() == '添加新课表':
            new_name = f'新课表 - {list.return_default_schedule_number() + 1}'
            list.create_new_profile(f'{new_name}.json')
            conf.write_conf('General', 'schedule', f'{new_name}.json')
        else:
            if conf_combo.currentText().endswith('.json'):
                conf.write_conf('General', 'schedule', conf_combo.currentText())
            else:
                conf.write_conf('General', 'schedule', f'{conf_combo.currentText()}.json')
        alert = MessageBox('您已切换课程表的配置文件',
                           '软件将在您确认后关闭，\n'
                           '您需重新打开设置菜单以设置您切换的配置文件。', self)
        alert.cancelButton.hide()  # 隐藏取消按钮，必须重启
        alert.buttonLayout.insertStretch(0, 1)
        if alert.exec():
            sys.exit()

    def sp_fill_grid_row(self):
        schedule_view = self.findChild(TableWidget, 'schedule_view')
        for i in range(len(schedule_dict)):
            for j in range(len(schedule_dict[str(i)])):
                item_text = schedule_dict[str(i)][j].split('-')[0]
                if item_text != '未添加':
                    item = QTableWidgetItem(item_text)
                else:
                    item = QTableWidgetItem('')
                schedule_view.setItem(j, i, item)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # 设置单元格文本居中对齐

    # 加载时间线
    def te_load_item(self, file=filename):
        global morning_st, afternoon_st
        loaded_data = conf.load_from_json(file)
        timeline = loaded_data.get('timeline')
        # 找控件
        te_m_start_time = self.findChild(TimePicker, 'morningStartTime')
        te_a_start_time = self.findChild(TimePicker, 'afternoonStartTime')
        te_timeline_list = self.findChild(ListWidget, 'timeline_list')

        for item_name, item_time in timeline.items():
            if item_name == 'start_time_m':
                if timeline[item_name]:
                    h = timeline[item_name][0]
                    m = timeline[item_name][1]
                    te_m_start_time.setTime(QTime(h, m))
                    morning_st = (h, m)
            elif item_name == 'start_time_a':
                if timeline[item_name]:
                    h = timeline[item_name][0]
                    m = timeline[item_name][1]
                    te_a_start_time.setTime(QTime(h, m))
                    afternoon_st = (h, m)
            else:
                prefix = ''
                period = ''
                item_time = f'{timeline[item_name]}分钟'
                # 判断前缀和时段
                if item_name.startswith('am'):
                    prefix = '课程/活动'
                    period = '上午'
                elif item_name.startswith('fm'):
                    prefix = '课间'
                    period = '上午'
                elif item_name.startswith('aa'):
                    prefix = '课程/活动'
                    period = '下午'
                elif item_name.startswith('fa'):
                    prefix = '课间'
                    period = '下午'
                # 还原 item_text
                item_text = f"{prefix}-{item_time}-{period}"
                te_timeline_list.addItem(item_text)
                self.te_detect_item()

    # 加载课表
    def se_load_item(self, file=filename):
        global schedule_dict
        loaded_data = conf.load_from_json(file)
        loaded_data_timeline = conf.load_from_json(file)
        timeline = loaded_data_timeline.get('timeline')
        schedule = loaded_data.get('schedule')
        for week, item in schedule.items():
            all_class = []
            morning_count = 0
            for item_name, item_time in timeline.items():
                if item_name.startswith('am'):
                    try:
                        prefix = item[int(item_name[-1])]
                        period = '上午'
                        all_class.append(f'{prefix}-{period}')
                    except Exception as e:
                        prefix = '未添加'
                        period = '上午'
                        all_class.append(f'{prefix}-{period}')
                    morning_count += 1
                elif item_name.startswith('aa'):
                    try:
                        prefix = item[int(item_name[-1]) + morning_count]
                        period = '下午'
                        all_class.append(f'{prefix}-{period}')
                    except Exception as e:
                        prefix = '未添加'
                        period = '下午'
                        all_class.append(f'{prefix}-{period}')
            schedule_dict[week] = all_class

    # 上传课表到列表组件
    def se_upload_list(self):
        se_schedule_list = self.findChild(ListWidget, 'schedule_list')
        se_schedule_list.clearSelection()
        se_week_combo = self.findChild(ComboBox, 'week_combo')
        global current_week
        current_week = se_week_combo.currentIndex()
        se_schedule_list.clear()
        se_schedule_list.addItems(schedule_dict[str(current_week)])

    def se_upload_item(self):
        se_schedule_list = self.findChild(ListWidget, 'schedule_list')
        global schedule_dict
        cache_list = []
        for i in range(se_schedule_list.count()):
            item_text = se_schedule_list.item(i).text()
            cache_list.append(item_text)
        schedule_dict[str(current_week)][:] = cache_list

    # 保存课表
    def se_save_item(self):
        data_dict = deepcopy(schedule_dict)
        for week, item in data_dict.items():
            cache_list = item
            replace_list = []
            for activity_num in range(len(cache_list)):
                item_info = cache_list[int(activity_num)].split('-')
                replace_list.append(item_info[0])
            data_dict[str(week)] = replace_list
        data_dict = {"schedule": data_dict}
        conf.save_data_to_json(data_dict, filename)
        Flyout.create(
            icon=InfoBarIcon.SUCCESS,
            title='保存成功',
            content=f"已保存至 ./config/schedule/{filename}",
            target=self.findChild(PrimaryPushButton, 'save_schedule'),
            parent=self,
            isClosable=True,
            aniType=FlyoutAnimationType.PULL_UP
        )
        self.sp_fill_grid_row()

    # 保存时间线
    def te_save_item(self, file=filename):
        file = filename
        te_timeline_list = self.findChild(ListWidget, 'timeline_list')
        data_dict = {"timeline": {}}
        # 逐条把列表里的信息整理保存
        data_dict['timeline']['start_time_m'] = morning_st
        data_dict['timeline']['start_time_a'] = afternoon_st
        m = 0
        for i in range(te_timeline_list.count()):
            item_text = te_timeline_list.item(i).text()
            item_info = item_text.split('-')
            item_name = ''
            if item_info[0] == '课程/活动':
                item_name += 'a'
            if item_info[0] == '课间':
                item_name += 'f'
            if item_info[2] == '上午':
                item_name += 'm'
                m += 1
                item_name += str(int(i / 2))
            if item_info[2] == '下午':
                item_name += 'a'
                item_name += str(int((i - m) / 2))
            if len(item_info[1]) == 4:
                item_time = item_info[1][:2]
            else:
                item_time = item_info[1][:1]
            data_dict['timeline'][item_name] = item_time
        conf.save_data_to_json(data_dict, file)
        self.se_load_item()
        self.se_upload_list()
        self.sp_fill_grid_row()
        Flyout.create(
            icon=InfoBarIcon.SUCCESS,
            title='保存成功',
            content=f"已保存至 ./config/schedule/{filename}",
            target=self.findChild(PrimaryPushButton, 'save'),
            parent=self,
            isClosable=True,
            aniType=FlyoutAnimationType.PULL_UP
        )

    def te_sync_time(self):
        te_class_activity_combo = self.findChild(ComboBox, 'class_activity')
        spin_time = self.findChild(SpinBox, 'spin_time')
        if te_class_activity_combo.currentIndex() == 0:
            spin_time.setValue(40)
        if te_class_activity_combo.currentIndex() == 1:
            spin_time.setValue(10)

    def te_detect_item(self):
        timeline_list = self.findChild(ListWidget, 'timeline_list')
        tips = self.findChild(CaptionLabel, 'tips')
        if timeline_list.count() > 0:
            tips.hide()
        else:
            tips.show()

    def te_add_item(self):
        te_timeline_list = self.findChild(ListWidget, 'timeline_list')
        class_activity = self.findChild(ComboBox, 'class_activity')
        spin_time = self.findChild(SpinBox, 'spin_time')
        time_period = self.findChild(ComboBox, 'time_period')
        te_timeline_list.addItem(
            f'{class_activity.currentText()}-{spin_time.value()}分钟-{time_period.currentText()}'
        )
        self.te_detect_item()

    def te_edit_item(self):
        te_timeline_list = self.findChild(ListWidget, 'timeline_list')
        class_activity = self.findChild(ComboBox, 'class_activity')
        spin_time = self.findChild(SpinBox, 'spin_time')
        time_period = self.findChild(ComboBox, 'time_period')
        selected_items = te_timeline_list.selectedItems()

        if selected_items:
            selected_item = selected_items[0]  # 取第一个选中的项目
            selected_item.setText(
                f'{class_activity.currentText()}-{spin_time.value()}分钟-{time_period.currentText()}'
            )

    def se_edit_item(self):
        se_schedule_list = self.findChild(ListWidget, 'schedule_list')
        se_class_combo = self.findChild(ComboBox, 'class_combo')
        se_custom_class_text = self.findChild(LineEdit, 'custom_class')
        selected_items = se_schedule_list.selectedItems()

        if selected_items:
            selected_item = selected_items[0]
            name_list = selected_item.text().split('-')
            if se_class_combo.currentIndex() != 0:
                selected_item.setText(
                    f'{se_class_combo.currentText()}-{name_list[1]}'
                )
            else:
                if se_custom_class_text.text() != '':
                    selected_item.setText(
                        f'{se_custom_class_text.text()}-{name_list[1]}'
                    )

    def te_delete_item(self):
        te_timeline_list = self.findChild(ListWidget, 'timeline_list')
        selected_items = te_timeline_list.selectedItems()
        for item in selected_items:
            te_timeline_list.takeItem(te_timeline_list.row(item))
        self.te_detect_item()

    def se_delete_item(self):
        se_schedule_list = self.findChild(ListWidget, 'schedule_list')
        selected_items = se_schedule_list.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            name_list = selected_item.text().split('-')
            selected_item.setText(
                f'未添加-{name_list[1]}'
            )

    def m_start_time_changed(self):
        global morning_st
        te_m_start_time = self.findChild(TimePicker, 'morningStartTime')
        unformatted_time = te_m_start_time.time
        h = unformatted_time.hour()
        m = unformatted_time.minute()
        morning_st = (h, m)

    def a_start_time_changed(self):
        global afternoon_st
        te_m_start_time = self.findChild(TimePicker, 'afternoonStartTime')
        unformatted_time = te_m_start_time.time
        h = unformatted_time.hour()
        m = unformatted_time.minute()
        afternoon_st = (h, m)

    def init_nav(self):
        self.addSubInterface(self.spInterface, fIcon.HOME, '课表预览')
        self.addSubInterface(self.teInterface, fIcon.DATE_TIME, '时间线编辑')
        self.addSubInterface(self.seInterface, fIcon.EDUCATION, '课程表编辑')
        self.addSubInterface(self.adInterface, fIcon.SETTING, '高级选项', NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.ifInterface, fIcon.INFO, '关于本产品', NavigationItemPosition.BOTTOM)

    def init_window(self):
        self.stackedWidget.setCurrentIndex(0)  # 设置初始页面
        self.load_all_item()
        self.resize(width, height)
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)
        self.navigationInterface.setExpandWidth(250)
        self.navigationInterface.setCollapsible(False)

        setTheme(Theme.AUTO)
        setThemeColor('#36ABCF')

        self.move(300, 110)
        self.setWindowTitle('Class Widgets - 设置')
        self.setWindowIcon(QIcon('img/favicon.png'))


def sp_get_class_num():
    file = filename
    loaded_data_timeline = conf.load_from_json(file)
    timeline = loaded_data_timeline.get('timeline')
    count = 0
    for item_name, item_time in timeline.items():
        if item_name.startswith('a'):
            count += 1
    return count


if __name__ == '__main__':
    app = QApplication(sys.argv)
    if sys.platform == 'win32' and sys.getwindowsversion().build >= 22000:  # 修改在win11高版本阴影异常
        app.setStyle("fusion")
    application = desktop_widget()
    application.show()
    sys.exit(app.exec())
