import os
from shutil import rmtree

import requests
from PyQt6 import uic, QtCore
from PyQt6.QtCore import Qt, QTime, QUrl, QDate, QThread, pyqtSignal
from qframelesswindow.webengine import FramelessWebEngineView
import sys

from PyQt6.QtGui import QIcon, QDesktopServices, QPixmap, QColor, QFontDatabase
from PyQt6.QtWidgets import QApplication, QHeaderView, QTableWidgetItem, QLabel, QHBoxLayout, QSizePolicy, QSpacerItem, \
    QFileDialog, QVBoxLayout, QTextBrowser
from qfluentwidgets import (
    Theme, setTheme, FluentWindow, FluentIcon as fIcon, ToolButton, ListWidget, ComboBox, CaptionLabel,
    SpinBox, LineEdit, PrimaryPushButton, TableWidget, Flyout, InfoBarIcon,
    FlyoutAnimationType, NavigationItemPosition, MessageBox, SubtitleLabel, PushButton, SwitchButton,
    CalendarPicker, BodyLabel, ColorDialog, isDarkTheme, TimeEdit, EditableComboBox, SegmentedWidget, MessageBoxBase,
    SearchLineEdit, Slider, PlainTextEdit, TextEdit
)
from copy import deepcopy
from loguru import logger
import datetime as dt
import list
import conf
import tip_toast as toast
import weather_db as wd

today = dt.date.today()

width = 1200
height = 800

morning_st = 0
afternoon_st = 0

current_week = 0

filename = conf.read_conf('General', 'schedule')
loaded_data = conf.load_from_json(filename)

schedule_dict = {}  # 对应时间线的课程表
schedule_even_dict = {}  # 对应时间线的课程表（双周）

timeline_dict = {}  # 时间线字典


def get_timeline():
    global loaded_data
    loaded_data = conf.load_from_json(filename)
    return loaded_data['timeline']


class VersionThread(QThread):  # 获取最新版本号
    version_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        version = self.get_latest_version()
        self.version_signal.emit(version)

    def get_latest_version(self):
        url = "https://api.github.com/repos/RinLit-233-shiroko/Class-Widgets/releases/latest"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get("tag_name")
            else:
                return f"无法获取版本信息 错误代码：{response.status_code}"
        except requests.exceptions.RequestException as e:
            return f"请求失败: {e}"


class selectCity(MessageBoxBase):  # 选择城市
    def __init__(self, parent=None):
        super().__init__(parent)
        title_label = SubtitleLabel('搜索城市')
        subtitle_label = BodyLabel('请输入当地城市名进行搜索')
        self.search_edit = SearchLineEdit()

        self.search_edit.setPlaceholderText('输入城市名')
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self.search_city)

        self.city_list = ListWidget()
        self.city_list.addItems(wd.search_by_name(''))
        self.get_selected_city()

        # 将组件添加到布局中
        self.viewLayout.addWidget(title_label)
        self.viewLayout.addWidget(subtitle_label)
        self.viewLayout.addWidget(self.search_edit)
        self.viewLayout.addWidget(self.city_list)
        self.widget.setMinimumWidth(500)
        self.widget.setMinimumHeight(600)

    def search_city(self):
        self.city_list.clear()
        self.city_list.addItems(wd.search_by_name(self.search_edit.text()))

    def get_selected_city(self):
        selected_city = self.city_list.findItems(
            wd.search_by_num(str(conf.read_conf('Weather', 'city'))), QtCore.Qt.MatchFlag.MatchExactly
        )
        if selected_city:  # 若找到该城市
            item = selected_city[0]
            # 选中该项
            self.city_list.setCurrentItem(item)
            # 聚焦该项
            self.city_list.scrollToItem(item)


class licenseDialog(MessageBoxBase):  # 显示软件许可协议
    def __init__(self, parent=None):
        super().__init__(parent)
        title_label = SubtitleLabel('软件许可协议')
        subtitle_label = BodyLabel('此项目 (Class Widgets) 基于 GPL-3.0 许可证授权发布，详情请参阅：')
        self.license_text = PlainTextEdit()
        self.license_text.setPlainText(open('LICENSE', 'r', encoding='utf-8').read())
        self.license_text.setReadOnly(True)

        # 将组件添加到布局中
        self.viewLayout.addWidget(title_label)
        self.viewLayout.addWidget(subtitle_label)
        self.viewLayout.addWidget(self.license_text)
        self.widget.setMinimumWidth(700)
        self.widget.setMinimumHeight(600)


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
            self.cfInterface = uic.loadUi('menu-configs.ui')
            self.cfInterface.setObjectName("cfInterface")
            self.sdInterface = uic.loadUi('menu-sound.ui')
            self.sdInterface.setObjectName("sdInterface")
            self.hdInterface = uic.loadUi('menu-help.ui')
            self.hdInterface.setObjectName("hdInterface")

            self.init_nav()
            self.init_window()
        except Exception as e:
            logger.error(f'初始化设置界面时发生错误：{e}')

    def init_font(self):  # 设置字体
        self.setStyleSheet("""QLabel {
                    font: 'Microsoft YaHei';
                }""")

    def load_all_item(self):
        self.setup_timeline_edit()
        self.setup_schedule_edit()
        self.setup_schedule_preview()
        self.setup_advance_interface()
        self.setup_about_interface()
        self.setup_customization_interface()
        self.setup_configs_interface()
        self.setup_sound_interface()
        self.setup_help_interface()

    # 初始化界面
    def setup_help_interface(self):
        help_docu = FramelessWebEngineView(self)
        help_docu.load(QUrl("https://www.yuque.com/rinlit/class-widgets_help?#"))
        help_docu.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        open_by_browser = self.findChild(PushButton, 'open_by_browser')
        open_by_browser.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(
            'https://www.yuque.com/rinlit/class-widgets_help?#'
        )))

        web_layout = self.findChild(QVBoxLayout, 'web')
        web_layout.addWidget(help_docu)

    def setup_sound_interface(self):
        switch_enable_toast = self.findChild(SwitchButton, 'switch_enable_toast')
        switch_enable_toast.setChecked(int(conf.read_conf('General', 'enable_toast')))
        switch_enable_toast.checkedChanged.connect(self.switch_enable_toast)  # 通知开关

        slider_volume = self.findChild(Slider, 'slider_volume')
        slider_volume.setValue(int(conf.read_conf('Audio', 'volume')))
        slider_volume.valueChanged.connect(self.save_volume)  # 音量滑块

        preview_toast_button = self.findChild(PushButton, 'preview_toast_bar')
        preview_toast_button.clicked.connect(lambda: toast.main(
            4, title='通知', subtitle='测试通知', content='这是一条测试通知'
        ))  # 预览通知栏

        switch_wave_effect = self.findChild(SwitchButton, 'switch_enable_wave')
        switch_wave_effect.setChecked(int(conf.read_conf('Toast', 'wave')))
        switch_wave_effect.checkedChanged.connect(self.switch_wave_effect)  # 波纹开关

        spin_prepare_time = self.findChild(SpinBox, 'spin_prepare_class')
        spin_prepare_time.setValue(int(conf.read_conf('Toast', 'prepare_minutes')))
        spin_prepare_time.valueChanged.connect(self.save_prepare_time)  # 准备时间

    def setup_configs_interface(self):  # 配置界面
        cf_import_schedule = self.findChild(PushButton, 'im_schedule')
        cf_import_schedule.clicked.connect(self.cf_import_schedule)  # 导入课程表
        cf_export_schedule = self.findChild(PushButton, 'ex_schedule')
        cf_export_schedule.clicked.connect(self.cf_export_schedule)  # 导出课程表
        cf_open_schedule_folder = self.findChild(PushButton, 'open_schedule_folder')  # 打开课程表文件夹
        cf_open_schedule_folder.clicked.connect(lambda: os.startfile(os.path.join(os.getcwd(), 'config/schedule')))

    def setup_customization_interface(self):
        self.ct_update_preview()

        widgets_list = self.findChild(ListWidget, 'widgets_list')
        widgets_list.addItems((list.widget_name[key] for key in list.get_widget_config()))

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

        set_ac_color = self.findChild(PushButton, 'set_ac_color')  # 主题色
        set_ac_color.clicked.connect(self.ct_set_ac_color)
        set_fc_color = self.findChild(PushButton, 'set_fc_color')
        set_fc_color.clicked.connect(self.ct_set_fc_color)

        select_theme_combo = self.findChild(ComboBox, 'combo_theme_select')  # 主题选择
        select_theme_combo.addItems(list.theme_names)
        select_theme_combo.setCurrentIndex(list.get_current_theme_num())
        select_theme_combo.currentIndexChanged.connect(self.ct_change_theme)

        color_mode_combo = self.findChild(ComboBox, 'combo_color_mode')  # 颜色模式选择
        color_mode_combo.addItems(list.color_mode)
        color_mode_combo.setCurrentIndex(int(conf.read_conf('General', 'color_mode')))
        color_mode_combo.currentIndexChanged.connect(self.ct_change_color_mode)

        widgets_combo = self.findChild(ComboBox, 'widgets_combo')  # 组件选择
        widgets_combo.addItems(list.get_widget_names())

        search_city_button = self.findChild(PushButton, 'select_city')
        search_city_button.clicked.connect(self.show_search_city)

        add_widget_button = self.findChild(PrimaryPushButton, 'add_widget')
        add_widget_button.clicked.connect(self.ct_add_widget)

        remove_widget_button = self.findChild(PushButton, 'remove_widget')
        remove_widget_button.clicked.connect(self.ct_remove_widget)

        slider_opacity = self.findChild(Slider, 'slider_opacity')
        slider_opacity.setValue(int(conf.read_conf('General', 'opacity')))
        slider_opacity.valueChanged.connect(
            lambda: conf.write_conf('General', 'opacity', str(slider_opacity.value()))
        )  # 透明度

    def setup_about_interface(self):
        self.version = self.findChild(BodyLabel, 'version')
        self.version.setText(f'当前版本：{conf.read_conf("Other", "version")}\n正在检查最新版本…')

        self.version_thread = VersionThread()
        self.version_thread.version_signal.connect(self.ab_check_update)
        self.version_thread.start()

        github_page = self.findChild(PushButton, "button_github")
        github_page.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(
            'https://github.com/RinLit-233-shiroko/Class-Widgets')))

        bilibili_page = self.findChild(PushButton, 'button_bilibili')
        bilibili_page.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(
            'https://space.bilibili.com/569522843')))

        license_button = self.findChild(PushButton, 'button_show_license')
        license_button.clicked.connect(self.show_license)

        thanks_button = self.findChild(PushButton, 'button_thanks')
        thanks_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(
            'https://github.com/RinLit-233-shiroko/Class-Widgets?tab=readme-ov-file#致谢')))

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

        hide_mode_combo = self.findChild(ComboBox, 'hide_mode_combo')
        hide_mode_combo.addItems(list.hide_mode)
        hide_mode_combo.setCurrentIndex(int(conf.read_conf('General', 'hide')))
        hide_mode_combo.currentIndexChanged.connect(
            lambda: conf.write_conf('General', 'hide', str(hide_mode_combo.currentIndex()))
        )  # 隐藏模式

        switch_enable_alt_schedule = self.findChild(SwitchButton, 'switch_enable_alt_schedule')
        switch_enable_alt_schedule.setChecked(int(conf.read_conf('General', 'enable_alt_schedule')))
        switch_enable_alt_schedule.checkedChanged.connect(self.switch_enable_alt_schedule)  # 单双周开关

        switch_enable_multiple_programs = self.findChild(SwitchButton, 'switch_multiple_programs')
        switch_enable_multiple_programs.setChecked(int(conf.read_conf('Other', 'multiple_programs')))
        switch_enable_multiple_programs.checkedChanged.connect(self.switch_enable_multiple_programs)  # 多开

        switch_disable_log = self.findChild(SwitchButton, 'switch_disable_log')
        switch_disable_log.setChecked(int(conf.read_conf('Other', 'do_not_log')))
        switch_disable_log.checkedChanged.connect(self.switch_disable_log)  # 禁用日志

        button_clear_log = self.findChild(PushButton, 'button_clear_log')
        button_clear_log.clicked.connect(self.clear_log)  # 清空日志

        set_start_date = self.findChild(CalendarPicker, 'set_start_date')  # 日期
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

        quick_set_schedule = self.findChild(ListWidget, 'subject_list')
        quick_set_schedule.addItems(list.class_kind[1:])
        quick_set_schedule.itemClicked.connect(self.se_quick_set_schedule)

        quick_select_week_button = self.findChild(PushButton, 'quick_select_week')
        quick_select_week_button.clicked.connect(self.se_quick_select_week)

    def setup_timeline_edit(self):  # 底层大改
        self.te_load_item()  # 加载时段
        # teInterface
        te_add_button = self.findChild(ToolButton, 'add_button')  # 添加
        te_add_button.setIcon(fIcon.ADD)
        te_add_button.clicked.connect(self.te_add_item)
        te_add_button.clicked.connect(self.te_upload_item)

        te_add_part_button = self.findChild(ToolButton, 'add_part_button')  # 添加节点
        te_add_part_button.setIcon(fIcon.ADD)
        te_add_part_button.clicked.connect(self.te_add_part)

        te_name_edit = self.findChild(EditableComboBox, 'name_part_combo')  # 名称
        te_name_edit.addItems(list.time)

        te_delete_part_button = self.findChild(ToolButton, 'delete_part_button')  # 删除节点
        te_delete_part_button.setIcon(fIcon.DELETE)
        te_delete_part_button.clicked.connect(self.te_delete_part)

        te_edit_button = self.findChild(ToolButton, 'edit_button')  # 编辑
        te_edit_button.setIcon(fIcon.EDIT)
        te_edit_button.clicked.connect(self.te_edit_item)

        te_delete_button = self.findChild(ToolButton, 'delete_button')  # 删除
        te_delete_button.setIcon(fIcon.DELETE)
        te_delete_button.clicked.connect(self.te_delete_item)
        te_delete_button.clicked.connect(self.te_upload_item)

        te_class_activity_combo = self.findChild(ComboBox, 'class_activity')  # 活动类型
        te_class_activity_combo.addItems(list.class_activity)
        te_class_activity_combo.currentIndexChanged.connect(self.te_sync_time)

        te_select_timeline = self.findChild(ComboBox, 'select_timeline')  # 选择时间线
        te_select_timeline.addItem('默认')
        te_select_timeline.addItems(list.week)
        te_select_timeline.currentIndexChanged.connect(self.te_upload_list)

        te_timeline_list = self.findChild(ListWidget, 'timeline_list')  # 所选时间线列表
        te_timeline_list.addItems(timeline_dict['default'])
        te_timeline_list.itemChanged.connect(self.te_upload_item)

        te_save_button = self.findChild(PrimaryPushButton, 'save')  # 保存
        te_save_button.clicked.connect(self.te_save_item)

        self.te_detect_item()

    def setup_schedule_preview(self):
        subtitle = self.findChild(SubtitleLabel, 'subtitle_file')
        subtitle.setText(f'预览  -  {filename[:-5]}')

        schedule_view = self.findChild(TableWidget, 'schedule_view')
        schedule_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # 使列表自动等宽

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

    def save_volume(self):
        slider_volume = self.findChild(Slider, 'slider_volume')
        conf.write_conf('Audio', 'volume', str(slider_volume.value()))

    def show_search_city(self):
        search_city_dialog = selectCity(self)
        if search_city_dialog.exec():
            selected_city = search_city_dialog.city_list.selectedItems()
            if selected_city:
                conf.write_conf('Weather', 'city', wd.search_code_by_name(selected_city[0].text()))

    def show_license(self):
        license_dialog = licenseDialog(self)
        license_dialog.exec()

    def switch_disable_log(self):
        switch_disable_log = self.findChild(SwitchButton, 'switch_disable_log')
        if switch_disable_log.isChecked():
            conf.write_conf('Other', 'do_not_log', '1')
        else:
            conf.write_conf('Other', 'do_not_log', '0')

    def switch_pin(self):
        switch_pin_button = self.findChild(SwitchButton, 'switch_pin_button')
        if switch_pin_button.isChecked():
            conf.write_conf('General', 'pin_on_top', '1')
        else:
            conf.write_conf('General', 'pin_on_top', '0')

    def switch_wave_effect(self):
        switch_wave_effect = self.findChild(SwitchButton, 'switch_enable_wave')
        if switch_wave_effect.isChecked():
            conf.write_conf('Toast', 'wave', '1')
        else:
            conf.write_conf('Toast', 'wave', '0')

    def switch_startup(self):
        switch_startup = self.findChild(SwitchButton, 'switch_startup')
        if switch_startup.isChecked():
            conf.write_conf('General', 'auto_startup', '1')
            conf.add_to_startup('ClassWidgets.exe', 'img/favicon.ico')
        else:
            conf.write_conf('General', 'auto_startup', '0')
            conf.remove_from_startup()

    def switch_enable_toast(self):
        switch_enable_toast = self.findChild(SwitchButton, 'switch_enable_toast')
        if switch_enable_toast.isChecked():
            conf.write_conf('General', 'enable_toast', '1')
        else:
            conf.write_conf('General', 'enable_toast', '0')

    def switch_enable_alt_schedule(self):
        switch_enable_alt_schedule = self.findChild(SwitchButton, 'switch_enable_alt_schedule')
        if switch_enable_alt_schedule.isChecked():
            conf.write_conf('General', 'enable_alt_schedule', '1')
        else:
            conf.write_conf('General', 'enable_alt_schedule', '0')

    def switch_enable_multiple_programs(self):
        switch_enable_multiple_programs = self.findChild(SwitchButton, 'switch_multiple_programs')
        if switch_enable_multiple_programs.isChecked():
            conf.write_conf('Other', 'multiple_programs', '1')
        else:
            conf.write_conf('Other', 'multiple_programs', '0')

    def save_prepare_time(self):
        prepare_time_spin = self.findChild(SpinBox, 'spin_prepare_class')
        conf.write_conf('Toast', 'prepare_minutes', str(prepare_time_spin.value()))

    def clear_log(self):  # 清空日志
        button_clear_log = self.findChild(PushButton, 'button_clear_log')
        try:
            if os.path.exists('log'):
                rmtree('log')
            Flyout.create(
                icon=InfoBarIcon.SUCCESS,
                title='已清除日志',
                content="已清空所有日志文件",
                target=button_clear_log,
                parent=self,
                isClosable=True,
                aniType=FlyoutAnimationType.PULL_UP
            )
        except Exception as e:
            Flyout.create(
                icon=InfoBarIcon.ERROR,
                title='清除日志失败！',
                content=f"清除日志失败：{e}",
                target=button_clear_log,
                parent=self,
                isClosable=True,
                aniType=FlyoutAnimationType.PULL_UP
            )

    def ct_change_color_mode(self):
        color_mode_combo = self.findChild(ComboBox, 'combo_color_mode')
        conf.write_conf('General', 'color_mode', str(color_mode_combo.currentIndex()))
        if color_mode_combo.currentIndex() == 0:
            tg_theme = Theme.LIGHT
        elif color_mode_combo.currentIndex() == 1:
            tg_theme = Theme.DARK
        else:
            tg_theme = Theme.AUTO
        setTheme(tg_theme)
        self.ct_update_preview()

    def ct_add_widget(self):
        widgets_list = self.findChild(ListWidget, 'widgets_list')
        widgets_combo = self.findChild(ComboBox, 'widgets_combo')
        if not widgets_list.findItems(widgets_combo.currentText(), QtCore.Qt.MatchFlag.MatchExactly):
            widgets_list.addItem(widgets_combo.currentText())
        self.ct_update_preview()

    def ct_remove_widget(self):
        widgets_list = self.findChild(ListWidget, 'widgets_list')
        if widgets_list.count() > 2:
            widgets_list.takeItem(widgets_list.currentRow())
            self.ct_update_preview()
        else:
            w = MessageBox('无法删除', '至少需要保留两个小组件。', self)
            w.cancelButton.hide()  # 隐藏取消按钮
            w.buttonLayout.insertStretch(0, 1)
            w.exec()

    def ct_change_theme(self):
        select_theme_combo = self.findChild(ComboBox, 'combo_theme_select')
        alert = MessageBox('您已切换主题',
                           '软件将在您确认后关闭，\n'
                           '您需重新启动以应用您切换的主题。', self)
        alert.cancelButton.hide()  # 隐藏取消按钮，必须重启
        alert.buttonLayout.insertStretch(0, 1)
        if alert.exec():
            conf.write_conf('General', 'theme', list.get_theme_ui_path(select_theme_combo.currentText()))
            sys.exit()

    def ct_set_ac_color(self):
        current_color = QColor(f'#{conf.read_conf("Color", "attend_class")}')
        w = ColorDialog(current_color, "更改上课时主题色", self, enableAlpha=False)
        w.colorChanged.connect(lambda color: conf.write_conf('Color', 'attend_class', color.name()[1:]))
        w.exec()

    def ct_set_fc_color(self):
        current_color = QColor(f'#{conf.read_conf("Color", "finish_class")}')
        w = ColorDialog(current_color, "更改课间时主题色", self, enableAlpha=False)
        w.colorChanged.connect(lambda color: conf.write_conf('Color', 'finish_class', color.name()[1:]))
        w.exec()

    def cf_export_schedule(self):  # 导出课程表
        file_path, _ = QFileDialog.getSaveFileName(self, "保存文件", filename, "Json 配置文件 (*.json)")
        if file_path:
            if list.export_schedule(file_path, filename):
                alert = MessageBox('您已成功导出课程表配置文件',
                                   f'文件将导出于{file_path}', self)
                alert.cancelButton.hide()
                alert.buttonLayout.insertStretch(0, 1)
                if alert.exec():
                    return 0
            else:
                print('导出失败！')
                alert = MessageBox('导出失败！',
                                   '课程表文件导出失败，\n'
                                   '可能为文件损坏，请将此情况反馈给开发者。', self)
                alert.cancelButton.hide()
                alert.buttonLayout.insertStretch(0, 1)
                if alert.exec():
                    return 0

    def ab_check_update(self, version):  # 检查更新
        if version[1:] == conf.read_conf("Other", "version"):
            self.version.setText(f'当前版本：{version}\n当前为最新版本')
        else:
            self.version.setText(f'当前版本：{conf.read_conf("Other", "version")}\n最新版本：{version}')

    def cf_import_schedule(self):  # 导入课程表
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "Json 配置文件 (*.json)")
        if file_path:
            file_name = file_path.split("/")[-1]
            if list.import_schedule(file_path, file_name):
                alert = MessageBox('您已成功导入课程表配置文件',
                                   '软件将在您确认后关闭，\n'
                                   '您需重新启动以应用您切换的配置文件。', self)
                alert.cancelButton.hide()  # 隐藏取消按钮，必须重启
                alert.buttonLayout.insertStretch(0, 1)
                if alert.exec():
                    sys.exit()
            else:
                print('导入失败！')
                alert = MessageBox('导入失败！',
                                   '课程表文件导入失败！\n'
                                   '可能为格式错误或文件损坏，请检查此文件是否为 Class Widgets 课程表文件。\n'
                                   '详情请查看Log日志，日志位于./log/下。', self)
                alert.cancelButton.hide()  # 隐藏取消按钮
                alert.buttonLayout.insertStretch(0, 1)
                if alert.exec():
                    return 0

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
                if isDarkTheme() and conf.load_theme_config(conf.read_conf("General", "theme"))['support_dark_mode']:
                    path = f'ui/{conf.read_conf("General", "theme")}/dark/preview/{widget_name[:-3]}.png'
                else:
                    path = f'ui/{conf.read_conf("General", "theme")}/preview/{widget_name[:-3]}.png'
                label = QLabel()
                label.setPixmap(QPixmap(path))
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
            conf_combo = self.findChild(ComboBox, 'conf_combo')
            conf_combo.clear()
            conf_combo.addItems(list.get_schedule_config())
            conf_combo.setCurrentIndex(list.get_schedule_config().index(f'{new_name}.json'))
        except Exception as e:
            print(f'修改课程文件名称时发生错误：{e}')
            logger.error(f'修改课程文件名称时发生错误：{e}')

    def ad_change_file(self):  # 切换课程文件
        try:
            conf_combo = self.findChild(ComboBox, 'conf_combo')
            conf_name = self.findChild(LineEdit, 'conf_name')
            # 添加新课表
            if conf_combo.currentText() == '添加新课表':
                new_name = f'新课表 - {list.return_default_schedule_number() + 1}'
                list.create_new_profile(f'{new_name}.json')
                conf_combo.clear()
                conf_combo.addItems(list.get_schedule_config())
                conf.write_conf('General', 'schedule', f'{new_name}.json')
                conf_combo.setCurrentIndex(list.get_schedule_config().index(conf.read_conf('General', 'schedule')))
                conf_name.setText(new_name)

            elif conf_combo.currentText().endswith('.json'):
                new_name = conf_combo.currentText()
                conf.write_conf('General', 'schedule', new_name)
                conf_name.setText(new_name[:-5])

            else:
                logger.error(f'切换课程文件时列表选择异常：{conf_combo.currentText()}')
                Flyout.create(
                    icon=InfoBarIcon.ERROR,
                    title='错误！',
                    content=f"列表选项异常！{conf_combo.currentText()}",
                    target=conf_combo,
                    parent=self,
                    isClosable=True,
                    aniType=FlyoutAnimationType.PULL_UP
                )
                return

            global filename
            filename = conf.read_conf('General', 'schedule')
            self.te_load_item()
            self.te_upload_list()
            self.se_load_item()
            self.se_upload_list()
            self.sp_fill_grid_row()
        except Exception as e:
            print(f'切换配置文件时发生错误：{e}')
            logger.error(f'切换配置文件时发生错误：{e}')

    def sp_fill_grid_row(self):  # 填充预览表格
        subtitle = self.findChild(SubtitleLabel, 'subtitle_file')
        subtitle.setText(f'预览  -  {filename[:-5]}')
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
    def te_load_item(self):
        global morning_st, afternoon_st, loaded_data, timeline_dict
        loaded_data = conf.load_from_json(filename)
        part = loaded_data.get('part')
        part_name = loaded_data.get('part_name')
        timeline = get_timeline()
        # 找控件
        te_timeline_list = self.findChild(ListWidget, 'timeline_list')
        te_timeline_list.clear()
        part_list = self.findChild(ListWidget, 'part_list')
        part_list.clear()

        for part_num, part_time in part.items():  # 加载节点
            prefix = part_name[part_num]
            time = QTime(int(part_time[0]), int(part_time[1])).toString('h:mm')
            period = time
            text = f'{prefix} - {period}'
            part_list.addItem(text)

        for week, _ in timeline.items():  # 加载节点
            all_line = []
            for item_name, time in timeline[week].items():  # 加载时间线
                prefix = ''
                item_time = f'{timeline[week][item_name]}分钟'
                # 判断前缀和时段
                if item_name.startswith('a'):
                    prefix = '课程'
                elif item_name.startswith('f'):
                    prefix = '课间'
                period = part_name[item_name[1]]

                # 还原 item_text
                item_text = f"{prefix} - {item_time} - {period}"
                all_line.append(item_text)
            timeline_dict[week] = all_line

    # 加载课表
    def se_load_item(self):
        global schedule_dict
        global schedule_even_dict
        global loaded_data
        loaded_data = conf.load_from_json(filename)
        part_name = loaded_data.get('part_name')
        part = loaded_data.get('part')
        schedule = loaded_data.get('schedule')
        schedule_even = loaded_data.get('schedule_even')
        for week, item in schedule.items():
            all_class = []
            count = []  # 初始化计数器
            for i in range(len(part)):
                count.append(0)
            if str(week) in loaded_data['timeline'] and loaded_data['timeline'][str(week)]:
                timeline = get_timeline()[str(week)]
            else:
                timeline = get_timeline()['default']
            for item_name, item_time in timeline.items():
                if item_name.startswith('a'):
                    try:
                        if int(item_name[1]) == 0:
                            count_num = 0
                        else:
                            count_num = sum(count[:int(item_name[1])])

                        prefix = item[int(item_name[-1]) - 1 + count_num]
                        period = part_name[str(item_name[1])]
                        all_class.append(f'{prefix}-{period}')
                    except Exception as e:
                        prefix = '未添加'
                        period = part_name[str(item_name[1])]
                        all_class.append(f'{prefix}-{period}')
                    count[int(item_name[1])] += 1
            schedule_dict[week] = all_class
        for week, item in schedule_even.items():
            all_class = []
            count = []  # 初始化计数器
            for i in range(len(part)):
                count.append(0)
            if str(week) in loaded_data['timeline'] and loaded_data['timeline'][str(week)]:
                timeline = get_timeline()[str(week)]
            else:
                timeline = get_timeline()['default']
            for item_name, item_time in timeline.items():
                if item_name.startswith('a'):
                    try:
                        if int(item_name[1]) == 0:
                            count_num = 0
                        else:
                            count_num = sum(count[:int(item_name[1])])

                        prefix = item[int(item_name[-1]) - 1 + count_num]
                        period = part_name[str(item_name[1])]
                        all_class.append(f'{prefix}-{period}')
                    except Exception as e:
                        prefix = '未添加'
                        period = part_name[str(item_name[1])]
                        all_class.append(f'{prefix}-{period}')
                    count[int(item_name[1])] += 1
            schedule_even_dict[week] = all_class

    def se_copy_odd_schedule(self):
        logger.info('复制单周课表')
        global schedule_dict, schedule_even_dict
        schedule_even_dict = deepcopy(schedule_dict)
        self.se_upload_list()

    def te_upload_list(self):  # 更新时间线到列表组件
        logger.info('更新列表：时间线编辑')
        te_timeline_list = self.findChild(ListWidget, 'timeline_list')
        te_select_timeline = self.findChild(ComboBox, 'select_timeline')
        try:
            if te_select_timeline.currentIndex() == 0:
                te_timeline_list.clear()
                te_timeline_list.addItems(timeline_dict['default'])
            else:
                te_timeline_list.clear()
                te_timeline_list.addItems(timeline_dict[str(te_select_timeline.currentIndex() - 1)])
            self.te_detect_item()
        except Exception as e:
            print(f'加载时间线时发生错误：{e}')

    # 上传课表到列表组件
    def se_upload_list(self):  # 更新课表到列表组件
        logger.info('更新列表：课程表编辑')
        se_schedule_list = self.findChild(ListWidget, 'schedule_list')
        se_schedule_list.clearSelection()
        se_week_combo = self.findChild(ComboBox, 'week_combo')
        se_week_type_combo = self.findChild(ComboBox, 'week_type_combo')
        se_copy_schedule_button = self.findChild(PushButton, 'copy_schedule')
        global current_week
        try:
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
        except Exception as e:
            print(f'加载课表时发生错误：{e}')

    def se_upload_item(self):  # 保存列表内容到课表文件
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
                print(f'加载双周课表时发生错误：{e}')
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
            data_dict_even = deepcopy(schedule_even_dict)  # 单双周保存
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

    def te_upload_item(self):  # 上传时间线到列表组件
        te_timeline_list = self.findChild(ListWidget, 'timeline_list')
        te_select_timeline = self.findChild(ComboBox, 'select_timeline')
        global timeline_dict
        cache_list = []
        for i in range(te_timeline_list.count()):
            item_text = te_timeline_list.item(i).text()
            cache_list.append(item_text)
        if te_select_timeline.currentIndex() == 0:
            timeline_dict['default'] = cache_list
        else:
            timeline_dict[str(te_select_timeline.currentIndex() - 1)] = cache_list

    # 保存时间线
    def te_save_item(self):
        te_part_list = self.findChild(ListWidget, 'part_list')
        data_dict = {"part": {}, "part_name": {}, "timeline": {'default': {}, **{str(w): {} for w in range(7)}}}
        data_timeline_dict = deepcopy(timeline_dict)
        # 逐条把列表里的信息整理保存
        for i in range(te_part_list.count()):
            item_text = te_part_list.item(i).text()
            item_info = item_text.split(' - ')
            time_tostring = item_info[1].split(':')
            data_dict['part'][str(i)] = [int(time_tostring[0]), int(time_tostring[1])]
            data_dict['part_name'][str(i)] = item_info[0]

        try:
            for week, _ in data_timeline_dict.items():
                counter = []  # 初始化计数器
                for i in range(len(data_dict['part'])):
                    counter.append(0)
                counter_key = 0
                lesson_num = 0
                for i in range(len(data_timeline_dict[week])):
                    item_text = data_timeline_dict[week][i]
                    item_info = item_text.split(' - ')
                    item_name = ''
                    if item_info[0] == '课程':
                        item_name += 'a'
                        lesson_num += 1
                    if item_info[0] == '课间':
                        item_name += 'f'

                    for key, value in data_dict['part_name'].items():  # 节点计数
                        if value == item_info[2]:
                            item_name += str(key)  # +节点序数
                            counter_key = int(key)  # 记录节点序数
                            break

                    if item_name.startswith('a'):
                        counter[counter_key] += 1

                    item_name += str(lesson_num - sum(counter[:counter_key]))  # 课程序数
                    item_time = item_info[1][0:len(item_info[1]) - 2]
                    data_dict['timeline'][str(week)][item_name] = item_time

            conf.save_data_to_json(data_dict, filename)
            self.te_detect_item()
            self.se_load_item()
            self.se_upload_list()
            self.se_upload_item()
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
        except Exception as e:
            logger.error(f'保存时间线时发生错误: {e}')
            Flyout.create(
                icon=InfoBarIcon.ERROR,
                title='保存失败!',
                content=f"{e}\n保存失败，请将 ./log/ 中的日志提交给开发者以反馈问题。",
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
        part_list = self.findChild(ListWidget, 'part_list')
        tips = self.findChild(CaptionLabel, 'tips_2')
        tips_part = self.findChild(CaptionLabel, 'tips_1')
        self.se_load_item()
        if part_list.count() > 0:
            tips_part.hide()
        else:
            tips_part.show()
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
            f'{class_activity.currentText()} - {spin_time.value()}分钟 - {time_period.currentText()}'
        )
        self.te_detect_item()

    def te_add_part(self):
        te_part_list = self.findChild(ListWidget, 'part_list')
        te_name_part = self.findChild(EditableComboBox, 'name_part_combo')
        te_part_time = self.findChild(TimeEdit, 'part_time')
        if te_part_list.count() < 9:
            te_part_list.addItem(
                f'{te_name_part.currentText()} - {te_part_time.time().toString("h:mm")}'
            )
        self.te_detect_item()
        self.te_detect_part()

    def te_delete_part(self):
        te_part_list = self.findChild(ListWidget, 'part_list')
        selected_items = te_part_list.selectedItems()
        for item in selected_items:
            te_part_list.takeItem(te_part_list.row(item))
        self.te_detect_item()
        self.te_detect_part()

    def te_detect_part(self):
        rl = []
        te_time_combo = self.findChild(ComboBox, 'time_period')  # 时段
        te_time_combo.clear()
        part_list = self.findChild(ListWidget, 'part_list')
        for i in range(part_list.count()):
            info = part_list.item(i).text().split(' - ')
            rl.append(info[0])
        te_time_combo.addItems(rl)

    def te_edit_item(self):
        te_timeline_list = self.findChild(ListWidget, 'timeline_list')
        class_activity = self.findChild(ComboBox, 'class_activity')
        spin_time = self.findChild(SpinBox, 'spin_time')
        time_period = self.findChild(ComboBox, 'time_period')
        selected_items = te_timeline_list.selectedItems()

        if selected_items:
            selected_item = selected_items[0]  # 取第一个选中的项目
            selected_item.setText(
                f'{class_activity.currentText()} - {spin_time.value()}分钟 - {time_period.currentText()}'
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
                    se_class_combo.addItem(se_custom_class_text.text())

    def se_quick_set_schedule(self):  # 快速设置课表
        se_schedule_list = self.findChild(ListWidget, 'schedule_list')
        quick_set_schedule = self.findChild(ListWidget, 'subject_list')
        selected_items = se_schedule_list.selectedItems()
        selected_subject = quick_set_schedule.currentItem().text()
        if se_schedule_list.count() > 0:
            if not selected_items:
                se_schedule_list.setCurrentRow(0)

            selected_row = se_schedule_list.currentRow()
            selected_item = se_schedule_list.item(selected_row)
            name_list = selected_item.text().split('-')
            selected_item.setText(
                f'{selected_subject}-{name_list[1]}'
            )

            if se_schedule_list.count() > selected_row + 1:  # 选择下一行
                se_schedule_list.setCurrentRow(selected_row + 1)

    def se_quick_select_week(self):  # 快速选择周
        se_week_combo = self.findChild(ComboBox, 'week_combo')
        if se_week_combo.currentIndex() != 6:
            se_week_combo.setCurrentIndex(se_week_combo.currentIndex() + 1)

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
        te_m_start_time = self.findChild(TimeEdit, 'morningStartTime')
        unformatted_time = te_m_start_time.time()
        h = unformatted_time.hour()
        m = unformatted_time.minute()
        morning_st = (h, m)

    def a_start_time_changed(self):
        global afternoon_st
        te_m_start_time = self.findChild(TimeEdit, 'afternoonStartTime')
        unformatted_time = te_m_start_time.time()
        h = unformatted_time.hour()
        m = unformatted_time.minute()
        afternoon_st = (h, m)

    def init_nav(self):
        self.addSubInterface(self.spInterface, fIcon.HOME, '课表预览')
        self.addSubInterface(self.teInterface, fIcon.DATE_TIME, '时间线编辑')
        self.addSubInterface(self.seInterface, fIcon.EDUCATION, '课程表编辑')
        self.addSubInterface(self.cfInterface, fIcon.FOLDER, '配置文件')
        self.navigationInterface.addSeparator()
        self.addSubInterface(self.hdInterface, fIcon.QUESTION, '帮助')
        self.addSubInterface(self.ctInterface, fIcon.BRUSH, '自定义', NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.sdInterface, fIcon.RINGER, '提醒', NavigationItemPosition.BOTTOM)
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
        screen_geometry = QApplication.primaryScreen().geometry()
        screen_width = screen_geometry.width()

        self.move(int(screen_width / 2 - width / 2), 150)
        self.setWindowTitle('Class Widgets - 设置')
        self.setWindowIcon(QIcon('img/favicon-settings.ico'))

        if conf.read_conf('General', 'color_mode') == '2':
            setTheme(Theme.AUTO)
        elif conf.read_conf('General', 'color_mode') == '1':
            setTheme(Theme.DARK)
        else:
            setTheme(Theme.LIGHT)

        self.init_font()  # 设置字体

    def closeEvent(self, event):
        event.ignore()
        self.hide()


def sp_get_class_num():  # 获取当前周课程数（未完成）
    timeline = get_timeline()['default']
    count = 0
    for item_name, item_time in timeline.items():
        if item_name.startswith('a'):
            count += 1
    return count


if __name__ == '__main__':
    app = QApplication(sys.argv)
    application = desktop_widget()
    application.show()
    application.setMicaEffectEnabled(True)

    sys.exit(app.exec())
