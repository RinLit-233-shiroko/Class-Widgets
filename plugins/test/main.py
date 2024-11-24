'''
    这是一个示例插件
'''
from loguru import logger
from datetime import datetime

# 自定义小组件
WIDGET_CODE = 'widget_test.ui'
WIDGET_NAME = '测试组件'
WIDGET_WIDTH = 225

class Plugin:  # 插件类
    def __init__(self, cw_contexts, method):  # 初始化
        # 保存上下文和方法
        self.cw_contexts = cw_contexts
        self.method = method
        
        self.CONFIG_PATH = f'{cw_contexts["PLUGIN_PATH"]}/config.json'  # 配置文件路径

        self.method.register_widget(WIDGET_CODE, WIDGET_NAME, WIDGET_WIDTH)

    def execute(self):  # 自启动执行部分
        if self.cw_contexts['State']:  # 判断当前状态
            self.method.change_widget_content(WIDGET_CODE, '测试', '上课状态')
        else:
            self.method.change_widget_content(WIDGET_CODE, '测试', '课间/休息状态')
            
        logger.success('Plugin1 executed!')
        logger.info(f'Config path: {self.CONFIG_PATH}')

    def update(self, cw_contexts):  # 自动更新部分
        self.cw_contexts = cw_contexts
        widget_title = f'天气:{self.cw_contexts["Weather"]}，当前秒:{datetime.now().second}'  # 标题内容

        if self.cw_contexts['State']:  # 判断当前状态
            self.method.change_widget_content(WIDGET_CODE, widget_title, '上课状态')
        else:
            self.method.change_widget_content(WIDGET_CODE, widget_title, '课间/休息状态')

        if self.method.is_get_notification():
            logger.warning('warning', f'Plugin1 got notification! Title: {self.cw_contexts["Notification"]["title"]}')

            if self.cw_contexts['Notification']['state'] == 0:  # 如果下课
                self.method.subprocess_exec('打开记事本', 'notepad')  # 调用CW方法构建自动化
