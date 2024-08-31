import os

from PyQt6 import uic
from PyQt6.QtCore import Qt, QTime, QUrl, QDate
import sys

from PyQt6.QtGui import QIcon, QDesktopServices, QPixmap
from PyQt6.QtWidgets import QApplication, QHeaderView, QTableWidgetItem, QLabel, QHBoxLayout, QSizePolicy, QSpacerItem
from qfluentwidgets import (
    Theme, setTheme, FluentWindow, FluentIcon as fIcon, ToolButton, ListWidget, ComboBox, CaptionLabel,
    SpinBox, TimePicker, LineEdit, PrimaryPushButton, TableWidget, Flyout, InfoBarIcon,
    FlyoutAnimationType, NavigationItemPosition, MessageBox, SubtitleLabel, PushButton, SwitchButton,
    CalendarPicker,
)
from copy import deepcopy
from loguru import logger
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
schedule_even_dict = {}  # 对应时间线的课程表（双周）


class desktop_widget(FluentWindow):
    def __init__(self):
        super().__init__()
        # 设置窗口无边框和透明背景
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        try:
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
            self.ctInterface = uic.loadUi('menu-custom.ui')
            self.ctInterface.setObjectName("ctInterface")

            self.init_nav()
            self.init_window()
        except Exception as e:
            logger.error(f'初始化设置界面时发生错误：{e}')
            print(f'初始化设置界面时发生错误：{e}')

    def load_all_item(self):
        self.setup_timeline_edit()
        self.setup_schedule_edit()
        self.setup_schedule_preview()
        self.setup_advance_interface()
        self.setup_about_interface()
        self.setup_customization_interface()

    # 初始化界面
    def setup_customization_interface(self):
        self.ct_update_preview()

        widgets_list = self.findChild(ListWidget, 'widgets_list')
        widgets_list.addItems((list.widget_name[key] for key in list.get_widget_config()))

        switch_countdown_custom = self.findChild(SwitchButton, 'switch_countdown_custom')
        switch_countdown_custom.setChecked(conf.get_is_widget_in('widget-countdown-custom.ui'))
        switch_countdown_custom.checkedChanged.connect(self.switch_countdown_custom)

        save_config_button = self.findChild(PrimaryPushButton, 'save_config')
        save_config_button.clicked.connect(self.ct_save_widget_config)

        set_wcc_title = self.findChild(LineEdit, 'set_wcc_title')  # 倒计时标题
        set_wcc_title.setText(conf.read_conf('Date', 'cd_text_custom'))
        set_wcc_title.textChanged.connect(lambda: conf.write_conf('Date', 'cd_text_custom', set_wcc_title.text()))

        set_countdown_date = self.findChild(CalendarPicker, 'set_countdown_date')  # 倒计时日期
        if conf.read_conf('Date', 'countdown_date') != '':
            set_countdown_date.setDate(QDate.fromString(conf.read_conf('Date', 'countdown_date'), 'yyyy-M-d'))
        set_countdown_date.dateChanged.connect(
            lambda: conf.write_conf(
                'Date', 'countdown_date', set_countdown_date.date.toString('yyyy-M-d'))
        )

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

        conf_combo = self.findChild(ComboBox, 'conf_combo')
        conf_combo.addItems(list.get_schedule_config())
        conf_combo.setCurrentIndex(list.get_schedule_config().index(conf.read_conf('General', 'schedule')))
        conf_combo.currentIndexChanged.connect(self.ad_change_file)  # 切换配置文件

        conf_name = self.findChild(LineEdit, 'conf_name')
        conf_name.setText(filename[:-5])
        conf_name.textChanged.connect(self.ad_change_file_name)

        switch_pin_button = self.findChild(SwitchButton, 'switch_pin_button')
        switch_pin_button.setChecked(int(conf.read_conf('General', 'pin_on_top')))
        switch_pin_button.checkedChanged.connect(self.switch_pin)  # 置顶开关

        switch_startup = self.findChild(SwitchButton, 'switch_startup')
        switch_startup.setChecked(int(conf.read_conf('General', 'auto_startup')))
        switch_startup.checkedChanged.connect(self.switch_startup)  # 开机自启

        switch_auto_hide = self.findChild(SwitchButton, 'switch_auto_hide')
        switch_auto_hide.setChecked(int(conf.read_conf('General', 'auto_hide')))
        switch_auto_hide.checkedChanged.connect(self.switch_auto_hide)  # 自动隐藏

        switch_enable_toast = self.findChild(SwitchButton, 'switch_enable_toast')
        switch_enable_toast.setChecked(int(conf.read_conf('General', 'enable_toast')))
        switch_enable_toast.checkedChanged.connect(self.switch_enable_toast)  # 通知开关

        switch_enable_alt_schedule = self.findChild(SwitchButton, 'switch_enable_alt_schedule')
        switch_enable_alt_schedule.setChecked(int(conf.read_conf('General', 'enable_alt_schedule')))
        switch_enable_alt_schedule.checkedChanged.connect(self.switch_enable_alt_schedule)  # 单双周开关

        set_start_date = self.findChild(CalendarPicker, 'set_start_date')  # 倒计时日期
        if conf.read_conf('Date', 'start_date') != '':
            set_start_date.setDate(QDate.fromString(conf.read_conf('Date', 'start_date'), 'yyyy-M-d'))
        set_start_date.dateChanged.connect(
            lambda: conf.write_conf('Date', 'start_date', set_start_date.date.toString('yyyy-M-d')))  # 开学日期

        offset_spin = self.findChild(SpinBox, 'offset_spin')
        offset_spin.setValue(int(conf.read_conf('General', 'time_offset')))
        offset_spin.valueChanged.connect(
            lambda: conf.write_conf('General', 'time_offset', str(offset_spin.value()))
        )  # 保存时差偏移


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

        se_week_type_combo = self.findChild(ComboBox, 'week_type_combo')
        se_week_type_combo.addItems(list.week_type)
        se_week_type_combo.currentIndexChanged.connect(self.se_upload_list)

        se_copy_schedule_button = self.findChild(PushButton, 'copy_schedule')
        se_copy_schedule_button.hide()
        se_copy_schedule_button.clicked.connect(self.se_copy_odd_schedule)


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

        sp_week_type_combo = self.findChild(ComboBox, 'pre_week_type_combo')
        sp_week_type_combo.addItems(list.week_type)
        sp_week_type_combo.currentIndexChanged.connect(self.sp_fill_grid_row)

        # 设置表格
        schedule_view.setColumnCount(7)
        schedule_view.setHorizontalHeaderLabels(list.week[0:7])
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

    def switch_auto_hide(self):
        switch_auto_hide = self.findChild(SwitchButton, 'switch_auto_hide')
        if switch_auto_hide.isChecked():
            conf.write_conf('General', 'auto_hide', '1')
        else:
            conf.write_conf('General', 'auto_hide', '0')

    def switch_enable_toast(self):
        switch_enable_toast = self.findChild(SwitchButton, 'switch_enable_toast')
        if switch_enable_toast.isChecked():
            conf.write_conf('General', 'enable_toast', '1')
        else:
            conf.write_conf('General', 'enable_toast', '0')

    def switch_countdown_custom(self):
        widgets_list = self.findChild(ListWidget, 'widgets_list')
        switch_countdown_custom = self.findChild(SwitchButton, 'switch_countdown_custom')
        if switch_countdown_custom.isChecked():
            widgets_list.addItem(list.widget_name['widget-countdown-custom.ui'])
        else:
            target = list.widget_name['widget-countdown-custom.ui']
            items = [widgets_list.item(i).text() for i in range(widgets_list.count())]
            if target in items:
                row_to_remove = items.index(target)
                widgets_list.takeItem(row_to_remove)

    def switch_enable_alt_schedule(self):
        switch_enable_alt_schedule = self.findChild(SwitchButton, 'switch_enable_alt_schedule')
        if switch_enable_alt_schedule.isChecked():
            conf.write_conf('General', 'enable_alt_schedule', '1')
        else:
            conf.write_conf('General', 'enable_alt_schedule', '0')

    def ct_save_widget_config(self):
        widgets_list = self.findChild(ListWidget, 'widgets_list')
        widget_config = {'widgets': []}
        for i in range(widgets_list.count()):
            widget_config['widgets'].append(list.widget_conf[widgets_list.item(i).text()])
        if conf.save_widget_conf_to_json(widget_config):
            self.ct_update_preview()
            Flyout.create(
                icon=InfoBarIcon.SUCCESS,
                title='保存成功',
                content=f"已保存至 ./config/widget.json",
                target=self.findChild(PrimaryPushButton, 'save_config'),
                parent=self,
                isClosable=True,
                aniType=FlyoutAnimationType.PULL_UP
            )

    def ct_update_preview(self):
        try:
            widgets_preview = self.findChild(QHBoxLayout, 'widgets_preview')
            # 获取配置列表
            widget_config = list.get_widget_config()
            while widgets_preview.count() > 0:  # 清空预览界面
                item = widgets_preview.itemAt(0)
                if item:
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()
                    widgets_preview.removeItem(item)

            left_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            widgets_preview.addItem(left_spacer)
            for i in range(len(widget_config)):
                widget_name = widget_config[i]
                label = QLabel()
                label.setPixmap(QPixmap(f'img/settings/{widget_name[:-3]}.png'))
                widgets_preview.addWidget(label)
                widget_config[i] = label
            right_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            widgets_preview.addItem(right_spacer)
        except Exception as e:
            print(f'更新预览界面时发生错误：{e}')
            logger.error(f'更新预览界面时发生错误：{e}')

    def ad_change_file_name(self):
        global filename
        try:
            conf_name = self.findChild(LineEdit, 'conf_name')
            old_name = filename
            new_name = conf_name.text()
            os.rename(f'config/schedule/{old_name}', f'config/schedule/{new_name}.json')  # 重命名
            conf.write_conf('General', 'schedule', f'{new_name}.json')
            filename = new_name + '.json'
        except Exception as e:
            print(f'修改配置文件名称时发生错误：{e}')
            logger.error(f'修改配置文件名称时发生错误：{e}')


    def ad_change_file(self):
        try:
            conf_combo = self.findChild(ComboBox, 'conf_combo')
            # 添加新课表
            if conf_combo.currentText() == '添加新课表':
                new_name = f'新课表 - {list.return_default_schedule_number() + 1}'
                list.create_new_profile(f'{new_name}.json')
                conf.write_conf('General', 'schedule', f'{new_name}.json')
            else:
                if conf_combo.currentText().endswith('.json'):
                    conf.write_conf('General', 'schedule', conf_combo.currentText())
        except Exception as e:
            print(f'切换配置文件时发生错误：{e}')
            logger.error(f'切换配置文件时发生错误：{e}')
        alert = MessageBox('您已切换课程表的配置文件',
                           '软件将在您确认后关闭，\n'
                           '您需重新打开设置菜单以设置您切换的配置文件。', self)
        alert.cancelButton.hide()  # 隐藏取消按钮，必须重启
        alert.buttonLayout.insertStretch(0, 1)
        if alert.exec():
            self.close()

    def sp_fill_grid_row(self):  # 填充预览表格
        sp_week_type_combo = self.findChild(ComboBox, 'pre_week_type_combo')
        schedule_view = self.findChild(TableWidget, 'schedule_view')
        schedule_view.setRowCount(sp_get_class_num())
        if sp_week_type_combo.currentIndex() == 1:
            schedule_dict_sp = schedule_even_dict
        else:
            schedule_dict_sp = schedule_dict
        for i in range(len(schedule_dict_sp)):
            for j in range(len(schedule_dict_sp[str(i)])):
                item_text = schedule_dict_sp[str(i)][j].split('-')[0]
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
        global schedule_even_dict
        loaded_data = conf.load_from_json(file)
        loaded_data_timeline = conf.load_from_json(file)
        timeline = loaded_data_timeline.get('timeline')
        schedule = loaded_data.get('schedule')
        schedule_even = loaded_data.get('schedule_even')
        if schedule is None:
            schedule_even = deepcopy(schedule)
            self.se_save_item()
        for week, item in schedule.items():
            all_class = []
            morning_count = 0
            for item_name, item_time in timeline.items():
                if item_name.startswith('am'):
                    try:
                        prefix = item[int(item_name[-1])-1]
                        period = '上午'
                        all_class.append(f'{prefix}-{period}')
                    except Exception as e:
                        prefix = '未添加'
                        period = '上午'
                        all_class.append(f'{prefix}-{period}')
                    morning_count += 1
                elif item_name.startswith('aa'):
                    try:
                        prefix = item[int(item_name[-1]) + morning_count-1]
                        period = '下午'
                        all_class.append(f'{prefix}-{period}')
                    except Exception as e:
                        prefix = '未添加'
                        period = '下午'
                        all_class.append(f'{prefix}-{period}')
            schedule_dict[week] = all_class
        for week, item in schedule_even.items():
            all_class = []
            morning_count = 0
            for item_name, item_time in timeline.items():
                if item_name.startswith('am'):
                    try:
                        prefix = item[int(item_name[-1]) - 1]
                        period = '上午'
                        all_class.append(f'{prefix}-{period}')
                    except Exception as e:
                        prefix = '未添加'
                        period = '上午'
                        all_class.append(f'{prefix}-{period}')
                    morning_count += 1
                elif item_name.startswith('aa'):
                    try:
                        prefix = item[int(item_name[-1]) + morning_count - 1]
                        period = '下午'
                        all_class.append(f'{prefix}-{period}')
                    except Exception as e:
                        prefix = '未添加'
                        period = '下午'
                        all_class.append(f'{prefix}-{period}')
            schedule_even_dict[week] = all_class

    def se_copy_odd_schedule(self):
        logger.info('复制单周课表')
        global schedule_dict, schedule_even_dict
        schedule_even_dict = deepcopy(schedule_dict)
        self.se_upload_list()

    # 上传课表到列表组件
    def se_upload_list(self):
        logger.info('更新列表：课程表编辑')
        se_schedule_list = self.findChild(ListWidget, 'schedule_list')
        se_schedule_list.clearSelection()
        se_week_combo = self.findChild(ComboBox, 'week_combo')
        se_week_type_combo = self.findChild(ComboBox, 'week_type_combo')
        se_copy_schedule_button = self.findChild(PushButton, 'copy_schedule')
        global current_week
        if se_week_type_combo.currentIndex() == 1:
            se_copy_schedule_button.show()
            current_week = se_week_combo.currentIndex()
            se_schedule_list.clear()
            se_schedule_list.addItems(schedule_even_dict[str(current_week)])
        else:
            se_copy_schedule_button.hide()
            current_week = se_week_combo.currentIndex()
            se_schedule_list.clear()
            se_schedule_list.addItems(schedule_dict[str(current_week)])

    def se_upload_item(self):
        se_schedule_list = self.findChild(ListWidget, 'schedule_list')
        se_week_type_combo = self.findChild(ComboBox, 'week_type_combo')
        if se_week_type_combo.currentIndex() == 1:
            global schedule_even_dict
            try:
                cache_list = []
                for i in range(se_schedule_list.count()):
                    item_text = se_schedule_list.item(i).text()
                    cache_list.append(item_text)
                schedule_even_dict[str(current_week)][:] = cache_list
            except Exception as e:
                print(f'上传双周课表时发生错误：{e}')
        else:
            global schedule_dict
            cache_list = []
            for i in range(se_schedule_list.count()):
                item_text = se_schedule_list.item(i).text()
                cache_list.append(item_text)
            schedule_dict[str(current_week)][:] = cache_list

    # 保存课表
    def se_save_item(self):
        try:
            data_dict = deepcopy(schedule_dict)
            data_dict_even = deepcopy(schedule_even_dict)  #单双周保存
            for week, item in data_dict.items():
                cache_list = item
                replace_list = []
                for activity_num in range(len(cache_list)):
                    item_info = cache_list[int(activity_num)].split('-')
                    replace_list.append(item_info[0])
                data_dict[str(week)] = replace_list
            for week, item in data_dict_even.items():
                cache_list = item
                replace_list = []
                for activity_num in range(len(cache_list)):
                    item_info = cache_list[int(activity_num)].split('-')
                    replace_list.append(item_info[0])
                data_dict_even[str(week)] = replace_list
            # 写入
            data_dict_even = {"schedule_even": data_dict_even}
            conf.save_data_to_json(data_dict_even, filename)
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
        except Exception as e:
            logger.error(f'保存课表时发生错误: {e}')


    # 保存时间线
    def te_save_item(self, file=filename):
        file = filename
        te_timeline_list = self.findChild(ListWidget, 'timeline_list')
        data_dict = {"timeline": {}}
        # 逐条把列表里的信息整理保存
        data_dict['timeline']['start_time_m'] = morning_st
        data_dict['timeline']['start_time_a'] = afternoon_st
        m = 0
        counter = 0
        for i in range(te_timeline_list.count()):
            item_text = te_timeline_list.item(i).text()
            item_info = item_text.split('-')
            item_name = ''
            if item_info[0] == '课程/活动':
                item_name += 'a'
                counter += 1
            if item_info[0] == '课间':
                item_name += 'f'
            if item_info[2] == '上午':
                item_name += 'm'
                if item_info[0] == '课程/活动':  # 修复 Bug
                    m += 1
                item_name += str(counter)
            if item_info[2] == '下午':
                item_name += 'a'
                item_name += str(counter - m)
            # 修复 3 位数保存 Bug
            item_time = item_info[1][0:len(item_info[1]) - 2]
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
        self.addSubInterface(self.ctInterface, fIcon.BRUSH, '自定义', NavigationItemPosition.BOTTOM)
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

        self.move(300, 110)
        self.setWindowTitle('Class Widgets - 设置')
        self.setWindowIcon(QIcon('img/favicon-settings.ico'))

    def closeEvent(self, event):
        event.ignore()
        self.hide()


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
