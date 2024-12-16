import json

import requests
from PyQt5.QtCore import QThread, pyqtSignal
from loguru import logger

import conf

headers = {"User-Agent": "Mozilla/5.0"}

MIRROR_PATH = "config/mirror.json"
PLAZA_REPO_URL = "https://raw.githubusercontent.com/Class-Widgets/plugin-plaza/"
PLAZA_REPO_DIR = "https://api.github.com/repos/Class-Widgets/plugin-plaza/contents/"

# 读取镜像配置
mirror_list = []
try:
    with open(MIRROR_PATH, 'r', encoding='utf-8') as file:
        mirror_dict = json.load(file).get('gh_mirror')
except Exception as e:
    logger.error(f"读取镜像配置失败: {e}")

for name in mirror_dict:
    mirror_list.append(name)


class getRepoFileList(QThread):  # 获取仓库文件目录
    repo_signal = pyqtSignal(list)

    def __init__(self, path='Plugins', endswith='.json'):  # 目录
        super().__init__()
        self.path = path
        self.endswith = endswith

    def run(self):
        try:
            file_list = self.get_list()
            self.repo_signal.emit(file_list)
        except Exception as e:
            logger.error(f"触发所有插件信息失败: {e}")

    def get_list(self):
        try:
            # 获取目录内容
            url = f"{PLAZA_REPO_DIR}{self.path}"
            print(url)
            response = requests.get(url, proxies={'http': None, 'https': None}, headers=headers)
            if response.status_code == 200:
                response.raise_for_status()
                files = response.json()

                # 筛选出 JSON 文件
                json_files = [file['download_url'] for file in files if file['name'].endswith(self.endswith)]

                if not json_files:
                    logger.warning(f"插件广场内{self.path}的目录为空")
                    return []
                else:
                    logger.success(f"获取{self.path}目录成功")
                    return json_files
            elif response.status_code == 403 or response.status_code == 429:
                logger.warning("到达Github API限制，请稍后再试")
                return []
            else:
                logger.error(f"获取{self.path}目录失败：{response.status_code}")
                return []
        except Exception as e:
            logger.error(f"获取{self.path}目录错误: {e}")
            return []


class getPluginInfo(QThread):  # 获取插件信息(json)
    repo_signal = pyqtSignal(dict)

    def __init__(
            self, url='https://raw.githubusercontent.com/Class-Widgets/plugin-plaza/main/Plugins/plugin_list.json'
    ):
        super().__init__()
        self.download_url = url

    def run(self):
        try:
            plugin_info_data = self.get_plugin_info()
            self.repo_signal.emit(plugin_info_data)
        except Exception as e:
            logger.error(f"触发插件信息失败: {e}")

    def get_plugin_info(self):
        try:
            mirror_url = mirror_dict[conf.read_conf('Plugin', 'mirror')]
            url = f"{mirror_url}{self.download_url}"
            response = requests.get(url, proxies={'http': None, 'https': None})  # 禁用代理
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                logger.error(f"获取插件信息失败：{response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"获取插件信息失败：{e}")
            return {}


class getImg(QThread):  # 获取图片
    repo_signal = pyqtSignal(bytes)

    def __init__(self, url='https://raw.githubusercontent.com/Class-Widgets/plugin-plaza/main/Banner/banner_1.png'):
        super().__init__()
        self.download_url = url

    def run(self):
        try:
            banner_data = self.get_banner()
            if banner_data is not None:
                self.repo_signal.emit(banner_data)
            else:
                with open("img/plaza/banner_pre.png", 'rb') as default_img:  # 读取默认图片
                    self.repo_signal.emit(default_img.read())
        except Exception as e:
            logger.error(f"触发图片失败: {e}")

    def get_banner(self):
        try:
            mirror_url = mirror_dict[conf.read_conf('Plugin', 'mirror')]
            url = f"{mirror_url}{self.download_url}"
            response = requests.get(url, proxies={'http': None, 'https': None})
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"获取图片失败：{response.status_code}")
                return None
        except Exception as e:
            logger.error(f"获取图片失败：{e}")
            return None


class getReadme(QThread):  # 获取README
    html_signal = pyqtSignal(str)

    def __init__(self, url='https://raw.githubusercontent.com/Class-Widgets/Class-Widgets/main/README.md'):
        super().__init__()
        self.download_url = url

    def run(self):
        try:
            readme_data = self.get_readme()
            self.html_signal.emit(readme_data)
        except Exception as e:
            logger.error(f"触发README失败: {e}")

    def get_readme(self):
        try:
            mirror_url = mirror_dict[conf.read_conf('Plugin', 'mirror')]
            url = f"{mirror_url}{self.download_url}"
            print(url)
            response = requests.get(url, proxies={'http': None, 'https': None})
            if response.status_code == 200:
                return response.text
            else:
                logger.error(f"获取README失败：{response.status_code}")
                return ''
        except Exception as e:
            logger.error(f"获取README失败：{e}")
            return ''
