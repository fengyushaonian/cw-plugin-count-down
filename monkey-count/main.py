from PyQt5 import uic
from datetime import datetime, date, timedelta

from PyQt5.QtWidgets import QHBoxLayout
import configparser
import os
from qfluentwidgets import PrimaryPushButton, PushButton, DisplayLabel
from .ClassWidgets.base import PluginBase, SettingsBase  # 导入CW的基类
import platform

class Plugin(PluginBase):
    def __init__(self, cw_contexts, method):
        super().__init__(cw_contexts, method)
        self.config = self.load_config()
        self.debug_config = self.load_debug_config()
        # 从配置文件读取小组件标题
        widget_name = self.config.get('workday_counter', 'widget_name', fallback='工作日计数器')
        self.method.register_widget('widget_workday_counter.ui', widget_name, 200)

    def load_config(self):
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), 'configs', 'config.ini')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config.read_file(f)
        except FileNotFoundError:
            print(f"配置文件 {config_path} 未找到，使用默认配置。")
        except UnicodeDecodeError:
            print(f"配置文件 {config_path} 编码错误，使用默认配置。")
        return config

    def load_debug_config(self):
        debug_config = configparser.ConfigParser()
        debug_config_path = os.path.join(os.path.dirname(__file__), 'configs', 'debug.ini')
        try:
            with open(debug_config_path, 'r', encoding='utf-8') as f:
                debug_config.read_file(f)
        except FileNotFoundError:
            print(f"调试配置文件 {debug_config_path} 未找到，使用默认配置。")
        except UnicodeDecodeError:
            print(f"调试配置文件 {debug_config_path} 编码错误，使用默认配置。")
        return debug_config

    def execute(self):
        try:
            if self.debug_config.has_section('debug') and self.debug_config.getboolean('debug', 'force_exception', fallback=False):
                raise ValueError("根据配置文件强制抛出的异常")
            self.test_widget = self.method.get_widget('widget_workday_counter.ui')
            if self.test_widget:
                contentLayout = self.test_widget.findChild(QHBoxLayout, 'contentLayout')
                contentLayout.setSpacing(1)
            self.update_workday_count()
        except Exception as e:
            self.handle_exception(e)

    def update_workday_count(self):
        start_date = date.today()
        target_date_str = self.config.get('workday_counter', 'target_date')
        end_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        work_days = 0
        days_diff = (end_date - start_date).days
        for i in range(days_diff + 1):
            current_day = start_date + timedelta(days=i)
            if current_day.weekday() < 5:
                work_days += 1

        display_text = self.config.get('workday_counter', 'display_text', fallback=f'距离 {end_date.strftime("%Y-%m-%d")} 还有 {work_days} 个工作日')
        widget_content = display_text.format(end_date=end_date.strftime("%Y-%m-%d"), work_days=work_days)
        widget_name = self.config.get('workday_counter', 'widget_name', fallback='工作日计数器')
        self.method.change_widget_content('widget_workday_counter.ui', widget_name, widget_content)

    def update(self, cw_contexts):
        try:
            super().update(cw_contexts)
            if hasattr(self, 'test_widget'):
                self.update_workday_count()
        except Exception as e:
            self.handle_exception(e)

    def handle_exception(self, e):
        if self.debug_config.has_section('debug') and self.debug_config.has_option('debug', 'crash_client'):
            crash_client = self.debug_config.getboolean('debug', 'crash_client')
            if crash_client:
                print("根据调试配置，客户端即将崩溃...")
                raise e
            else:
                print(f"发生异常，但根据配置不崩溃客户端: {str(e)}")
        else:
            print(f"发生异常: {str(e)}")


class Settings(SettingsBase):
    def __init__(self, plugin_path, parent=None):
        super().__init__(plugin_path, parent)
        uic.loadUi(os.path.join(self.PATH, "settings.ui"), self)
        open_names_list = self.findChild(PrimaryPushButton, "open_names_list")
        open_names_list.clicked.connect(self.open_names_file)
    def open_names_file(self):
        file_path = os.path.join(self.PATH, "configs", "config.ini")
        if platform.system() == "Windows":
            os.startfile(file_path)
        elif platform.system() == "Linux":
            subprocess.call(["xdg-open", file_path])
        elif platform.system() == "Darwin":
            subprocess.call(["open", file_path])
