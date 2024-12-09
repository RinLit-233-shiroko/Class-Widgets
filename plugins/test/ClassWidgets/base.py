from PyQt5.QtWidgets import QWidget
import json
import os

class PluginBase:  # 插件类
    def __init__(self, cw_contexts, method):  # 初始化
        # 保存上下文和方法
        self.cw_contexts = cw_contexts
        self.method = method

        self.PATH = self.cw_contexts['PLUGIN_PATH']  # 插件路径

    def execute(self):  # 自启动执行部分
        pass

    def update(self, cw_contexts):  # 自动更新部分
        self.cw_contexts = cw_contexts
        pass


class SettingsBase(QWidget):
    def __init__(self, plugin_path, parent=None):
        super().__init__(parent)
        self.PATH = plugin_path


class PluginConfig:
    def __init__(self, path, filename):
        self.path = path
        self.filename = filename
        self.config = {}
        self.full_path = os.path.join(self.path, self.filename)

    def load_config(self, default_config):
        if default_config is None:
            print('Warning: default_config is None, use empty config instead.')
            default_config = {}
        # 如果文件存在，加载配置
        if os.path.exists(self.full_path):
            with open(self.full_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = default_config  # 如果文件不存在，使用默认配置
            self.save_config()

    def update_config(self):  # 更新配置
        with open(self.full_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    def upload_config(self, key=str or list, value=None):
        if type(key) == str:
            self.config[key] = value
        elif type(key) == list:
            for k in key:
                self.config[k] = value
        else:
            raise TypeError('key must be str or list (键的类型必须是字符串或列表)')
        self.save_config()

    def save_config(self):
        with open(self.full_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

    def __getitem__(self, key):
        return self.config.get(key)

    def __setitem__(self, key, value):
        self.config[key] = value
        self.save_config()

    def __repr__(self):
        return json.dumps(self.config, ensure_ascii=False, indent=4)
