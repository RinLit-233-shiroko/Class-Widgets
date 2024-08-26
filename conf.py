import json
import os
import configparser as config
from win32com.client import Dispatch
path = 'config.ini'
conf = config.ConfigParser()
name = 'Class Widgets'

# CONFIG
# 读取config
def read_conf(section='General', key=''):
    data = config.ConfigParser()
    try:
        with open(path, 'r', encoding='utf-8') as configfile:
            data.read_file(configfile)
    except FileNotFoundError:
        return None
    except Exception:
        return None

    if section in data and key in data[section]:
        return data[section][key]
    else:
        return None


# 写入config
def write_conf(section, key, value):
    data = config.ConfigParser()
    try:
        with open(path, 'r', encoding='utf-8') as configfile:
            data.read_file(configfile)
    except FileNotFoundError:
        pass
    except Exception:
        print(Exception)

    if section not in data:
        data.add_section(section)

    data.set(section, key, value)

    with open(path, 'w', encoding='utf-8') as configfile:
        data.write(configfile)


# JSON
def save_data_to_json(new_data, filename):
    # 初始化 data_dict 为一个空字典
    data_dict = {}

    # 如果文件存在，先读取文件中的现有数据
    if os.path.exists(f'config/schedule/{filename}'):
        try:
            with open(f'config/schedule/{filename}', 'r', encoding='utf-8') as file:
                data_dict = json.load(file)
        except Exception as e:
            print(f"读取现有数据时出错: {e}")

    # 更新 data_dict，添加或覆盖新的数据
    data_dict.update(new_data)

    # 将更新后的数据保存回文件
    try:
        with open(f'config/schedule/{filename}', 'w', encoding='utf-8') as file:
            json.dump(data_dict, file, ensure_ascii=False, indent=4)
        return (f"数据已成功保存到 config/schedule/{filename}")
    except Exception as e:
        print(f"保存数据时出错: {e}")


def load_from_json(filename):
    """
    从 JSON 文件中加载数据。
    :param filename: 要加载的文件
    :return: 返回从文件中加载的数据字典
    """
    try:
        with open(f'config/schedule/{filename}', 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except Exception as e:
        print(f"加载数据时出错: {e}")
        return None


def is_temp_week():
    if read_conf('Temp', 'set_week') is None or read_conf('Temp', 'set_week') == '':
        return False
    else:
        return read_conf('Temp', 'set_week')


def is_temp_schedule():
    if read_conf('Temp', 'temp_schedule') is None or read_conf('Temp', 'temp_schedule') == '':
        return False
    else:
        return read_conf('Temp', 'temp_schedule')


def add_shortcut_to_startmenu(file='', icon=''):
    if file == "":
        file_path = os.path.realpath(__file__)
    else:
        file_path = os.path.abspath(file)  # 将相对路径转换为绝对路径

    if icon == "":
        icon_path = file_path  # 如果未指定图标路径，则使用程序路径
    else:
        icon_path = os.path.abspath(icon)  # 将相对路径转换为绝对路径

    # 获取开始菜单文件夹路径
    menu_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs')

    # 快捷方式文件名（使用文件名或自定义名称）
    name = os.path.splitext(os.path.basename(file_path))[0]  # 使用文件名作为快捷方式名称
    shortcut_path = os.path.join(menu_folder, f'{name}.lnk')

    # 创建快捷方式
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = file_path
    shortcut.WorkingDirectory = os.path.dirname(file_path)
    shortcut.IconLocation = icon_path  # 设置图标路径
    shortcut.save()

def add_shortcut(file='', icon=''):
    if file == "":
        file_path = os.path.realpath(__file__)
    else:
        file_path = os.path.abspath(file)  # 将相对路径转换为绝对路径

    if icon == "":
        icon_path = file_path  # 如果未指定图标路径，则使用程序路径
    else:
        icon_path = os.path.abspath(icon)  # 将相对路径转换为绝对路径

    # 获取桌面文件夹路径
    desktop_folder = os.path.join(os.environ['USERPROFILE'], 'Desktop')

    # 快捷方式文件名（使用文件名或自定义名称）
    name = os.path.splitext(os.path.basename(file_path))[0]  # 使用文件名作为快捷方式名称
    shortcut_path = os.path.join(desktop_folder, f'{name}.lnk')

    # 创建快捷方式
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = file_path
    shortcut.WorkingDirectory = os.path.dirname(file_path)
    shortcut.IconLocation = icon_path  # 设置图标路径
    shortcut.save()

def add_to_startup(file_path='', icon_path=''):  # 注册到开机启动
    if file_path == "":
        file_path = os.path.realpath(__file__)
    else:
        file_path = os.path.abspath(file_path)  # 将相对路径转换为绝对路径

    if icon_path == "":
        icon_path = file_path  # 如果未指定图标路径，则使用程序路径
    else:
        icon_path = os.path.abspath(icon_path)  # 将相对路径转换为绝对路径

    # 获取启动文件夹路径
    startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')

    # 快捷方式文件名（使用文件名或自定义名称）
    name = os.path.splitext(os.path.basename(file_path))[0]  # 使用文件名作为快捷方式名称
    shortcut_path = os.path.join(startup_folder, f'{name}.lnk')

    # 创建快捷方式
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = file_path
    shortcut.WorkingDirectory = os.path.dirname(file_path)
    shortcut.IconLocation = icon_path  # 设置图标路径
    shortcut.save()


def remove_from_startup():
    startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
    shortcut_path = os.path.join(startup_folder, f'{name}.lnk')
    if os.path.exists(shortcut_path):
        os.remove(shortcut_path)


def get_time_offset():  # 获取时差偏移
    time_offset = read_conf('General', 'time_offset')
    if time_offset is None or time_offset == '' or time_offset == '0':
        return 0
    else:
        return int(time_offset)


# 示例使用
test_data_dict = {
    "timeline": {
        "start_time_m": (0, 0),
        "start_time_a": (0, 0),
        "am0": "40",
        "fm0": "10",
        "am1": "30",
        "fm1": "10",
        "am2": "40",
        "aa0": "40",
        "fa0": "10",
        "aa1": "40",
        "fa1": "10",
        "aa2": "40",
    },
    "schedule": {
        0: ['语文', '数学', '英语', '语文', '数学', '英语'],
        1: ['语文', '数学', '英语', '语文', '数学', '英语'],
        2: ['语文', '数学', '英语', '语文', '数学', '英语'],
        3: ['语文', '数学', '英语', '语文', '数学', '英语'],
        4: ['语文', '数学', '英语', '语文', '数学', '英语']
    }
}


# if __name__ == '__main__':
    # save_data_to_json(test_data_dict, 'schedule-1.json')
    # loaded_data = load_from_json('schedule-1.json')
    # print(loaded_data)
    # schedule = loaded_data.get('schedule')

    # print(schedule['0'])
    # add_shortcut_to_startmenu('Settings.exe', 'img/favicon.ico')