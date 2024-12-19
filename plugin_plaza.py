import json

from PyQt5 import uic
from PyQt5.QtCore import QSize, Qt, QTimer, QEventLoop, QUrl
from PyQt5.QtGui import QIcon, QPixmap, QDesktopServices
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QGridLayout, QSpacerItem, QSizePolicy, QWidget
from qfluentwidgets import MSFluentWindow, FluentIcon as fIcon, NavigationItemPosition, TitleLabel, \
    ImageLabel, StrongBodyLabel, HyperlinkLabel, CaptionLabel, PrimaryPushButton, HorizontalFlipView, \
    InfoBar, InfoBarPosition, SplashScreen, MessageBoxBase, TransparentToolButton, BodyLabel, \
    PrimarySplitPushButton, RoundMenu, Action, PipsPager, TextBrowser, CardWidget, \
    IndeterminateProgressRing, ComboBox, IndeterminateProgressBar, ProgressBar

from loguru import logger
from datetime import datetime

import conf
import list as l
import sys
import network_thread as nt

# 适配高DPI缩放
QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

CONF_PATH = "plugins/plugins_from_pp.json"
PLAZA_REPO_URL = "https://raw.githubusercontent.com/Class-Widgets/plugin-plaza/"
PLAZA_REPO_DIR = "https://api.github.com/repos/Class-Widgets/plugin-plaza/contents/Plugins"
TEST_DOWNLOAD_LINK = "https://dldir1.qq.com/qqfile/qq/PCQQ9.7.17/QQ9.7.17.29225.exe"

restart_tips_flag = False  # 重启提示
plugins_data = []  # 仓库插件信息
download_progress = []  # 下载线程

installed_plugins = []  # 已安装插件（通过PluginPlaza获取）
try:
    with open(CONF_PATH, 'r', encoding='utf-8') as file:
        installed_plugins = json.load(file).get('plugins')
except Exception as e:
    logger.error(f"读取已安装的插件失败: {e}")


class downloadProgressBar(InfoBar):  # 下载进度条(创建下载进程)
    def __init__(self, url=TEST_DOWNLOAD_LINK, name="Test", parent=None):
        global download_progress
        self.p_name = url.split('/')[4]  # repo
        user = url.split('/')[3]
        self.name = name

        super().__init__(icon=fIcon.DOWNLOAD,
                         title='',
                         content=f"正在下载 {name} (～￣▽￣)～)",
                         orient=Qt.Horizontal,
                         isClosable=False,
                         position=InfoBarPosition.TOP,
                         duration=-1,
                         parent=parent
                         )
        # self.setCustomBackgroundColor('white', '#202020')
        # self.bar = IndeterminateProgressBar()
        self.bar = ProgressBar()
        self.bar.setFixedWidth(300)
        self.cancelBtn = HyperlinkLabel()
        self.cancelBtn.setText("取消")
        self.cancelBtn.clicked.connect(self.cancelDownload)
        self.addWidget(self.bar)
        self.addWidget(self.cancelBtn)

        # 开始下载

        download_progress.append(self.p_name)
        self.get_url_thread = nt.getDownloadUrl(user, self.p_name)
        self.get_url_thread.geturl_signal.connect(self.set_url)  # 获取下载链接
        self.get_url_thread.start()

    def set_url(self, url):  # 接受下载连接并开始任务
        if not url.startswith('ERROR'):
            self.download_thread = nt.DownloadAndExtract(url, self.p_name)
            # self.download_thread = nt.DownloadAndExtract(TEST_DOWNLOAD_LINK, self.p_name)
            self.download_thread.progress_signal.connect(lambda progress: self.bar.setValue(int(progress)))  # 下载
            self.download_thread.status_signal.connect(self.detect_status)  # 判断状态
            self.download_thread.start()
        else:
            self.download_error(url[6:])

    def cancelDownload(self):
        global download_progress
        download_progress.remove(self.p_name)
        self.download_thread.stop()
        self.download_thread.deleteLater()
        self.close()

    def detect_status(self, status):
        if status == "DOWNLOADING":
            self.content = f"正在下载 {self.name} (～￣▽￣)～)"
        elif status == "EXTRACTING":
            self.content = f"正在解压 {self.name} ( •̀ ω •́ )✧)"
        elif status == "DONE":
            self.download_finished()
        elif status.startswith("ERROR"):
            self.download_error(status[6:])
        else:
            pass

    def download_finished(self):
        global download_progress
        download_progress.remove(self.p_name)
        add2save_plugin(self.p_name)  # 保存到配置
        self.download_thread.finished.emit()
        self.download_thread.deleteLater()
        InfoBar.success(
            title='下载成功！',
            content=f"下载 {self.name} 成功！",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self.parent()
        )
        if not restart_tips_flag:  # 重启提示
            self.parent().restart_tips()
        self.close()

    def download_error(self, error_info):
        global download_progress
        download_progress.remove(self.p_name)
        InfoBar.error(
            title='下载失败(っ °Д °;)っ',
            content=f"{error_info}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self.parent()
        )
        self.close()


class PluginDetailPage(MessageBoxBase):  # 插件详情页面
    def __init__(self, icon, title, content, tag, version, author, url, data=None, parent=None):
        super().__init__(parent)
        self.url = url
        self.data = data
        self.title = title
        self.parent = parent
        self.p_name = url.split('/')[-1]  # repo
        author_url = '/'.join(self.url.rsplit('/', 2)[:-1])
        self.init_ui()
        self.download_readme()
        scroll_area_widget = self.findChild(QVBoxLayout, 'verticalLayout_9')

        self.iconWidget = self.findChild(ImageLabel, 'pluginIcon')
        self.iconWidget.setImage(icon)
        self.iconWidget.setFixedSize(100, 100)
        self.iconWidget.setBorderRadius(8, 8, 8, 8)

        self.titleLabel = self.findChild(TitleLabel, 'titleLabel')
        self.titleLabel.setText(title)

        self.contentLabel = self.findChild(CaptionLabel, 'descLabel')
        self.contentLabel.setText(content)

        self.tagLabel = self.findChild(HyperlinkLabel, 'tagButton')
        self.tagLabel.setText(tag)

        self.versionLabel = self.findChild(BodyLabel, 'versionLabel')
        self.versionLabel.setText(version)

        self.authorLabel = self.findChild(HyperlinkLabel, 'authorButton')
        self.authorLabel.setText(author)
        self.authorLabel.setUrl(author_url)

        self.openGitHub = self.findChild(TransparentToolButton, 'openGitHub')
        self.openGitHub.setIcon(fIcon.GITHUB)
        self.openGitHub.setIconSize(QSize(24, 24))
        self.openGitHub.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.url)))

        self.installButton = self.findChild(PrimarySplitPushButton, 'installButton')
        self.installButton.setText("  安装  ")
        self.installButton.setIcon(fIcon.DOWNLOAD)
        self.installButton.clicked.connect(self.install)

        if self.p_name in download_progress:  # 如果正在下载
            self.installButton.setText("  安装中  ")
            self.installButton.setEnabled(False)
        if self.p_name in installed_plugins:  # 如果已安装
            self.installButton.setText("  已安装  ")
            self.installButton.setEnabled(False)

        menu = RoundMenu(parent=self.installButton)
        menu.addActions([
            Action(fIcon.DOWNLOAD, "为 Class Widgets 安装", triggered=self.install),
            Action(fIcon.LINK, "下载到本地",
                   triggered=lambda: QDesktopServices.openUrl(QUrl(f"{self.url}/releases/latest")))
        ])
        self.installButton.setFlyout(menu)

        self.readmePage = TextBrowser()
        self.readmePage.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.readmePage.setReadOnly(True)
        scroll_area_widget.addWidget(self.readmePage)

    def install(self):
        self.installButton.setText("  安装中  ")
        self.installButton.setEnabled(False)
        di = downloadProgressBar(
            url=f"{replace_to_file_server(self.url, self.data['branch'])}/releases/latest/download",
            name=self.title,
            parent=self.parent
        )
        di.show()

    def download_readme(self):
        def display_readme(markdown_text):
            self.readmePage.setMarkdown(markdown_text)

        if self.data is None:
            self.download_thread = nt.getReadme(f"{replace_to_file_server(self.url)}/README.md")
        else:
            self.download_thread = nt.getReadme(f"{replace_to_file_server(self.url, self.data['branch'])}/README.md")
        self.download_thread.html_signal.connect(display_readme)
        self.download_thread.start()

    def init_ui(self):
        # 加载ui文件
        self.temp_widget = QWidget()
        uic.loadUi('pp-plugin_detail.ui', self.temp_widget)
        self.viewLayout.addWidget(self.temp_widget)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        # 隐藏原有按钮
        self.yesButton.hide()
        self.cancelButton.hide()
        self.buttonGroup.hide()

        # 自定关闭按钮
        self.closeButton = self.findChild(TransparentToolButton, 'closeButton')
        self.closeButton.setIcon(fIcon.CLOSE)
        self.closeButton.clicked.connect(self.close)

        self.widget.setMinimumWidth(875)
        self.widget.setMinimumHeight(625)


class PluginCard_Horizontal(CardWidget):  # 插件卡片（横向）
    def __init__(
            self, icon='img/settings/plugin-icon.png', title='Plugin Name', content='Description...', tag='Unknown',
            version='1.0.0', author="CW Support",
            url="https://github.com/RinLit-233-shiroko/cw-example-plugin", data=None, parent=None):
        super().__init__(parent)
        self.icon = icon
        self.title = title
        self.parent = parent
        self.tag = tag
        self.url = url
        self.p_name = url.split('/')[-1]  # repo
        self.data = data
        author_url = '/'.join(self.url.rsplit('/', 2)[:-1])

        self.iconWidget = ImageLabel(icon)  # 插件图标
        self.titleLabel = StrongBodyLabel(title, self)  # 插件名
        self.versionLabel = CaptionLabel(version, self)  # 插件版本
        self.authorLabel = HyperlinkLabel()  # 插件作者
        self.contentLabel = CaptionLabel(content, self)  # 插件描述
        self.installButton = PrimaryPushButton()

        # layout
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout_Title = QHBoxLayout()
        self.hBoxLayout_Author = QHBoxLayout()
        self.vBoxLayout = QVBoxLayout(self)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(110)
        self.authorLabel.setText(author)
        self.authorLabel.setUrl(author_url)
        self.authorLabel.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.iconWidget.setFixedSize(84, 84)
        self.iconWidget.setBorderRadius(5, 5, 5, 5)  # 圆角
        self.contentLabel.setTextColor("#606060", "#d2d2d2")
        self.versionLabel.setTextColor("#999999", "#999999")
        self.titleLabel.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

        self.installButton.setText("安装")
        self.installButton.setFixedSize(115, 36)
        self.installButton.setIcon(fIcon.DOWNLOAD)
        self.installButton.clicked.connect(self.install)
        if self.p_name in installed_plugins:  # 如果已安装
            self.installButton.setText("已安装")
            self.installButton.setEnabled(False)

        self.hBoxLayout.setContentsMargins(20, 11, 11, 11)
        self.hBoxLayout.setSpacing(15)
        self.hBoxLayout.addWidget(self.iconWidget)

        self.blank = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vBoxLayout.setContentsMargins(0, 5, 0, 5)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.addLayout(self.hBoxLayout_Title)
        self.vBoxLayout.addLayout(self.hBoxLayout_Author)
        self.vBoxLayout.addItem(self.blank)
        self.vBoxLayout.addWidget(self.contentLabel, 0, Qt.AlignmentFlag.AlignTop)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.hBoxLayout.addWidget(self.installButton)

        self.hBoxLayout_Title.setSpacing(12)
        self.hBoxLayout_Title.addWidget(self.titleLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        self.hBoxLayout_Title.addWidget(self.versionLabel, 0, Qt.AlignmentFlag.AlignVCenter)

        self.hBoxLayout_Author.addWidget(self.authorLabel, 0, Qt.AlignmentFlag.AlignLeft)

    def install(self):
        if self.p_name not in download_progress:  # 如果正在下载
            di = downloadProgressBar(
                url=f"{replace_to_file_server(self.url, self.data['branch'])}/releases/latest/download",
                name=self.title,
                parent=self.parent
            )
            di.show()

    def show_detail(self):
        w = PluginDetailPage(
            icon=self.icon, title=self.title, content=self.contentLabel.text(),
            tag=self.tag, version=self.versionLabel.text(), author=self.authorLabel.text(),
            url=self.url, data=self.data, parent=self.parent
        )
        w.exec()


class PluginPlaza(MSFluentWindow):
    def __init__(self):
        super().__init__()
        try:
            self.homeInterface = uic.loadUi('pp-home.ui')  # 首页
            self.homeInterface.setObjectName("homeInterface")
            self.latestsInterface = uic.loadUi('pp-latests.ui')  # 最新更新
            self.latestsInterface.setObjectName("latestInterface")
            self.settingsInterface = uic.loadUi('pp-settings.ui')  # 设置
            self.settingsInterface.setObjectName("settingsInterface")

            self.init_nav()
            self.init_window()
            self.get_pp_data()
            self.get_banner_img()
        except Exception as e:
            logger.error(f'初始化插件广场时发生错误：{e}')

    def load_all_interface(self):
        self.setup_homeInterface()
        self.setup_settingsInterface()

    def setup_settingsInterface(self):  # 初始化设置
        # 选择代理
        select_mirror = self.settingsInterface.findChild(ComboBox, 'select_proxy')
        select_mirror.addItems(nt.mirror_list)
        select_mirror.setCurrentIndex(nt.mirror_list.index(conf.read_conf('Plugin', 'mirror')))
        select_mirror.currentIndexChanged.connect(
            lambda: conf.write_conf('Plugin', 'mirror', select_mirror.currentText()))

    def setup_homeInterface(self):  # 初始化首页
        # 标题和副标题
        time_today_label = self.homeInterface.findChild(TitleLabel, 'time_today_label')
        time_today_label.setText(f"{datetime.now().month}月{datetime.now().day}日 {l.week[datetime.now().weekday()]}")

        # Banner
        self.banner_view = self.homeInterface.findChild(HorizontalFlipView, 'banner_view')
        self.banner_view.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.banner_view.setItemSize(QSize(900, 450))  # 设置图片大小（banner图片尺寸比）
        self.banner_view.setBorderRadius(8)
        self.banner_view.setSpacing(5)
        self.banner_view.clicked.connect(lambda: print("tt"))

        self.auto_play_timer = QTimer(self)  # 自动轮播
        self.auto_play_timer.timeout.connect(lambda: self.switch_banners())
        self.auto_play_timer.setInterval(2500)

        # 翻页
        self.banner_pager = self.homeInterface.findChild(PipsPager, 'banner_pager')
        self.banner_pager.setVisibleNumber(5)
        self.banner_pager.currentIndexChanged.connect(
            lambda: (self.banner_view.scrollToIndex(self.banner_pager.currentIndex()),
                     self.auto_play_timer.stop(),
                     self.auto_play_timer.start(2500))
        )

    def load_recommend_plugin(self, p_data):
        self.rec_plugin_grid = self.homeInterface.findChild(QGridLayout, 'rec_plugin_grid')  # 插件表格
        plugin_num = 0  # 计数
        total_plugins = len(p_data)  # 总数
        event_loop = QEventLoop()  # 事件循环

        def load_plugin_card(img):  # 加载插件卡片
            nonlocal plugin_num
            pixmap = QPixmap()
            pixmap.loadFromData(img)
            plugin_card = PluginCard_Horizontal(icon=pixmap, title=data['name'], content=data['description'],
                                                tag=data['tag'], version=data['version'], url=data['url'],
                                                author=data['author'], data=data, parent=self)
            plugin_card.clicked.connect(plugin_card.show_detail)  # 点击事件
            self.rec_plugin_grid.addWidget(plugin_card, plugin_num // 2, plugin_num % 2)  # 排列

            plugin_num += 1
            if plugin_num == total_plugins:
                load_plugin_progress = self.homeInterface.findChild(IndeterminateProgressRing, 'load_plugin_progress')
                load_plugin_progress.hide()
                event_loop.quit()

        for plugin, data in p_data.items():  # 遍历插件data
            img_thread = nt.getImg(f"{replace_to_file_server(data['url'], branch=data['branch'])}/icon.png")
            img_thread.repo_signal.connect(load_plugin_card)
            img_thread.start()

        event_loop.exec_()

    def get_banner_img(self):
        def display_banner(data, index=0):
            if index == 0:
                self.auto_play_timer.start()
            if data:
                pixmap = QPixmap()
                pixmap.loadFromData(data)
                self.banner_view.setItemImage(index, pixmap)
            self.splashScreen.hide()

        def get_banner(data):
            try:
                self.banner_pager.setPageNumber(len(data))
                self.banners = ["img/plaza/banner_pre.png" for _ in range(len(data))]
                if data:
                    self.banner_view.addImages(self.banners)

                # 定义一个内部函数来启动下一个线程
                def start_next_banner(index):
                    if index < len(data):
                        self.banner_thread = nt.getImg(data[index])
                        self.banner_thread.repo_signal.connect(lambda data: display_banner(data, index))
                        self.banner_thread.repo_signal.connect(lambda: start_next_banner(index + 1))  # 连接完成信号
                        self.banner_thread.start()

                start_next_banner(0)  # 启动第一个线程

            except Exception as e:
                logger.error(f"获取Banner失败：{e}")

        self.banner_list_thread = nt.getRepoFileList(path="Banner", endswith=".png")
        self.banner_list_thread.repo_signal.connect(get_banner)
        self.banner_list_thread.start()

    def restart_tips(self):
        global restart_tips_flag
        restart_tips_flag = True
        w = InfoBar.info(
                title='需要重启',
                content='若要应用插件配置，需重启 Class Widgets',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=-1,
                parent=self
            )
        restart_btn = HyperlinkLabel('关闭软件')
        restart_btn.clicked.connect(lambda: sys.exit())
        w.addWidget(restart_btn)
        w.show()

    def get_pp_data(self):
        global plugins_data
        self.get_plugin_list_thread = nt.getPluginInfo()
        self.get_plugin_list_thread.repo_signal.connect(self.load_recommend_plugin)
        self.get_plugin_list_thread.start()

    def switch_banners(self):  # 切换Banner
        if self.banner_view.currentIndex() == len(self.banners) - 1:
            self.banner_view.scrollToIndex(0)
            self.banner_pager.setCurrentIndex(0)
        else:
            self.banner_view.scrollNext()
            self.banner_pager.setCurrentIndex(self.banner_view.currentIndex())

    def init_nav(self):
        self.addSubInterface(self.homeInterface, fIcon.HOME, '首页', fIcon.HOME_FILL)
        self.addSubInterface(self.latestsInterface, fIcon.MEGAPHONE, '最新上架')
        self.addSubInterface(
            self.settingsInterface, fIcon.SETTING, '设置', position=NavigationItemPosition.BOTTOM
        )

    def init_window(self):
        self.load_all_interface()
        self.init_font()

        self.setMinimumWidth(950)
        self.setMinimumHeight(400)
        self.setMicaEffectEnabled(True)
        self.setWindowTitle('插件广场')
        self.setWindowIcon(QIcon('img/pp_favicon.png'))

        screen_geometry = QApplication.primaryScreen().geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        width = int(screen_width * 0.6)
        height = int(screen_height * 0.7)

        self.move(int(screen_width / 2 - width / 2), 150)
        self.resize(width, height)

        # 启动屏幕
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(102, 102))
        self.show()

    def init_font(self):  # 设置字体
        self.setStyleSheet("""QLabel {
                    font-family: 'Microsoft YaHei';
                }""")

    def closeEvent(self, event):
        event.ignore()
        # self.deleteLater()
        self.hide()


def add2save_plugin(p_name):  # 保存已安装插件
    global installed_plugins
    installed_plugins.append(p_name)
    try:
        with open(CONF_PATH, 'w', encoding='utf-8') as f:
            json.dump({"plugins": installed_plugins}, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"保存已安装插件失败：{e}")


def replace_to_file_server(url, branch='main'):
    return (f'{url.replace("https://github.com/", "https://raw.githubusercontent.com/")}'
            f'/{branch}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    pp = PluginPlaza()
    pp.show()
    sys.exit(app.exec())
