"""
    这是一个示例插件
"""
from PyQt5 import uic
from loguru import logger
from datetime import datetime
from .ClassWidgets.base import PluginBase, SettingsBase, PluginConfig  # 导入CW的基类

from PyQt5.QtWidgets import QHBoxLayout
from qfluentwidgets import ImageLabel, LineEdit

# 自定义小组件
WIDGET_CODE = 'widget_test.ui'
WIDGET_NAME = '测试组件'
WIDGET_WIDTH = 245


class Plugin(PluginBase):  # 插件类
    def __init__(self, cw_contexts, method):  # 初始化
        super().__init__(cw_contexts, method)  # 调用父类初始化方法

        self.method.register_widget(WIDGET_CODE, WIDGET_NAME, WIDGET_WIDTH)  # 注册小组件到CW
        self.cfg = PluginConfig(self.PATH, 'config.json')  # 实例化配置类

    def execute(self):  # 自启动执行部分
        # 小组件自定义（照PyQt的方法正常写）
        self.test_widget = self.method.get_widget(WIDGET_CODE)  # 获取小组件对象

        if self.test_widget:  # 判断小组件是否存在
            contentLayout = self.test_widget.findChild(QHBoxLayout, 'contentLayout')  # 标题布局
            contentLayout.setSpacing(1)  # 设置间距

            self.testimg = ImageLabel(f'{self.PATH}/img/favicon.png')  # 自定义图片
            self.testimg.setFixedSize(36, 30)

            contentLayout.addWidget(self.testimg)  # 添加图片到布局

        # Others
        if self.cw_contexts['State']:  # 判断当前状态
            self.method.change_widget_content(WIDGET_CODE, '测试', '上课状态')
        else:
            self.method.change_widget_content(WIDGET_CODE, '测试', '课间状态')

        logger.success('Plugin1 executed!')
        logger.info(f'Config path: {self.PATH}')

    def update(self, cw_contexts):  # 自动更新部分
        super().update(cw_contexts)  # 调用父类更新方法
        self.cfg.update_config()  # 更新配置

        if hasattr(self, 'test_widget'):  # 判断小组件是否存在
            widget_title = f'天气:{self.cw_contexts["Weather"]}，当前秒:{datetime.now().second}'  # 标题内容

            if self.cw_contexts['State']:  # 判断当前状态
                self.method.change_widget_content(WIDGET_CODE, widget_title, '上课状态')
            else:
                self.method.change_widget_content(WIDGET_CODE, widget_title, '课间状态')

        if self.method.is_get_notification():
            logger.warning('warning', f'Plugin1 got notification! Title: {self.cw_contexts["Notification"]["title"]}')

            if self.cw_contexts['Notification']['state'] == 0:  # 如果下课
                self.method.subprocess_exec(self.cfg['name'], self.cfg['action'])  # 调用CW方法构建自动化


# 设置页
class Settings(SettingsBase):
    def __init__(self, plugin_path, parent=None):
        super().__init__(plugin_path, parent)
        uic.loadUi(f'{self.PATH}/settings.ui', self)  # 加载设置界面

        default_config = {
            "name": "打开记事本",
            "action": "notepad"
        }

        self.cfg = PluginConfig(self.PATH, 'config.json')  # 实例化配置类
        self.cfg.load_config(default_config)  # 加载配置

        # 名称和动作输入框
        self.nameEdit = self.findChild(LineEdit, 'nameEdit')
        self.nameEdit.setText(self.cfg['name'])
        self.actionEdit = self.findChild(LineEdit, 'actionEdit')
        self.actionEdit.setText(self.cfg['action'])

        self.nameEdit.textChanged.connect(lambda: self.cfg.upload_config('name', self.nameEdit.text()))
        self.actionEdit.textChanged.connect(lambda: self.cfg.upload_config('action', self.actionEdit.text()))
