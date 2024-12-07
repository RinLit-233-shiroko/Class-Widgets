from PyQt5 import uic
from PyQt5.QtCore import QSize, Qt, QTimer, QEventLoop, QUrl
from PyQt5.QtGui import QIcon, QPixmap, QFont, QDesktopServices
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QGridLayout, QSpacerItem, QSizePolicy, QWidget
from qfluentwidgets import MSFluentWindow, FluentIcon as fIcon, NavigationItemPosition, TitleLabel, \
    ImageLabel, StrongBodyLabel, HyperlinkLabel, CaptionLabel, PrimaryPushButton, HorizontalFlipView, \
    ElevatedCardWidget, InfoBar, InfoBarPosition, SplashScreen, MessageBoxBase, TransparentToolButton, BodyLabel, \
    PrimarySplitPushButton, RoundMenu, Action
from qframelesswindow.webengine import FramelessWebEngineView

from loguru import logger
from datetime import datetime

import list as l
import sys
import network_thread as nt

# 适配高DPI缩放
QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

MIRROR_PATH = "config/mirror.json"
PLAZA_REPO_URL = "https://raw.githubusercontent.com/Class-Widgets/plugin-plaza/"
PLAZA_REPO_DIR = "https://api.github.com/repos/Class-Widgets/plugin-plaza/contents/Plugins"

plugins_data = []  # 存储插件信息


class PluginDetailPage(MessageBoxBase):  # 插件详情页面
    def __init__(self, icon, title, content, tag, version, author, url, parent=None):
        super().__init__(parent)
        self.url = url
        self.install_url = f"{self.url}/releases/latest"
        author_url = '/'.join(self.url.rsplit('/', 2)[:-1])
        self.init_ui()

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

        self.installButton = self.findChild(PrimarySplitPushButton, 'installButton')
        self.installButton.setText("  安装  ")
        self.installButton.setIcon(fIcon.DOWNLOAD)
        self.installButton.clicked.connect(self.install)
        menu = RoundMenu(parent=self.installButton)
        menu.addActions([
            Action(fIcon.DOWNLOAD, "为 Class Widgets 安装", triggered=self.install),
            Action(fIcon.LINK, "下载到本地", triggered=lambda: QDesktopServices.openUrl(QUrl(self.install_url)))
        ])
        self.installButton.setFlyout(menu)

    def install(self):
        InfoBar.warning(
            title='安装失败……',
            content="Coming s∞n~",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=1500,
            parent=self.parent()
        )

    def init_ui(self):
        # 加载ui文件
        temp_widget = QWidget()
        uic.loadUi('pp-plugin_detail.ui', temp_widget)
        self.viewLayout.addWidget(temp_widget)
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


class PluginCard_Horizontal(ElevatedCardWidget):  # 插件卡片（横向）
    def __init__(
            self, icon='img/settings/plugin-icon.png', title='Plugin Name', content='Description...', tag='Unknown',
            version='1.0.0', author="CW Support",
            url="https://github.com/RinLit-233-shiroko/cw-example-plugin", parent=None):
        super().__init__(parent)
        self.icon = icon
        self.title = title
        self.parent = parent
        self.tag = tag
        self.url = url
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
        InfoBar.warning(
            title='安装失败……',
            content="Coming s∞n~",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=1500,
            parent=self.parent
        )

    def show_detail(self):
        w = PluginDetailPage(
            icon=self.icon, title=self.title, content=self.contentLabel.text(),
            tag=self.tag, version=self.versionLabel.text(), author=self.authorLabel.text(),
            url=self.url, parent=self.parent
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
                                                author=data['author'], parent=self)
            plugin_card.clicked.connect(plugin_card.show_detail)  # 点击事件
            self.rec_plugin_grid.addWidget(plugin_card, plugin_num // 2, plugin_num % 2)  # 排列

            plugin_num += 1
            if plugin_num == total_plugins:
                event_loop.quit()

        for plugin, data in p_data.items():  # 遍历插件data
            img_thread = nt.getImg(f'{data["url"].replace("https://github.com/", "https://raw.githubusercontent.com/")}'
                                   f'/{data["branch"]}/icon.png')
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

    def get_pp_data(self):
        global plugins_data
        self.get_plugin_list_thread = nt.getPluginInfo()
        self.get_plugin_list_thread.repo_signal.connect(self.load_recommend_plugin)
        self.get_plugin_list_thread.start()

    def switch_banners(self):  # 切换Banner
        if self.banner_view.currentIndex() == len(self.banners) - 1:
            self.banner_view.scrollToIndex(0)
        else:
            self.banner_view.scrollNext()

    def init_nav(self):
        self.addSubInterface(self.homeInterface, fIcon.HOME, '首页', fIcon.HOME_FILL)
        self.addSubInterface(self.latestsInterface, fIcon.MEGAPHONE, '最新上架')
        self.addSubInterface(
            self.settingsInterface, fIcon.SETTING, '设置', position=NavigationItemPosition.BOTTOM
        )

    def init_window(self):
        self.load_all_interface()
        self.init_font()

        self.setMinimumWidth(700)
        self.setMinimumHeight(400)
        self.setMicaEffectEnabled(True)
        self.setWindowTitle('插件广场')
        self.setWindowIcon(QIcon('img/pp_favicon.png'))
        self.setMicaEffectEnabled(True)

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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    pp = PluginPlaza()
    pp.show()
    sys.exit(app.exec())
