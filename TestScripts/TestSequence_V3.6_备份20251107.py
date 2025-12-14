import sys
import os
import subprocess
import json
import configparser
import time
import glob
import re
import codecs
import sqlite3
from collections import deque
from datetime import datetime, timedelta
from uuid import uuid4

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QFileDialog,
    QListWidget, QListWidgetItem, QListView, QProgressBar, QWidget, QMessageBox, QHBoxLayout,
    QMenu, QInputDialog, QDialog, QLabel, QLineEdit, QPushButton,
    QFormLayout, QGroupBox, QGridLayout, QAction, QToolBar,
    QDialogButtonBox, QSplitter, QTabWidget, QComboBox, QDateEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QCalendarWidget, QPlainTextEdit, QTreeView
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QDate, QSignalBlocker
from PyQt5.QtGui import QIcon, QFont, QColor, QBrush, QTextOption

import io
import locale
import sys

import io
import sys


def safe_set_std_stream(stream):
    try:
        if stream is None:
            return io.TextIOWrapper(io.BytesIO(), encoding='utf-8', errors='replace')
        return io.TextIOWrapper(stream.buffer, encoding='utf-8', errors='replace')
    except (AttributeError, OSError):
        return io.TextIOWrapper(io.BytesIO(), encoding='utf-8', errors='replace')


try:
    sys.stdout = safe_set_std_stream(sys.stdout)
    sys.stderr = safe_set_std_stream(sys.stderr)
except Exception:
    pass


os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"


if sys.platform.startswith('win'):
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
    except Exception:
        pass


def resource_path(relative_path):
    """更健壮的资源路径获取函数"""
    try:
        base_path = sys._MEIPASS
        path = os.path.join(base_path, relative_path)
        if os.path.exists(path):
            return path
    except Exception:
        pass

    try:
        base_path = os.path.abspath(".")
        path = os.path.join(base_path, relative_path)
        if os.path.exists(path):
            return path
    except Exception:
        pass

    try:
        base_path = os.path.abspath(".")
        path = os.path.join(base_path, "resources", relative_path)
        if os.path.exists(path):
            return path
    except Exception:
        pass

    return os.path.abspath(relative_path)


def detect_file_encoding(file_path):
    """检测文件编码"""
    import chardet
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding'] or 'utf-8'

# Worker thread for executing Python files
class FileExecutionThread(QThread):
    progress_signal = pyqtSignal(int)  # Signal to update progress bar
    executed_signal = pyqtSignal(str)  # Signal to update executed files list
    error_signal = pyqtSignal(str)  # Signal to show error messages
    current_index_signal = pyqtSignal(int)  # Signal to update current index
    execution_time_signal = pyqtSignal(str)  # Signal to update execution time
    breakpoint_hit_signal = pyqtSignal(int)  # Signal when breakpoint is hit
    console_output_signal = pyqtSignal(str)  # 控制台输出信号
    test_result_signal = pyqtSignal(int, str, str, str)  # 测试结果信号 (序号, 文件名, 运行时间, 结果)
    script_console_signal = pyqtSignal(int, str, str)  # 每个脚本完整控制台输出

    def __init__(self, file_paths, scheme_name, breakpoints):
        super().__init__()
        self.file_paths = file_paths
        self.scheme_name = scheme_name
        self.breakpoints = breakpoints  # Pass breakpoints to thread
        self.running = True  # Control flag for execution
        self.pause_requested = False
        self.stopped_at_breakpoint = False
        self.current_index = 0
        self.log_base_path = None  # 日志基础路径
        self.result_cache = {}  # 用于缓存测试结果
        self.recent_output = deque(maxlen=200)
        self.current_process = None
        self.current_output_lines = []

    def run(self):
        # Determine the Python executable to use
        python_executable = sys.executable
        if hasattr(sys, '_MEIPASS'):
            # If running in a PyInstaller bundle, use 'python' from PATH
            python_executable = "python"

        total_files = len(self.file_paths)
        self.current_index = 0
        
        for self.current_index, file_path in enumerate(self.file_paths):
            if not self.running:
                # If stop requested, break the loop after finishing current file
                break
                
            # Check for pause request
            while self.pause_requested:
                time.sleep(0.1)  # Sleep briefly to reduce CPU usage
                
            # Check if we've hit a breakpoint BEFORE executing
            if self.current_index in self.breakpoints and not self.stopped_at_breakpoint:
                self.stopped_at_breakpoint = True
                self.breakpoint_hit_signal.emit(self.current_index)
                # Wait until resumed
                while self.pause_requested:
                    time.sleep(0.1)
                self.stopped_at_breakpoint = False
                
            start_time = time.time()
            file_name = os.path.basename(file_path)
            base_name = os.path.splitext(file_name)[0]
            
            # 重置当前脚本的结果
            self.current_result = None
            self.recent_output.clear()
            self.current_output_lines = []
            
            # 初始化exec_time变量，避免引用前未定义
            exec_time = 0.0
            process = None
            console_text = ""
            
            try:
                # 在子进程中设置环境变量确保编码正确
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
                # 避免强制UTF-8导致部分conda环境的site模块解析失败
                env.pop('PYTHONUTF8', None)
                
                # 在创建子进程之前添加这段代码
                if sys.platform.startswith('win'):
                    # 只在Windows平台上使用startupinfo
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo_args = {'startupinfo': startupinfo}
                else:
                    # 在非Windows平台上不使用startupinfo
                    startupinfo_args = {}

                # 然后创建子进程
                process = subprocess.Popen(
                    [python_executable, file_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    env=env,
                    text=False,  # 使用二进制模式读取
                    **startupinfo_args
                )
                self.current_process = process
                
                # 实时读取输出 - 使用二进制模式读取然后解码
                while True:
                    output_line = process.stdout.readline()
                    if not output_line and process.poll() is not None:
                        break
                    
                    try:
                        # 尝试UTF-8解码
                        decoded_line = output_line.decode('utf-8').strip()
                    except UnicodeDecodeError:
                        try:
                            # 尝试GBK解码（常见于Windows中文环境）
                            decoded_line = output_line.decode('gbk').strip()
                        except:
                            # 如果两种编码都失败，使用错误替换
                            decoded_line = output_line.decode('utf-8', errors='replace').strip()

                    self.current_output_lines.append(decoded_line)
                    
                    # 跳过空行和调试信息
                    if decoded_line.strip() and not decoded_line.startswith("DEBUG:"):
                        self.console_output_signal.emit(decoded_line)
                        self.recent_output.append(decoded_line.strip())
                    
                    # 修复：使用更可靠的结果检测方式
                    line = decoded_line.lower()
                    
                    # 优先检查不合格 (修复问题1)
                    if "不合格" in line:
                        self.current_result = "不合格"
                    
                    # 然后检查合格
                    elif "合格" in line:
                        self.current_result = "合格"
                        
                    # 捕获特殊结束标记
                    elif "测试结束" in line or "result:" in line or "测试结果" in line:
                        # 使用正则表达式提取测试结果
                        match = re.search(r'(合格|不合格|passed|failed)', line, re.IGNORECASE)
                        if match:
                            result = match.group(1)
                            if result.lower() in ["合格", "passed"]:
                                self.current_result = "合格"
                            else:
                                self.current_result = "不合格"

                # 仅在脚本显式输出合格/不合格时判定结果，避免误判

                console_text = "\n".join(self.current_output_lines)
                self.script_console_signal.emit(self.current_index, file_name, console_text)
                
                # 检查进程是否成功结束
                return_code = process.poll()
                if return_code != 0:
                    self.error_signal.emit(f"执行错误 (返回码 {return_code}): {file_name}")
                
                # 缓存当前文件的结果
                self.result_cache[file_name] = self.current_result
                
                # Emit signal for successfully executed file
                self.executed_signal.emit(f"{file_name} - 已执行")
                
                # 计算执行时间
                exec_time = time.time() - start_time
                
                # 发送测试结果信号
                result = self.current_result or "结果未获取"
                self.test_result_signal.emit(self.current_index, file_name, f"{exec_time:.2f}s", result)
                
            except Exception as e:
                # 在异常情况下也要计算执行时间
                exec_time = time.time() - start_time
                console_text = "\n".join(self.current_output_lines)
                self.script_console_signal.emit(self.current_index, file_name, console_text)
                
                # Emit error signal and stop execution
                self.error_signal.emit(f"执行 {file_name} 时出错:\n{str(e)}")
                
                # 发送带错误信息的测试结果
                self.test_result_signal.emit(self.current_index, file_name, f"{exec_time:.2f}s", f"错误: {str(e)}")
                continue  # 继续下一个脚本的执行
            finally:
                if process and process.stdout:
                    try:
                        process.stdout.close()
                    except Exception:
                        pass
                self.current_process = None
                self.current_output_lines = []
            
            # 发送执行时间信号
            self.execution_time_signal.emit(
                f"{exec_time:.2f}s"
            )
            
            # Emit progress signal
            self.current_index_signal.emit(self.current_index + 1)
            progress = int(((self.current_index + 1) / total_files) * 100)
            self.progress_signal.emit(progress)
            
            # 修复问题2：添加短暂延迟防止资源占用过高导致界面卡顿
            time.sleep(0.05)

    def set_log_base_path(self, path):
        """设置日志基础路径"""
        self.log_base_path = path

    def pause(self):
        """Pause execution after current file completes."""
        self.pause_requested = True
        
    def resume(self):
        """Resume execution."""
        self.pause_requested = False
        
    def stop(self):
        """Request the thread to stop execution after current file completes."""
        self.running = False
        self.pause_requested = False
        if self.current_process and self.current_process.poll() is None:
            try:
                self.current_process.terminate()
            except Exception:
                try:
                    self.current_process.kill()
                except Exception:
                    pass

    def _infer_result_from_recent_output(self):
        """从近期输出中推断测试结果"""
        if not self.recent_output:
            return None

        failure_clues = (
            "不合格", "failed", "fail", "失败", "错误", "异常", "traceback", "ng"
        )

        for raw_line in reversed(self.recent_output):
            line = raw_line.strip().lower()
            if not line:
                continue
            if any(clue in line for clue in failure_clues):
                return "不合格"

        return None


class FolderScriptsDialog(QDialog):
    """选择文件夹脚本时的确认对话框"""

    def __init__(self, folder_path, scripts, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择要导入的脚本")
        self.setModal(True)
        self.resize(520, 420)

        layout = QVBoxLayout(self)

        folder_label = QLabel(f"文件夹: {folder_path}")
        folder_label.setWordWrap(True)
        layout.addWidget(folder_label)

        self.script_list = QListWidget()
        self.script_list.setSelectionMode(QAbstractItemView.MultiSelection)
        for path in scripts:
            item = QListWidgetItem(os.path.basename(path) or path)
            item.setToolTip(path)
            item.setData(Qt.UserRole, path)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self.script_list.addItem(item)
        layout.addWidget(self.script_list)

        button_row = QHBoxLayout()
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(lambda: self._set_all_checks(Qt.Checked))
        button_row.addWidget(select_all_btn)

        select_none_btn = QPushButton("全不选")
        select_none_btn.clicked.connect(lambda: self._set_all_checks(Qt.Unchecked))
        button_row.addWidget(select_none_btn)

        invert_btn = QPushButton("反选")
        invert_btn.clicked.connect(self._invert_checks)
        button_row.addStretch()
        button_row.addWidget(invert_btn)
        layout.addLayout(button_row)

        self.count_label = QLabel()
        layout.addWidget(self.count_label)
        self._update_count_label()

        self.script_list.itemChanged.connect(self._update_count_label)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _set_all_checks(self, state):
        for index in range(self.script_list.count()):
            item = self.script_list.item(index)
            item.setCheckState(state)

    def _invert_checks(self):
        for index in range(self.script_list.count()):
            item = self.script_list.item(index)
            item.setCheckState(Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked)

    def _update_count_label(self):
        total = self.script_list.count()
        selected = sum(1 for _ in self.selected_files())
        self.count_label.setText(f"已选择 {selected} / {total} 个脚本")

    def selected_files(self):
        for index in range(self.script_list.count()):
            item = self.script_list.item(index)
            if item.checkState() == Qt.Checked:
                yield item.data(Qt.UserRole)


class TestSequenceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python自动化测试脚本序列执行工具V3.6")
        self.resize(1625, 950)
        QTimer.singleShot(0, self.center_on_screen)
        # 在界面初始化前确保编码正确
        self.fix_encoding_environment()

        # 初始化搜索位置
        self.search_position = 0

        # 在主窗口初始化代码中
        icon_path = resource_path("Icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            # 创建警告日志但不中断程序
            error_msg = f"Icon file not found: {icon_path}"
            print(error_msg)
            # 可以记录到日志文件
            with open("error.log", "a") as log:
                log.write(f"{datetime.now()}: {error_msg}\n")

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Add menu bar
        self.menu_bar = self.menuBar()
        
        # File menu
        file_menu = self.menu_bar.addMenu("文件")
        load_action = file_menu.addAction("加载脚本")
        load_action.triggered.connect(self.load_files)

        load_scheme_action = file_menu.addAction("加载方案")
        load_scheme_action.triggered.connect(self.load_scheme)
        
        save_action = file_menu.addAction("保存方案")
        save_action.triggered.connect(self.save_scheme)
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("退出")
        exit_action.triggered.connect(self.close)
        
        # Settings menu
        settings_menu = self.menu_bar.addMenu("设置")
        settings_action = settings_menu.addAction("配置")
        settings_action.triggered.connect(self.show_configure)

        # Add toolbar with action buttons
        self.toolbar = QToolBar("主工具栏")
        self.addToolBar(self.toolbar)
        self.toolbar.setMovable(True)
        
        # 修复工具栏高度问题 - 设置固定高度
        self.toolbar.setFixedHeight(40)  # 设置固定高度避免变化
        self.toolbar.setIconSize(QSize(32, 32))  # 设置图标大小

        # 为工具栏按钮添加图标路径
        icon_path_run = resource_path("run.png")
        icon_path_stop = resource_path("stop.png")
        icon_path_pause = resource_path("pause.png")
        icon_path_resume = resource_path("resume.png")
        icon_path_single = resource_path("single.png")
        icon_path_breakpoint = resource_path("breakpoint.png")
        icon_path_pin = resource_path("pin.png")  # 新增钉住图标路径
        icon_path_pinned = resource_path("pinned.png")  # 新增已钉住图标路径

        # Run action
        run_action = QAction("运行全部", self)
        if os.path.exists(icon_path_run):
            run_action.setIcon(QIcon(icon_path_run))
        run_action.triggered.connect(self.run_files)
        run_action.setShortcut("F5")
        run_action.setToolTip("运行整个方案 (F5)")
        self.toolbar.addAction(run_action)
        self.run_action = run_action

        # Run single action
        run_single_action = QAction("运行单个", self)
        if os.path.exists(icon_path_single):
            run_single_action.setIcon(QIcon(icon_path_single))
        run_single_action.triggered.connect(self.run_single_file)
        run_single_action.setShortcut("F6")
        run_single_action.setToolTip("运行选中的单个文件 (F6)")
        self.toolbar.addAction(run_single_action)
        self.run_single_action = run_single_action

        # Set breakpoint action
        breakpoint_action = QAction("设置断点", self)
        if os.path.exists(icon_path_breakpoint):
            breakpoint_action.setIcon(QIcon(icon_path_breakpoint))
        breakpoint_action.triggered.connect(self.toggle_breakpoint)
        breakpoint_action.setShortcut("F9")
        breakpoint_action.setToolTip("在选中行设置/清除断点 (极F9)")
        self.toolbar.addAction(breakpoint_action)
        self.breakpoint_action = breakpoint_action

        # Pause action (will be enabled only during execution)
        pause_action = QAction("暂停执行", self)
        if os.path.exists(icon_path_pause):
            pause_action.setIcon(QIcon(icon_path_pause))
        pause_action.triggered.connect(self.pause_execution)
        pause_action.setShortcut("F7")
        pause_action.setToolTip("暂停执行 (F7)")
        self.toolbar.addAction(pause_action)
        self.pause_action = pause_action
        self.pause_action.setEnabled(False)

        # Resume action (will be enabled only during pause)
        resume_action = QAction("继续执行", self)
        if os.path.exists(icon_path_resume):
            resume_action.setIcon(QIcon(icon_path_resume))
        resume_action.triggered.connect(self.resume_execution)
        resume_action.setShortcut("F8")
        resume_action.setToolTip("继续执行 (F8)")
        self.toolbar.addAction(resume_action)
        self.resume_action = resume_action
        self.resume_action.setEnabled(False)

        # Stop action
        stop_action = QAction("停止执行", self)
        if os.path.exists(icon_path_stop):
            stop_action.setIcon(QIcon(icon_path_stop))
        stop_action.triggered.connect(self.stop_execution)
        stop_action.setShortcut("F12")
        stop_action.setToolTip("停止执行 (F12)")
        self.toolbar.addAction(stop_action)
        self.stop_action = stop_action
        self.stop_action.setEnabled(False)
        
        # 新增：钉住窗口按钮
        self.pin_action = QAction("钉住窗口", self)
        self.pin_action.setCheckable(True)
        self.pin_action.triggered.connect(self.toggle_pin_on_top)
        if os.path.exists(icon_path_pin):
            self.pin_action.setIcon(QIcon(icon_path_pin))
        self.pin_action.setToolTip("将窗口钉在最上层")
        self.toolbar.addAction(self.pin_action)

        # 创建一个 QTabWidget 作为主容器
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        # 第一个标签页：脚本与结果
        self.tab1 = QWidget()
        self.tab_layout1 = QVBoxLayout(self.tab1)
        self.tab_widget.addTab(self.tab1, "脚本与结果")

        # 使用 QSplitter 创建可调整大小的布局（水平方向）
        self.splitter_tab1 = QSplitter(Qt.Horizontal)
        self.tab_layout1.addWidget(self.splitter_tab1)

        # 左侧面板：文件列表
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)

        list_header_layout = QHBoxLayout()
        list_header_label = QLabel("待执行脚本列表")
        list_header_layout.addWidget(list_header_label)
        list_header_layout.addStretch()
        self.add_folder_button = QPushButton("添加文件夹")
        self.add_folder_button.setToolTip("将文件夹作为脚本组添加")
        self.add_folder_button.clicked.connect(self.add_python_folder)
        list_header_layout.addWidget(self.add_folder_button)
        self.left_layout.addLayout(list_header_layout)

        self.file_list = QListWidget()
        self.file_list.setWordWrap(True)
        self.file_list.setAlternatingRowColors(True)
        self.file_list.itemDoubleClicked.connect(self.on_file_list_item_double_clicked)
        self.left_layout.addWidget(self.file_list)

        # 控制台统一样式
        self.console_dark_style = """
            QPlainTextEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
                background-color: #1E1E1E;
                color: #DCDCDC;
                selection-background-color: #3A3A3A;
            }
        """
        # 右侧面板：仅显示当前结果
        self.right_panel_results = QWidget()
        self.right_layout_results = QVBoxLayout(self.right_panel_results)

        self.test_result_table = QTableWidget()
        self.test_result_table.setColumnCount(5)
        self.test_result_table.setHorizontalHeaderLabels(["序号", "脚本名称", "执行时间", "运行时间", "测试结果"])
        self.test_result_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.test_result_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.test_result_table.setAlternatingRowColors(True)
        self.test_result_table.verticalHeader().setVisible(False)
        header = self.test_result_table.horizontalHeader()
        header.setFont(QFont("Arial", 9, QFont.Bold))
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        self.clear_results_button = QPushButton("清除结果")
        self.clear_results_button.setIcon(QIcon(resource_path("clear.png")))
        self.clear_results_button.clicked.connect(self.clear_test_results)

        self.export_results_button = QPushButton("导出结果")
        self.export_results_button.setIcon(QIcon(resource_path("export.png")))
        self.export_results_button.clicked.connect(self.export_test_results)

        toolbar_layout = QHBoxLayout()
        toolbar_layout.addWidget(self.clear_results_button)
        toolbar_layout.addWidget(self.export_results_button)
        toolbar_layout.addStretch()

        self.right_layout_results.addLayout(toolbar_layout)
        self.right_layout_results.addWidget(self.test_result_table)

        # 添加到拆分器
        self.splitter_tab1.addWidget(self.left_panel)
        self.splitter_tab1.addWidget(self.right_panel_results)

        # 设置初始分割比例
        self.splitter_tab1.setSizes([320, 680])

        # 脚本与结果页内的执行进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.tab_layout1.addWidget(self.progress_bar)

        # 第二个标签页：控制台输出 - 修复卡顿问题
        self.tab2 = QWidget()
        self.tab_layout2 = QVBoxLayout(self.tab2)
        self.tab_widget.addTab(self.tab2, "控制台输出")

        # 控制台输出 - 改为QPlainTextEdit提高性能
        self.console_output = QPlainTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setWordWrapMode(QTextOption.WrapAnywhere)
        self.console_output.setStyleSheet(self.console_dark_style)
        # 设置控制台编码为UTF-8
        self.console_output.setPlainText("")
        self.console_output.document().setDefaultFont(QFont("Consolas", 10))

        # 添加搜索框、保存按钮和清除按钮
        self.search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索...")
        self.search_button = QPushButton("搜索")
        self.search_button.clicked.connect(self.search_console_output)
        self.save_console_button = QPushButton("保存日志")
        self.save_console_button.clicked.connect(self.save_console_output)
        self.clear_console_button = QPushButton("清除控制台输出")
        self.clear_console_button.clicked.connect(self.clear_console_output)

        self.search_layout.addWidget(self.search_input)
        self.search_layout.addWidget(self.search_button)
        self.search_layout.addWidget(self.save_console_button)
        self.search_layout.addWidget(self.clear_console_button)

        self.tab_layout2.addWidget(QLabel("控制台输出"))
        self.tab_layout2.addWidget(self.console_output)
        self.tab_layout2.addLayout(self.search_layout)
        
        # 第三个标签页：历史记录
        self.history_tab = QWidget()
        self.history_layout = QVBoxLayout(self.history_tab)
        self.history_layout.setContentsMargins(6, 6, 6, 6)
        self.history_layout.setSpacing(6)

        history_filter_layout = QHBoxLayout()
        history_filter_layout.addWidget(QLabel("开始日期:"))
        self.history_start_date = QDateEdit(QDate.currentDate().addDays(-7))
        self.history_start_date.setCalendarPopup(True)
        self.history_start_date.setDisplayFormat("yyyy-MM-dd")
        history_filter_layout.addWidget(self.history_start_date)

        history_filter_layout.addWidget(QLabel("结束日期:"))
        self.history_end_date = QDateEdit(QDate.currentDate())
        self.history_end_date.setCalendarPopup(True)
        self.history_end_date.setDisplayFormat("yyyy-MM-dd")
        history_filter_layout.addWidget(self.history_end_date)

        history_filter_layout.addWidget(QLabel("方案:"))
        self.history_scheme_combo = QComboBox()
        self.history_scheme_combo.setEditable(False)
        self.history_scheme_combo.setMinimumWidth(160)
        history_filter_layout.addWidget(self.history_scheme_combo)

        self.history_refresh_button = QPushButton("查询")
        self.history_refresh_button.clicked.connect(self.query_history_runs)
        history_filter_layout.addWidget(self.history_refresh_button)

        self.history_reset_button = QPushButton("重置")
        self.history_reset_button.clicked.connect(self.reset_history_filters)
        history_filter_layout.addWidget(self.history_reset_button)

        history_filter_layout.addStretch()
        self.history_layout.addLayout(history_filter_layout)

        self.history_summary_label = QLabel("请选择运行记录查看详情")
        self.history_summary_label.setWordWrap(True)
        self.history_summary_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.history_summary_label.setVisible(False)
        self.history_layout.addWidget(self.history_summary_label)

        self.history_splitter = QSplitter(Qt.Vertical)
        self.history_layout.addWidget(self.history_splitter)

        history_runs_container = QWidget()
        history_runs_layout = QVBoxLayout(history_runs_container)
        history_runs_layout.setContentsMargins(0, 0, 0, 0)

        self.history_runs_table = QTableWidget()
        self.history_runs_table.setColumnCount(8)
        self.history_runs_table.setHorizontalHeaderLabels([
            "记录ID", "方案", "开始时间", "结束时间", "通过", "失败", "待判定", "耗时(s)"
        ])
        self.history_runs_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_runs_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_runs_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.history_runs_table.verticalHeader().setVisible(False)
        self.history_runs_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.history_runs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.history_runs_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.history_runs_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.history_runs_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.history_runs_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.history_runs_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.history_runs_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.history_runs_table.itemSelectionChanged.connect(self.on_history_run_selected)
        history_runs_layout.addWidget(self.history_runs_table)

        self.history_splitter.addWidget(history_runs_container)

        history_detail_splitter = QSplitter(Qt.Horizontal)
        self.history_splitter.addWidget(history_detail_splitter)

        history_scripts_container = QWidget()
        history_scripts_layout = QVBoxLayout(history_scripts_container)
        history_scripts_layout.setContentsMargins(0, 0, 0, 0)

        self.history_scripts_table = QTableWidget()
        self.history_scripts_table.setColumnCount(5)
        self.history_scripts_table.setHorizontalHeaderLabels([
            "序号", "脚本名称", "执行时间", "运行时间", "测试结果"
        ])
        self.history_scripts_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_scripts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_scripts_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.history_scripts_table.verticalHeader().setVisible(False)
        self.history_scripts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.history_scripts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.history_scripts_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.history_scripts_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.history_scripts_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.history_scripts_table.itemSelectionChanged.connect(self.on_history_script_selected)
        history_scripts_layout.addWidget(self.history_scripts_table)

        history_detail_splitter.addWidget(history_scripts_container)

        self.history_detail_tabs = QTabWidget()

        history_console_container = QWidget()
        history_console_layout = QVBoxLayout(history_console_container)
        history_console_layout.setContentsMargins(0, 0, 0, 0)
        self.history_console_text = QPlainTextEdit()
        self.history_console_text.setReadOnly(True)
        self.history_console_text.setWordWrapMode(QTextOption.NoWrap)
        self.history_console_text.setStyleSheet(self.console_dark_style)
        self.history_console_text.document().setDefaultFont(QFont("Consolas", 10))
        history_console_layout.addWidget(self.history_console_text)
        self.history_detail_tabs.addTab(history_console_container, "控制台输出")

        history_config_container = QWidget()
        history_config_layout = QVBoxLayout(history_config_container)
        history_config_layout.setContentsMargins(0, 0, 0, 0)
        self.history_config_text = QPlainTextEdit()
        self.history_config_text.setReadOnly(True)
        self.history_config_text.setWordWrapMode(QTextOption.NoWrap)
        self.history_config_text.document().setDefaultFont(QFont("Consolas", 10))
        self.history_config_text.setStyleSheet(self.console_dark_style)
        history_config_layout.addWidget(self.history_config_text)
        self.history_detail_tabs.addTab(history_config_container, "配置快照")

        history_detail_splitter.addWidget(self.history_detail_tabs)

        self.history_splitter.setSizes([220, 480])
        history_detail_splitter.setSizes([420, 260])

        self.tab_widget.addTab(self.history_tab, "历史记录")

        # File paths and results initialization
        self.file_paths = []
        self.groups = []  # [{"id": uuid, "name": str, "files": [paths]}]
        self.flat_script_map = []  # 缓存脚本扁平结构
        self.test_results = []  # 存储测试结果
        self.execution_thread = None  # Thread for file execution
        self.scheme_name = "未命名方案"  # Default scheme name
        self.breakpoint_paths = set()  # 使用脚本路径记录断点
        self.is_paused = False
        self.is_running = False
        self.current_file_index = -1  # Current executing file index
        self.executed_count = 0  # 记录实际执行的脚本数量

        # Statistics Panel
        self.create_statistics_panel(self.tab_layout1)
        self.tab_layout1.setStretch(0, 1)
        self.tab_layout1.setStretch(1, 0)
        self.tab_layout1.setStretch(2, 0)
        
        # Timer for updating elapsed time
        self.elapsed_timer = QTimer()
        self.elapsed_timer.timeout.connect(self.update_elapsed_time)
        
        # Execution time variables
        self.start_time = None
        self.elapsed_time = timedelta(0)

        # Enable custom context menu for file_list
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_context_menu)

        # Enable drag-and-drop for file_list
        self.file_list.setDragDropMode(QListWidget.InternalMove)
        self.file_list.model().rowsMoved.connect(self.update_file_paths_on_drag)

        # Enable custom context menu for test_result_table
        self.test_result_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.test_result_table.customContextMenuRequested.connect(self.show_test_result_context_menu)

        # Initialize configuration
        self.config_file = resource_path("Configure.ini")
        self.init_config()

        # 数据库和运行状态
        self.current_run_id = None
        self.current_run_identifier = None
        self.current_run_start_time = None
        self.displayed_run_id = None
        self.console_buffer = {}
        self.pending_script_records = {}
        self.current_run_console = {}
        self.console_list_items = {}
        self.history_selected_run_id = None
        self.history_run_records = []
        self.history_script_cache = {}
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.project_root, "test_sequence_results.db")
        self.init_database()
        self.initialize_history_view()

    def fix_encoding_environment(self):
        """确保中文编码环境正确设置"""
        # 设置Python IO编码
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONUTF8'] = '1'  # 强制Python使用UTF-8模式
        
        # 修复QT文本编码
        try:
            from PyQt5.QtCore import QTextCodec
            QTextCodec.setCodecForLocale(QTextCodec.codecForName('UTF-8'))
        except ImportError:
            pass

    # 测试结果相关的新增函数
    def add_test_result(self, index, file_name, execution_time, result):
        """添加测试结果到结果表格并同步保存数据库"""
        run_id = self.current_run_id
        self.displayed_run_id = run_id if run_id is not None else self.displayed_run_id

        sequence = index + 1
        row_position = self.test_result_table.rowCount()
        self.test_result_table.insertRow(row_position)

        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sequence_item = QTableWidgetItem(str(sequence))
        sequence_item.setTextAlignment(Qt.AlignCenter)
        sequence_item.setData(Qt.UserRole, (run_id, sequence))
        self.test_result_table.setItem(row_position, 0, sequence_item)

        file_item = QTableWidgetItem(file_name)
        self.test_result_table.setItem(row_position, 1, file_item)

        exec_time_item = QTableWidgetItem(time_str)
        self.test_result_table.setItem(row_position, 2, exec_time_item)

        duration_item = QTableWidgetItem(execution_time)
        duration_item.setTextAlignment(Qt.AlignCenter)
        self.test_result_table.setItem(row_position, 3, duration_item)

        result_item = QTableWidgetItem(result)
        result_item.setTextAlignment(Qt.AlignCenter)
        if "不合格" in result:
            result_item.setForeground(QBrush(QColor(220, 0, 0)))
        elif "合格" in result:
            result_item.setForeground(QBrush(QColor(0, 200, 0)))
        else:
            result_item.setForeground(QBrush(QColor(150, 150, 150)))
        self.test_result_table.setItem(row_position, 4, result_item)

        self.test_result_table.scrollToBottom()

        self.test_results.append({
            "file_name": file_name,
            "execution_time": execution_time,
            "result": result,
            "timestamp": time_str,
            "sequence": sequence,
            "run_id": run_id,
        })

        # 更新控制台脚本列表
        if hasattr(self, "current_console_list"):
            item_text = f"{sequence}. {file_name}"
            console_item = QListWidgetItem(item_text)
            console_item.setData(Qt.UserRole, index)
            if "不合格" in result:
                console_item.setForeground(QBrush(QColor(220, 0, 0)))
            elif "合格" in result:
                console_item.setForeground(QBrush(QColor(0, 200, 0)))
            else:
                console_item.setForeground(QBrush(QColor(150, 150, 150)))
            console_item.setData(Qt.UserRole + 1, {
                "result": result,
                "execution_time": execution_time,
            })
            console_item.setToolTip(
                self.build_console_tooltip(result, execution_time, self.current_run_console.get(index))
            )
            self.current_console_list.addItem(console_item)
            self.console_list_items[index] = console_item

            current_item = self.current_console_list.currentItem()
            if self.current_console_list.count() == 1:
                self.current_console_list.setCurrentRow(0)
            elif current_item and current_item.data(Qt.UserRole) == index:
                self.display_current_console_output(index)

        self.update_test_result_stats()
        self.test_result_table.resizeColumnsToContents()
        self.test_result_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        self.save_script_result_to_db(index, file_name, execution_time, result, time_str)

    def save_script_result_to_db(self, index, file_name, execution_time, result, timestamp):
        """保存脚本结果到数据库"""
        if self.current_run_id is None:
            return

        payload = {
            "run_id": self.current_run_id,
            "sequence": index + 1,
            "file_name": file_name,
            "execution_timestamp": timestamp,
            "duration_seconds": self.parse_duration(execution_time),
            "result": result,
        }

        console_text = self.console_buffer.pop(index, None)
        if console_text is not None:
            payload["console_output"] = console_text
            self._insert_script_result(payload)
        else:
            self.pending_script_records[index] = payload

    def _insert_script_result(self, payload):
        """执行脚本结果插入"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO run_scripts
                    (run_id, sequence, file_name, execution_timestamp, duration_seconds, result, console_output)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        payload.get("run_id"),
                        payload.get("sequence"),
                        payload.get("file_name"),
                        payload.get("execution_timestamp"),
                        payload.get("duration_seconds"),
                        payload.get("result"),
                        payload.get("console_output", ""),
                    ),
                )
                conn.commit()
        except Exception as e:
            print(f"写入脚本结果失败: {e}")

    def capture_script_console(self, index, file_name, console_text):
        """缓存脚本控制台输出并尝试写入数据库"""
        self.console_buffer[index] = console_text
        self.current_run_console[index] = console_text
        if index in self.pending_script_records:
            payload = self.pending_script_records.pop(index)
            payload["console_output"] = console_text
            self._insert_script_result(payload)

        if hasattr(self, "console_list_items") and index in self.console_list_items:
            item = self.console_list_items[index]
            meta = item.data(Qt.UserRole + 1) or {}
            item.setToolTip(
                self.build_console_tooltip(
                    meta.get("result", ""),
                    meta.get("execution_time", ""),
                    console_text,
                )
            )
            if self.current_console_list.currentItem() is item:
                self.display_current_console_output(index)

    def parse_duration(self, execution_time):
        try:
            cleaned = execution_time.replace('s', '').strip()
            return float(cleaned) if cleaned else 0.0
        except Exception:
            return 0.0

    def build_console_tooltip(self, result, execution_time, console_text):
        tooltip = f"结果: {result}\n运行时间: {execution_time}"
        if console_text:
            lines = [line for line in console_text.strip().splitlines() if line.strip()]
            if lines:
                last_line = lines[-1]
                tooltip += f"\n最近输出: {last_line[:120]}"
        return tooltip

    def on_current_console_selection_changed(self, row):
        if not hasattr(self, "current_console_list") or not hasattr(self, "current_console_text"):
            return
        if row < 0:
            if hasattr(self, "current_console_list") and self.current_console_list.count() == 0:
                self.current_console_text.setPlainText("等待脚本执行...")
            else:
                self.current_console_text.setPlainText("请选择脚本查看控制台输出")
            return
        item = self.current_console_list.item(row)
        if item is None:
            self.current_console_text.clear()
            return
        index = item.data(Qt.UserRole)
        if index is None:
            self.current_console_text.clear()
            return
        self.display_current_console_output(index)

    def display_current_console_output(self, index):
        if not hasattr(self, "current_console_text"):
            return
        console_text = self.current_run_console.get(index)
        if console_text is None and self.current_run_id is not None:
            console_text = self.fetch_script_console_from_db(self.current_run_id, index + 1)
            if console_text:
                self.current_run_console[index] = console_text

        if console_text:
            self.current_console_text.setPlainText(console_text)
        else:
            self.current_console_text.setPlainText("暂无控制台输出")

        cursor = self.current_console_text.textCursor()
        cursor.movePosition(cursor.End)
        self.current_console_text.setTextCursor(cursor)
        self.current_console_text.ensureCursorVisible()

    def fetch_script_console_from_db(self, run_id, sequence):
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute(
                    "SELECT console_output FROM run_scripts WHERE run_id = ? AND sequence = ?",
                    (run_id, sequence),
                ).fetchone()
                if row:
                    return row[0] or ""
        except Exception as e:
            print(f"读取控制台输出失败: {e}")
        return ""

    def get_current_config_snapshot(self):
        snapshot = {"Paths": {}, "Breakpoints": sorted(list(self.breakpoint_paths))}
        if self.config.has_section("Paths"):
            for key, value in self.config.items("Paths"):
                snapshot["Paths"][key] = value
        return snapshot

    def start_run_record(self, total_scripts, scheme_label):
        run_start = datetime.now()
        normalized_label = (scheme_label or "").strip()
        if not normalized_label or normalized_label == "未命名方案":
            run_identifier = f"自定义方案_{run_start.strftime('%Y%m%d_%H%M%S')}"
        else:
            run_identifier = normalized_label

        stats_payload = {
            "total_scripts": total_scripts,
            "start_time": run_start.strftime("%Y-%m-%d %H:%M:%S"),
        }

        self.console_buffer.clear()
        self.pending_script_records.clear()

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO runs
                    (scheme_name, run_identifier, start_time, total_scripts, config_json, stats_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        scheme_label,
                        run_identifier,
                        run_start.strftime("%Y-%m-%d %H:%M:%S"),
                        total_scripts,
                        json.dumps(self.get_current_config_snapshot(), ensure_ascii=False),
                        json.dumps(stats_payload, ensure_ascii=False),
                    ),
                )
                self.current_run_id = cursor.lastrowid
                conn.commit()
        except Exception as e:
            print(f"创建测试记录失败: {e}")
            self.current_run_id = None

        self.current_run_identifier = run_identifier
        self.current_run_start_time = run_start
        self.displayed_run_id = self.current_run_id

    def prepare_run_context(self, total_scripts, scheme_label):
        self.test_result_table.setRowCount(0)
        self.test_results = []
        self.console_buffer.clear()
        self.pending_script_records.clear()
        self.current_run_console.clear()
        self.console_list_items.clear()
        if hasattr(self, "current_console_list"):
            self.current_console_list.clear()
        if hasattr(self, "current_console_text"):
            self.current_console_text.setPlainText("等待脚本执行...")
        self.executed_count = 0
        self.current_file_index = -1

        self.start_run_record(total_scripts, scheme_label)

        display_name = self.current_run_identifier or scheme_label
        if display_name:
            self.scheme_value.setText(display_name)

        self.total_value.setText(str(total_scripts))
        self.current_value.setText(f"0 / {total_scripts}")
        self.update_pending_exec_count()
        self.update_test_result_stats()

    def finalize_run_record(self, pass_count, fail_count, pending_count):
        if self.current_run_id is None:
            self.console_buffer.clear()
            self.pending_script_records.clear()
            return

        end_time = datetime.now()
        duration_seconds = 0.0
        if self.current_run_start_time:
            duration_seconds = (end_time - self.current_run_start_time).total_seconds()

        stats_payload = {
            "total_scripts": self.total_value.text(),
            "executed": self.executed_count,
            "pass": pass_count,
            "fail": fail_count,
            "pending": pending_count,
            "elapsed": self.elapsed_time_value.text(),
        }

        if self.pending_script_records:
            for payload in list(self.pending_script_records.values()):
                payload.setdefault("console_output", "")
                self._insert_script_result(payload)
            self.pending_script_records.clear()
        self.console_buffer.clear()

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE runs
                    SET end_time = ?,
                        executed_count = ?,
                        pass_count = ?,
                        fail_count = ?,
                        pending_count = ?,
                        duration_seconds = ?,
                        stats_json = ?
                    WHERE id = ?
                    """,
                    (
                        end_time.strftime("%Y-%m-%d %H:%M:%S"),
                        self.executed_count,
                        pass_count,
                        fail_count,
                        pending_count,
                        duration_seconds,
                        json.dumps(stats_payload, ensure_ascii=False),
                        self.current_run_id,
                    ),
                )
                conn.commit()
        except Exception as e:
            print(f"更新测试记录失败: {e}")

        self.displayed_run_id = self.current_run_id
        self.history_script_cache.pop(self.current_run_id, None)
        self.history_selected_run_id = self.current_run_id
        self.refresh_history_view(auto_select_latest=True)


    def clear_test_results(self):
        """清除所有测试结果"""
        reply = QMessageBox.question(
            self, 
            "确认清除", 
            "确定要清除所有测试结果吗?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.test_result_table.setRowCount(0)
            self.test_results = []
            # 更新测试结果统计
            self.update_test_result_stats()
    
    def export_test_results(self):
        """导出测试结果到CSV文件"""
        if self.test_result_table.rowCount() == 0:
            QMessageBox.warning(self, "没有结果", "没有可导出的测试结果")
            return
            
        # 安全获取配置路径
        try:
            self.config.read(self.config_file)
            path2 = self.config.get("Paths", "Path2", fallback="")
        except Exception as e:
            print(f"读取配置错误: {e}")
            path2 = ""
        
        # 确保默认路径有效
        if not path2 or not os.path.exists(path2):
            # 使用用户文档目录作为默认路径
            path2 = os.path.join(os.path.expanduser("~"), "Documents")
            # 如果文档目录不存在，使用用户主目录
            if not os.path.exists(path2):
                path2 = os.path.expanduser("~")
        
        # 构建默认文件名
        default_filename = f"测试结果_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        
        # 确保路径有效后再拼接
        if path2 and os.path.exists(path2):
            default_path = os.path.join(path2, default_filename)
        else:
            default_path = default_filename
        
        # 获取用户选择的保存路径
        file_name, _ = QFileDialog.getSaveFileName(
            self, 
            "导出测试结果", 
            default_path,
            "CSV文件 (*.csv)"
        )
        
        # 如果用户取消了操作
        if not file_name:
            return
            
        try:
            # 确保文件所在目录存在
            output_dir = os.path.dirname(file_name)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # 使用带BOM的UTF-8编码解决Excel中文乱码问题
            with codecs.open(file_name, "w", "utf_8_sig") as f:
                # 写入标题行
                f.write("序号,脚本名称,执行时间,运行时间,测试结果\n")
                
                # 写入数据
                for row in range(self.test_result_table.rowCount()):
                    row_data = []
                    for col in range(5):  # 改为5列
                        item = self.test_result_table.item(row, col)
                        if item:
                            text = item.text()
                            # 转义特殊字符
                            if any(char in text for char in [',', '"', '\n']):
                                # 修复：分两步处理
                                escaped_text = text.replace('"', '""')  # 将双引号替换为两个双引号
                                text = f'"{escaped_text}"'  # 将整个字符串用双引号括起来
                            row_data.append(text)
                        else:
                            row_data.append("")
                    f.write(",".join(row_data) + "\n")
                    
            QMessageBox.information(self, "导出成功", f"测试结果已成功导出到:\n{file_name}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出测试结果时发生错误:\n{str(e)}\n\n请检查路径权限或磁盘空间")
    
    def select_history_date(self):
        """选择历史日期查看结果"""
        dialog = QDialog(self)
        dialog.setWindowTitle("选择历史日期")
        layout = QVBoxLayout(dialog)
        
        calendar = QCalendarWidget()
        calendar.setGridVisible(True)
        calendar.setSelectedDate(QDate.currentDate())
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        layout.addWidget(calendar)
        layout.addWidget(button_box)
        
        if dialog.exec_() == QDialog.Accepted:
            if not hasattr(self, "date_selector"):
                return
            selected_date = calendar.selectedDate().toString("yyyy-MM-dd")
            self.date_selector.setText(selected_date)
            self.load_history_results(selected_date)
    
    def load_history_results(self, date_str):
        """根据选定日期更新历史记录筛选"""
        if not hasattr(self, "history_start_date"):
            return

        selected_date = QDate.fromString(date_str, "yyyy-MM-dd")
        if selected_date.isValid():
            self.history_start_date.setDate(selected_date)
            self.history_end_date.setDate(selected_date)

        self.populate_history_scheme_options()
        self.history_scheme_combo.setCurrentIndex(0)
        self.tab_widget.setCurrentWidget(self.history_tab)
        self.query_history_runs(auto_select_latest=False)
        
    def create_statistics_panel(self, parent_layout):
        """Create the statistics panel below the progress bar."""
        # Group box to contain all statistics
        self.stats_group = QGroupBox("执行统计信息")
        self.stats_layout = QGridLayout()
        
        # Create all stat labels
        self.scheme_label = QLabel("方案名称:")
        self.scheme_value = QLabel("未命名方案")
        self.scheme_value.setStyleSheet("font-weight: bold;")
        
        self.total_label = QLabel("脚本总数:")
        self.total_value = QLabel("0")
        
        self.current_label = QLabel("当前执行:")
        self.current_value = QLabel("0 / 0")
        
        self.pending_exec_label = QLabel("待执行数:")
        self.pending_exec_value = QLabel("0")
        
        self.current_time_label = QLabel("当前时间:")
        self.current_time_value = QLabel("--:--:--")
        
        self.start_time_label = QLabel("开始时间:")
        self.start_time_value = QLabel("未开始")
        
        self.elapsed_time_label = QLabel("已运行时间:")
        self.elapsed_time_value = QLabel("00:00:00")
        
        # 测试结果统计标签
        self.pass_label = QLabel("合格数:")
        self.pass_value = QLabel("0")
        self.pass_value.setStyleSheet("color: green;")
        
        self.fail_label = QLabel("不合格数:")
        self.fail_value = QLabel("0")
        self.fail_value.setStyleSheet("color: red;")
        
        self.pending_label = QLabel("待判定数:")
        self.pending_value = QLabel("0")
        self.pending_value.setStyleSheet("color: orange;")
        
        # 调整对齐方式，使标签左对齐，值标签左对齐
        for label in [self.scheme_label, self.total_label, self.current_label,
                     self.pending_exec_label, self.current_time_label, self.start_time_label,
                     self.elapsed_time_label, self.pass_label, self.fail_label, self.pending_label]:
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            label.setFixedWidth(80)  # 设置标签固定宽度

        for value in [self.scheme_value, self.total_value, self.current_value,
                     self.pending_exec_value, self.current_time_value, self.start_time_value,
                     self.elapsed_time_value, self.pass_value, self.fail_value, self.pending_value]:
            value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            value.setMinimumWidth(150)  # 设置值标签最小宽度
        
        # 布局：方案名称独占一行，然后是3列结构
        self.stats_layout.addWidget(self.scheme_label, 0, 0)
        self.stats_layout.addWidget(self.scheme_value, 0, 1, 1, 2)  # 跨2列
        
        # 第一列：脚本总数、待执行数、当前执行
        self.stats_layout.addWidget(self.total_label, 1, 0)
        self.stats_layout.addWidget(self.total_value, 1, 1)
        
        self.stats_layout.addWidget(self.pending_exec_label, 2, 0)
        self.stats_layout.addWidget(self.pending_exec_value, 2, 1)
        
        self.stats_layout.addWidget(self.current_label, 3, 0)
        self.stats_layout.addWidget(self.current_value, 3, 1)
        
        # 第二列：当前时间、开始时间、已运行时间
        self.stats_layout.addWidget(self.current_time_label, 1, 2)
        self.stats_layout.addWidget(self.current_time_value, 1, 3)
        
        self.stats_layout.addWidget(self.start_time_label, 2, 2)
        self.stats_layout.addWidget(self.start_time_value, 2, 3)
        
        self.stats_layout.addWidget(self.elapsed_time_label, 3, 2)
        self.stats_layout.addWidget(self.elapsed_time_value, 3, 3)
        
        # 第三列：合格数、不合格数、待判定数
        self.stats_layout.addWidget(self.pass_label, 1, 4)
        self.stats_layout.addWidget(self.pass_value, 1, 5)
        
        self.stats_layout.addWidget(self.fail_label, 2, 4)
        self.stats_layout.addWidget(self.fail_value, 2, 5)
        
        self.stats_layout.addWidget(self.pending_label, 3, 4)
        self.stats_layout.addWidget(self.pending_value, 3, 5)
        
        # 设置列之间的间距
        self.stats_layout.setHorizontalSpacing(5)
        self.stats_layout.setVerticalSpacing(5)

        self.stats_group.setLayout(self.stats_layout)
        parent_layout.addWidget(self.stats_group)
        
        # Timer to update current time
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_current_time)
        self.time_timer.start(1000)  # Update every second
        self.update_current_time()
        
        # 初始化测试结果统计数据
        self.update_test_result_stats()
        # 初始化待执行数
        self.update_pending_exec_count()

    def update_test_result_stats(self):
        """Update the test result statistics."""
        pass_count = 0
        fail_count = 0
        pending_count = 0
        
        for result in self.test_results:
            if "不合格" in result["result"]:
                fail_count += 1
            elif "合格" in result["result"]:
                pass_count += 1
            else:
                pending_count += 1
        
        self.pass_value.setText(str(pass_count))
        self.fail_value.setText(str(fail_count))
        self.pending_value.setText(str(pending_count))
        
    def update_pending_exec_count(self):
        """Update the pending execution count."""
        try:
            total = int(self.total_value.text())
            current = int(self.current_value.text().split('/')[0])
            pending = total - current
            self.pending_exec_value.setText(str(pending))
        except:
            self.pending_exec_value.setText("0")
    
    # 新增：清除控制台输出
    def clear_console_output(self):
        self.console_output.clear()
        # 重置搜索状态
        self.search_position = 0
        self.search_input.clear()

    # 新增：保存控制台输出到文件
    def save_console_output(self):
        # 获取Path3配置值（控制台输出日志目录）
        path3 = self.config.get("Paths", "Path3", fallback="")
        
        # 如果配置为空，使用用户主目录
        if not path3 or not os.path.exists(path3):
            path3 = os.path.expanduser("~")
        
        # 构建默认文件名
        default_filename = f"console_log_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
        default_path = os.path.join(path3, default_filename)
        
        # 获取用户选择的保存路径
        file_name, _ = QFileDialog.getSaveFileName(
            self, 
            "保存控制台日志", 
            default_path,
            "文本文件 (*.txt);;所有文件 (*)"
        )
        
        # 如果用户取消了操作
        if not file_name:
            return
            
        try:
            # 确保文件所在目录存在
            output_dir = os.path.dirname(file_name)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # 保存控制台内容
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(self.console_output.toPlainText())
                
            QMessageBox.information(self, "保存成功", f"控制台日志已成功保存到:\n{file_name}")
            
            # 打开保存目录
            if os.path.exists(output_dir):
                if sys.platform == 'win32':
                    os.startfile(output_dir)
                else:
                    # 对于非Windows系统，可以使用xdg-open或open命令
                    subprocess.Popen(['xdg-open', output_dir])
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存控制台日志时发生错误:\n{str(e)}")

    # 初始化搜索位置（在现有__init__方法中添加）
    # 注意：不需要添加新的__init__方法，只需在现有方法中添加一行代码
    # 搜索控制台输出
    def search_console_output(self):
        search_text = self.search_input.text()
        if not search_text:
            QMessageBox.information(self, "提示", "请输入搜索内容")
            return

        # 获取控制台文本
        text = self.console_output.toPlainText()
        if not text:
            return

        # 从当前位置开始搜索
        position = text.find(search_text, self.search_position)
        
        if position == -1:
            # 没有找到，从头开始搜索
            position = text.find(search_text, 0)
            if position == -1:
                QMessageBox.information(self, "搜索结果", f"未找到 '{search_text}'")
                self.search_position = 0
                return
            else:
                QMessageBox.information(self, "搜索结果", f"已回到开始位置，找到 '{search_text}'")

        # 高亮显示搜索结果
        cursor = self.console_output.textCursor()
        cursor.setPosition(position)
        cursor.movePosition(cursor.Right, cursor.KeepAnchor, len(search_text))
        self.console_output.setTextCursor(cursor)
        self.console_output.ensureCursorVisible()

        # 更新下一次搜索的起始位置
        self.search_position = position + len(search_text)
        
        # 如果已经搜索到文本末尾，重置搜索位置
        if self.search_position >= len(text):
            self.search_position = 0

    # 搜索控制台输出
    def search_console_output(self):
        search_text = self.search_input.text()
        if not search_text:
            QMessageBox.information(self, "提示", "请输入搜索内容")
            return

        # 获取控制台文本
        text = self.console_output.toPlainText()
        if not text:
            return

        # 从当前位置开始搜索
        position = text.find(search_text, self.search_position)
        
        if position == -1:
            # 没有找到，从头开始搜索
            position = text.find(search_text, 0)
            if position == -1:
                QMessageBox.information(self, "搜索结果", f"未找到 '{search_text}'")
                self.search_position = 0
                return
            else:
                QMessageBox.information(self, "搜索结果", f"已回到开始位置，找到 '{search_text}'")

        # 高亮显示搜索结果
        cursor = self.console_output.textCursor()
        cursor.setPosition(position)
        cursor.movePosition(cursor.Right, cursor.KeepAnchor, len(search_text))
        self.console_output.setTextCursor(cursor)
        self.console_output.ensureCursorVisible()

        # 更新下一次搜索的起始位置
        self.search_position = position + len(search_text)
        
        # 如果已经搜索到文本末尾，重置搜索位置
        if self.search_position >= len(text):
            self.search_position = 0
    
    def add_console_output(self, output):
        """添加控制台输出（优化性能版本）"""
        # 跳过空行输出
        if not output.strip():
            return
        
        # 启用高效追加模式
        cursor = self.console_output.textCursor()
        cursor.movePosition(cursor.End)
        
        # 追加文本
        cursor.insertText(output + "\n")
        
        # 自动滚动到底部
        self.console_output.setTextCursor(cursor)
        self.console_output.ensureCursorVisible()
        
        # 限制控制台输出长度（防止内存占用过大）
        if self.console_output.document().lineCount() > 1000:
            cursor.setPosition(0)
            cursor.select(cursor.LineUnderCursor)
            cursor.removeSelectedText()


    # 修复钉住窗口按钮问题
    def toggle_pin_on_top(self, checked):
        """切换窗口置顶状态"""
        # 创建新的Action避免改变现有布局
        if checked:
            # 创建新窗口标志
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            
            # 更新图标和提示文本
            icon_path_pinned = resource_path("pinned.png")
            if os.path.exists(icon_path_pinned):
                self.pin_action.setIcon(QIcon(icon_path_pinned))
            self.pin_action.setToolTip("取消窗口置顶")
        else:
            # 移除置顶标志
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            
            # 更新图标和提示文本
            icon_path_pin = resource_path("pin.png")
            if os.path.exists(icon_path_pin):
                self.pin_action.setIcon(QIcon(icon_path_pin))
            self.pin_action.setToolTip("将窗口钉在最上层")
        
        # 不改变按钮文本，避免布局问题
        self.show()  # 重新显示窗口使设置生效

    def toggle_breakpoint(self):
        """Toggle breakpoint on the current selected row."""
        row = self.file_list.currentRow()
        info = self.get_script_info_from_row(row)
        if not info:
            QMessageBox.information(self, "断点设置", "请选择一个脚本项以设置断点")
            return

        path = info.get("path")
        item = self.file_list.item(row)

        if path in self.breakpoint_paths:
            self.breakpoint_paths.remove(path)
            if item:
                item.setBackground(QBrush())
            action = "清除"
        else:
            self.breakpoint_paths.add(path)
            if item:
                item.setBackground(QColor(255, 220, 220))
            action = "设置"

        self.refresh_file_list(preserve_path=path)

        QMessageBox.information(self, "断点设置", f"脚本 {os.path.basename(path)} 断点已{action}")

    def on_file_list_item_double_clicked(self, item):
        """Handle double-clicks on the script list, supporting group toggling."""
        if not item:
            return
        data = item.data(Qt.UserRole) or {}
        if data.get("type") == "group":
            self.toggle_group_collapse(data.get("group_id"))
            return
        if data.get("type") == "script":
            self.file_list.setCurrentItem(item)
            self.run_single_file()

    def run_single_file(self):
        """Run the currently selected file."""
        script_info = self.get_script_info_from_row(self.file_list.currentRow())
        if not script_info:
            QMessageBox.warning(self, "未选择脚本", "请先选择一个脚本文件")
            return

        if self.is_running:
            QMessageBox.warning(self, "任务执行中", "请先停止当前任务或等待任务完成")
            return
        target_path = script_info.get("path")
        scheme_label = f"单文件执行:{os.path.basename(target_path)}"
        self.prepare_run_context(1, scheme_label)

        self.start_time = datetime.now()
        self.elapsed_time = timedelta(0)

        # Update start time display
        self.start_time_value.setText(self.start_time.strftime("%Y-%m-%d %H:%M:%S"))

        # Create and start the execution thread for single file
        self.execution_thread = FileExecutionThread([target_path], scheme_label, set())
        self.execution_thread.progress_signal.connect(self.progress_bar.setValue)
        self.execution_thread.executed_signal.connect(self.add_executed_file)
        self.execution_thread.error_signal.connect(self.show_error_message)
        self.execution_thread.finished.connect(self.execution_complete)
        self.execution_thread.console_output_signal.connect(self.add_console_output)  # 连接控制台输出信号
        self.execution_thread.test_result_signal.connect(self.add_test_result)  # 连接测试结果信号
        self.execution_thread.current_index_signal.connect(self.update_current_index)
        self.execution_thread.script_console_signal.connect(self.capture_script_console)
        
        # Update UI
        self.is_running = True
        self.is_paused = False
        self.update_button_states()
        self.progress_bar.setValue(0)
        self.console_output.clear()  # 清除之前的控制台输出
        
        # Run single file
        self.execution_thread.start()
        self.elapsed_timer.start(1000)

    def add_executed_file(self, file_info):
        """Record executed file information."""
        self.executed_count += 1

    def pause_execution(self):
        """Pause the current execution after current file completes."""
        if not self.is_running:
            QMessageBox.information(self, "信息", "当前没有运行中的任务")
            return
            
        if self.execution_thread:
            self.execution_thread.pause()
            self.is_paused = True
            self.update_button_states()

    def resume_execution(self):
        """Resume the paused execution."""
        if not self.is_paused:
            QMessageBox.information(self, "信息", "当前任务没有暂停")
            return
            
        if self.execution_thread:
            self.execution_thread.resume()
            self.is_paused = False
            self.update_button_states()

    def stop_execution(self):
        """Stop the current execution after completing the current file."""
        if not self.is_running:
            QMessageBox.information(self, "信息", "当前没有运行中的任务")
            return
            
        if self.execution_thread:
            self.execution_thread.stop()
            self.update_button_states()

    def update_button_states(self):
        """Update the state of action buttons based on current execution status."""
        is_running = self.is_running
        is_paused = self.is_paused
        
        # Set button states
        self.run_action.setEnabled(not is_running)
        self.run_single_action.setEnabled(not is_running)
        self.breakpoint_action.setEnabled(not is_running)
        self.pause_action.setEnabled(is_running and not is_paused)
        self.resume_action.setEnabled(is_running and is_paused)
        self.stop_action.setEnabled(is_running)

    def update_current_time(self):
        """Update the current time display."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.current_time_value.setText(current_time)

    def update_elapsed_time(self):
        """Update the elapsed time display."""
        if self.start_time:
            self.elapsed_time = datetime.now() - self.start_time
            hours, remainder = divmod(self.elapsed_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.elapsed_time_value.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        
    def init_config(self):
        """Initialize the configuration file if it doesn't exist."""
        self.config = configparser.ConfigParser()
        
        # 确保使用跨平台的配置路径
        if sys.platform == "win32":
            config_dir = os.path.join(os.getenv('APPDATA'), 'PythonTestSequencer')
        else:
            config_dir = os.path.join(os.path.expanduser('~'), '.config', 'PythonTestSequencer')

        self.config_dir = config_dir
        
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        
        self.config_file = os.path.join(config_dir, 'Configure.ini')
        
        # 如果配置文件已存在，则加载它
        if os.path.exists(self.config_file):
            self.safe_read_config()
        else:
            # 创建默认配置
            docs_path = os.path.join(os.path.expanduser("~"), "Documents")
            self.config["Paths"] = {
                "Path1": docs_path,
                "Path2": docs_path,
                "Path3": docs_path,
                "Path4": docs_path
            }
            self.save_config()
        
        # 确保配置文件内容正确
        if not self.config.has_section("Paths"):
            self.config.add_section("Paths")
            self.config.set("Paths", "Path1", os.path.join(os.path.expanduser("~"), "Documents"))
            self.config.set("Paths", "Path2", os.path.join(os.path.expanduser("~"), "Documents"))
            self.config.set("Paths", "Path3", os.path.join(os.path.expanduser("~"), "Documents"))
            self.config.set("Paths", "Path4", os.path.join(os.path.expanduser("~"), "Documents"))
            self.save_config()
        
        # 确保Path4存在
        if not self.config.has_option("Paths", "Path4"):
            self.config.set("Paths", "Path4", os.path.join(os.path.expanduser("~"), "Documents"))
            self.save_config()

    def save_config(self):
        """保存配置到文件"""
        with open(self.config_file, 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def init_database(self):
        """初始化结果数据库"""
        try:
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS runs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        scheme_name TEXT,
                        run_identifier TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        total_scripts INTEGER,
                        executed_count INTEGER,
                        pass_count INTEGER,
                        fail_count INTEGER,
                        pending_count INTEGER,
                        duration_seconds REAL,
                        config_json TEXT,
                        stats_json TEXT
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS run_scripts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        run_id INTEGER NOT NULL,
                        sequence INTEGER,
                        file_name TEXT,
                        execution_timestamp TEXT,
                        duration_seconds REAL,
                        result TEXT,
                        console_output TEXT,
                        FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE
                    )
                    """
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_run_scripts_run ON run_scripts(run_id, sequence)"
                )
                conn.commit()
        except Exception as e:
            print(f"数据库初始化失败: {e}")

    def initialize_history_view(self):
        """初始化历史记录面板"""
        if not hasattr(self, "history_start_date"):
            return
        self.history_start_date.setDate(QDate.currentDate().addDays(-7))
        self.history_end_date.setDate(QDate.currentDate())
        self.populate_history_scheme_options()
        self.history_scheme_combo.setCurrentIndex(0)
        self.query_history_runs(auto_select_latest=True)

    def populate_history_scheme_options(self):
        if not hasattr(self, "history_scheme_combo"):
            return

        current_data = self.history_scheme_combo.currentData() if self.history_scheme_combo.count() else None
        self.history_scheme_combo.blockSignals(True)
        self.history_scheme_combo.clear()
        self.history_scheme_combo.addItem("全部方案", None)

        seen = set()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT run_identifier FROM runs ORDER BY start_time DESC")
                for row in cursor.fetchall():
                    identifier = row[0] or "未命名方案"
                    if identifier in seen:
                        continue
                    seen.add(identifier)
                    self.history_scheme_combo.addItem(identifier, identifier)
        except Exception as e:
            print(f"加载历史方案失败: {e}")

        target_index = 0
        if current_data:
            idx = self.history_scheme_combo.findData(current_data)
            if idx >= 0:
                target_index = idx
        self.history_scheme_combo.setCurrentIndex(target_index)
        self.history_scheme_combo.blockSignals(False)

    def reset_history_filters(self, checked=False, apply_query=False):
        if not hasattr(self, "history_start_date"):
            return
        self.history_start_date.setDate(QDate.currentDate().addDays(-7))
        self.history_end_date.setDate(QDate.currentDate())
        self.populate_history_scheme_options()
        self.history_scheme_combo.setCurrentIndex(0)
        if apply_query:
            self.query_history_runs(auto_select_latest=True)
        else:
            if hasattr(self, "history_runs_table"):
                self.history_runs_table.clearSelection()
                self.history_runs_table.setRowCount(0)
            if hasattr(self, "history_scripts_table"):
                self.history_scripts_table.clearSelection()
                self.history_scripts_table.setRowCount(0)
            if hasattr(self, "history_console_text"):
                self.history_console_text.setPlainText("")
            if hasattr(self, "history_config_text"):
                self.history_config_text.setPlainText("")
            if hasattr(self, "history_summary_label"):
                self.history_summary_label.setText("")
            self.history_selected_run_id = None

    def refresh_history_view(self, auto_select_latest=False):
        if not hasattr(self, "history_scheme_combo"):
            return
        current_scheme = self.history_scheme_combo.currentData()
        self.populate_history_scheme_options()
        if current_scheme is not None:
            idx = self.history_scheme_combo.findData(current_scheme)
            if idx >= 0:
                self.history_scheme_combo.setCurrentIndex(idx)
        self.query_history_runs(auto_select_latest=auto_select_latest)

    def query_history_runs(self, checked=False, auto_select_latest=False):
        if not hasattr(self, "history_runs_table"):
            return

        start_date = self.history_start_date.date()
        end_date = self.history_end_date.date()
        if start_date > end_date:
            start_date, end_date = end_date, start_date
            self.history_start_date.setDate(start_date)
            self.history_end_date.setDate(end_date)

        start_text = f"{start_date.toString('yyyy-MM-dd')} 00:00:00"
        end_text = f"{end_date.toString('yyyy-MM-dd')} 23:59:59"
        scheme_filter = self.history_scheme_combo.currentData()

        query = (
            """
            SELECT id, scheme_name, run_identifier, start_time, end_time,
                   total_scripts, executed_count, pass_count, fail_count,
                   pending_count, duration_seconds, config_json, stats_json
            FROM runs
            WHERE datetime(start_time) BETWEEN datetime(?) AND datetime(?)
            """
        )
        params = [start_text, end_text]
        if scheme_filter:
            query += " AND run_identifier = ?"
            params.append(scheme_filter)
        query += " ORDER BY datetime(start_time) DESC"

        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
        except Exception as e:
            print(f"查询历史记录失败: {e}")
            rows = []
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

        self.history_run_records = [dict(row) for row in rows]
        self.history_runs_table.setRowCount(len(self.history_run_records))

        previous_selection = self.history_selected_run_id
        target_run_id = None

        for row_idx, record in enumerate(self.history_run_records):
            display_name = record.get("run_identifier") or record.get("scheme_name") or "未命名方案"
            start_time = record.get("start_time") or "-"
            end_time = record.get("end_time") or "-"
            pass_count = record.get("pass_count") or 0
            fail_count = record.get("fail_count") or 0
            pending_count = record.get("pending_count") or 0
            duration = record.get("duration_seconds") or 0.0

            id_item = QTableWidgetItem(str(record.get("id")))
            id_item.setData(Qt.UserRole, record.get("id"))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.history_runs_table.setItem(row_idx, 0, id_item)

            name_item = QTableWidgetItem(display_name)
            self.history_runs_table.setItem(row_idx, 1, name_item)

            start_item = QTableWidgetItem(start_time)
            start_item.setTextAlignment(Qt.AlignCenter)
            self.history_runs_table.setItem(row_idx, 2, start_item)

            end_item = QTableWidgetItem(end_time)
            end_item.setTextAlignment(Qt.AlignCenter)
            self.history_runs_table.setItem(row_idx, 3, end_item)

            pass_item = QTableWidgetItem(str(pass_count))
            pass_item.setTextAlignment(Qt.AlignCenter)
            self.history_runs_table.setItem(row_idx, 4, pass_item)

            fail_item = QTableWidgetItem(str(fail_count))
            fail_item.setTextAlignment(Qt.AlignCenter)
            self.history_runs_table.setItem(row_idx, 5, fail_item)

            pending_item = QTableWidgetItem(str(pending_count))
            pending_item.setTextAlignment(Qt.AlignCenter)
            self.history_runs_table.setItem(row_idx, 6, pending_item)

            duration_item = QTableWidgetItem(f"{duration:.1f}")
            duration_item.setTextAlignment(Qt.AlignCenter)
            self.history_runs_table.setItem(row_idx, 7, duration_item)

            if record.get("id") == previous_selection:
                target_run_id = previous_selection

        if target_run_id is None and auto_select_latest and self.history_run_records:
            target_run_id = self.history_run_records[0].get("id")

        if target_run_id:
            for row_idx, record in enumerate(self.history_run_records):
                if record.get("id") == target_run_id:
                    self.history_runs_table.selectRow(row_idx)
                    break
        else:
            self.history_runs_table.clearSelection()
            self.history_scripts_table.setRowCount(0)
            self.history_console_text.setPlainText("请选择脚本查看控制台输出")
            self.history_config_text.setPlainText("请选择运行记录查看配置")
            self.history_summary_label.setText("请选择运行记录查看详情")
            self.history_selected_run_id = None

    def on_history_run_selected(self):
        if not hasattr(self, "history_runs_table"):
            return
        current_row = self.history_runs_table.currentRow()
        if current_row < 0:
            self.history_selected_run_id = None
            self.history_scripts_table.setRowCount(0)
            self.history_console_text.setPlainText("请选择脚本查看控制台输出")
            self.history_config_text.setPlainText("请选择运行记录查看配置")
            self.history_summary_label.setText("请选择运行记录查看详情")
            return

        id_item = self.history_runs_table.item(current_row, 0)
        if id_item is None:
            return
        run_id = id_item.data(Qt.UserRole)
        self.history_selected_run_id = run_id
        record = next((rec for rec in self.history_run_records if rec.get("id") == run_id), None)
        if record:
            self.update_history_summary(record)
            self.load_history_scripts(run_id)
            if hasattr(self, "history_detail_tabs"):
                self.history_detail_tabs.setCurrentIndex(0)

    def update_history_summary(self, record):
        if not hasattr(self, "history_summary_label"):
            return
        display_name = record.get("run_identifier") or record.get("scheme_name") or "未命名方案"
        total_scripts = record.get("total_scripts") or 0
        executed = record.get("executed_count") or 0
        pass_count = record.get("pass_count") or 0
        fail_count = record.get("fail_count") or 0
        pending_count = record.get("pending_count") or 0
        duration = record.get("duration_seconds") or 0.0
        start_time = record.get("start_time") or "-"
        end_time = record.get("end_time") or "-"

        summary_text = (
            f"<b>方案:</b> {display_name}&nbsp;&nbsp;"
            f"<b>开始:</b> {start_time}&nbsp;&nbsp;<b>结束:</b> {end_time}<br>"
            f"<b>执行:</b> {executed}/{total_scripts}&nbsp;&nbsp;"
            f"<b>合格:</b> {pass_count}&nbsp;&nbsp;<b>不合格:</b> {fail_count}&nbsp;&nbsp;<b>待判定:</b> {pending_count}&nbsp;&nbsp;"
            f"<b>耗时:</b> {duration:.1f} s"
        )
        self.history_summary_label.setText(summary_text)

        config_text = record.get("config_json") or ""
        if config_text:
            try:
                parsed = json.loads(config_text)
                pretty = json.dumps(parsed, ensure_ascii=False, indent=2)
            except Exception:
                pretty = config_text
            self.history_config_text.setPlainText(pretty)
        else:
            self.history_config_text.setPlainText("无配置快照记录")

    def load_history_scripts(self, run_id):
        if not hasattr(self, "history_scripts_table"):
            return
        scripts = self.history_script_cache.get(run_id)
        if scripts is None:
            conn = None
            try:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """
                    SELECT sequence, file_name, execution_timestamp, duration_seconds, result, console_output
                    FROM run_scripts
                    WHERE run_id = ?
                    ORDER BY sequence
                    """,
                    (run_id,),
                ).fetchall()
                scripts = [dict(row) for row in rows]
            except Exception as e:
                print(f"加载运行脚本失败: {e}")
                scripts = []
            finally:
                if conn is not None:
                    try:
                        conn.close()
                    except Exception:
                        pass
            self.history_script_cache[run_id] = scripts

        self.history_scripts_table.setRowCount(len(scripts))
        self.history_console_text.setPlainText("请选择脚本查看控制台输出")
        if not scripts:
            self.history_console_text.setPlainText("该运行没有脚本记录")
            return

        for row_idx, script in enumerate(scripts):
            sequence = script.get("sequence") or 0
            seq_item = QTableWidgetItem(str(sequence))
            seq_item.setData(Qt.UserRole, script)
            seq_item.setTextAlignment(Qt.AlignCenter)
            self.history_scripts_table.setItem(row_idx, 0, seq_item)

            name_item = QTableWidgetItem(script.get("file_name") or "-")
            self.history_scripts_table.setItem(row_idx, 1, name_item)

            exec_time = script.get("execution_timestamp") or "-"
            exec_item = QTableWidgetItem(exec_time)
            exec_item.setTextAlignment(Qt.AlignCenter)
            self.history_scripts_table.setItem(row_idx, 2, exec_item)

            duration_seconds = script.get("duration_seconds")
            if duration_seconds is None:
                duration_text = "-"
            else:
                duration_text = f"{duration_seconds:.2f}s"
            duration_item = QTableWidgetItem(duration_text)
            duration_item.setTextAlignment(Qt.AlignCenter)
            self.history_scripts_table.setItem(row_idx, 3, duration_item)

            result_text = script.get("result") or "待判定"
            result_item = QTableWidgetItem(result_text)
            result_item.setTextAlignment(Qt.AlignCenter)
            if "不合格" in result_text:
                result_item.setForeground(QBrush(QColor(220, 0, 0)))
            elif "合格" in result_text:
                result_item.setForeground(QBrush(QColor(0, 200, 0)))
            else:
                result_item.setForeground(QBrush(QColor(150, 150, 150)))
            self.history_scripts_table.setItem(row_idx, 4, result_item)

        self.history_scripts_table.selectRow(0)

    def on_history_script_selected(self):
        if not hasattr(self, "history_scripts_table"):
            return
        current_row = self.history_scripts_table.currentRow()
        if current_row < 0:
            self.history_console_text.setPlainText("请选择脚本查看控制台输出")
            return
        seq_item = self.history_scripts_table.item(current_row, 0)
        if seq_item is None:
            return
        script = seq_item.data(Qt.UserRole) or {}
        console_output = script.get("console_output") or ""
        if console_output:
            self.history_console_text.setPlainText(console_output)
        else:
            self.history_console_text.setPlainText("该脚本没有控制台输出记录")
        self.history_detail_tabs.setCurrentIndex(0)
        cursor = self.history_console_text.textCursor()
        cursor.movePosition(cursor.Start)
        self.history_console_text.setTextCursor(cursor)
        self.history_console_text.ensureCursorVisible()
        scroll_bar = self.history_console_text.verticalScrollBar()
        if scroll_bar is not None:
            scroll_bar.setValue(scroll_bar.minimum())

    def center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        screen_geometry = screen.availableGeometry()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(screen_geometry.center())
        self.move(frame_geometry.topLeft())

    def show_configure(self):
        """Show a dialog to edit Path1, Path2, Path3 and Path4 together."""
        # 确保配置已加载
        self.safe_read_config()
            
        # 获取当前配置值
        path1 = self.config.get("Paths", "Path1", fallback="")
        path2 = self.config.get("Paths", "Path2", fallback="")
        path3 = self.config.get("Paths", "Path3", fallback="")
        path4 = self.config.get("Paths", "Path4", fallback="")

        # 创建配置对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("配置路径")
        dialog.setMinimumWidth(500)  # 设置对话框最小宽度
        layout = QVBoxLayout(dialog)

        # 创建分组框
        path_group = QGroupBox("路径配置")
        path_layout = QFormLayout()
        path_group.setLayout(path_layout)

        # Path1 input
        path1_label = QLabel("路径1 (Python文件目录):")
        self.path1_input = QLineEdit(path1)
        path1_button = QPushButton("浏览...")
        path1_button.clicked.connect(lambda: self.browse_path(self.path1_input))
        path1_layout = QHBoxLayout()
        path1_layout.addWidget(self.path1_input)
        path1_layout.addWidget(path1_button)
        path_layout.addRow(path1_label, path1_layout)

        # Path2 input
        path2_label = QLabel("路径2 (方案存储目录):")
        self.path2_input = QLineEdit(path2)
        path2_button = QPushButton("浏览...")
        path2_button.clicked.connect(lambda: self.browse_path(self.path2_input))
        path2_layout = QHBoxLayout()
        path2_layout.addWidget(self.path2_input)
        path2_layout.addWidget(path2_button)
        path_layout.addRow(path2_label, path2_layout)

        # Path3 input
        path3_label = QLabel("路径3 (控制台输出日志):")
        self.path3_input = QLineEdit(path3)
        path3_button = QPushButton("浏览...")
        path3_button.clicked.connect(lambda: self.browse_path(self.path3_input))
        path3_layout = QHBoxLayout()
        path3_layout.addWidget(self.path3_input)
        path3_layout.addWidget(path3_button)
        path_layout.addRow(path3_label, path3_layout)

        # Path4 input
        path4_label = QLabel("路径4 (日志输出目录):")
        self.path4_input = QLineEdit(path4)
        path4_button = QPushButton("浏览...")
        path4_button.clicked.connect(lambda: self.browse_path(self.path4_input))
        path4_layout = QHBoxLayout()
        path4_layout.addWidget(self.path4_input)
        path4_layout.addWidget(path4_button)
        path_layout.addRow(path4_label, path4_layout)

        layout.addWidget(path_group)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 添加测试按钮
        test_button = QPushButton("测试路径")
        test_button.clicked.connect(self.test_paths)
        button_layout.addWidget(test_button)

        # Save and cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.save_paths(dialog))
        button_box.rejected.connect(dialog.reject)
        button_layout.addWidget(button_box)

        layout.addLayout(button_layout)

        dialog.setLayout(layout)
        dialog.exec_()

    def safe_read_config(self):
        """安全读取配置文件，处理不同编码"""
        try:
            # 尝试UTF-8编码
            self.config.read(self.config_file, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                # 尝试GBK编码
                self.config.read(self.config_file, encoding='gbk')
            except:
                # 创建默认配置
                docs_path = os.path.join(os.path.expanduser("~"), "Documents")
                self.config["Paths"] = {
                    "Path1": docs_path,
                    "Path2": docs_path,
                    "Path3": docs_path
                }
                self.save_config()

    def browse_path(self, input_widget):
        """打开路径选择对话框"""
        # 获取初始路径
        init_path = input_widget.text() or os.path.expanduser("~")
        
        path = QFileDialog.getExistingDirectory(self, "选择目录", init_path)
        if path:
            input_widget.setText(path)
            
    def test_paths(self):
        """测试配置的路径是否有效"""
        results = []
        
        # 测试路径1
        path1 = self.path1_input.text()
        if os.path.exists(path1):
            results.append(f"✅ 路径1有效: {path1}")
        else:
            results.append(f"❌ 路径1无效或不存在: {path1}")
        
        # 测试路径2
        path2 = self.path2_input.text()
        if os.path.exists(path2):
            results.append(f"✅ 路径2有效: {path2}")
        else:
            results.append(f"❌ 路径2无效或不存在: {path2}")
        
        # 测试路径3
        path3 = self.path3_input.text()
        if os.path.exists(path3):
            results.append(f"✅ 路径3有效: {path3}")
        else:
            results.append(f"❌ 路径3无效或不存在: {path3}")
        
        # 测试路径4
        path4 = self.path4_input.text()
        if os.path.exists(path4):
            results.append(f"✅ 路径4有效: {path4}")
        else:
            results.append(f"❌ 路径4无效或不存在: {path4}")
        
        # 显示测试结果
        QMessageBox.information(self, "路径测试结果", "\n".join(results))

    def save_paths(self, dialog):
        """保存配置路径"""
        # 确保Paths部分存在
        if not self.config.has_section("Paths"):
            self.config.add_section("Paths")
        
        # 更新配置
        self.config.set("Paths", "Path1", self.path1_input.text())
        self.config.set("Paths", "Path2", self.path2_input.text())
        self.config.set("Paths", "Path3", self.path3_input.text())
        self.config.set("Paths", "Path4", self.path4_input.text())
        
        # 保存配置
        self.save_config()
        QMessageBox.information(self, "配置已更新", "路径设置已保存!\n下次启动软件时将自动加载这些路径")
        dialog.accept()

    def has_groups(self):
        """Return True when the UI is operating with grouped scripts."""
        return len(self.groups) > 0

    def get_group_by_id(self, group_id):
        """Find group by its persistent id."""
        if not group_id:
            return None
        for group in self.groups:
            if group.get("id") == group_id:
                return group
        return None

    def get_group_position(self, group_id):
        """Return index of group id within the groups list."""
        for index, group in enumerate(self.groups):
            if group.get("id") == group_id:
                return index
        return -1

    def ensure_unique_group_name(self, base_name):
        """Ensure the group name is unique across current groups."""
        if not base_name:
            base_name = "新建组"
        existing = {group.get("name", "") for group in self.groups}
        if base_name not in existing:
            return base_name
        counter = 2
        candidate = f"{base_name} ({counter})"
        while candidate in existing:
            counter += 1
            candidate = f"{base_name} ({counter})"
        return candidate

    def ensure_group_mode(self):
        """Convert legacy flat list into a default group when needed."""
        if self.has_groups() or not self.file_paths:
            return
        default_group = {
            "id": str(uuid4()),
            "name": "未分组脚本",
            "files": list(self.file_paths),
            "collapsed": False,
        }
        self.groups.append(default_group)

    def toggle_group_collapse(self, group_id):
        """Toggle collapsed/expanded state for a group header."""
        group = self.get_group_by_id(group_id)
        if not group:
            return
        group["collapsed"] = not group.get("collapsed", False)
        self.refresh_file_list(preserve_group_id=group_id)

    def rebuild_flat_structure(self):
        """Update the flattened script cache and file_paths list."""
        self.flat_script_map = []
        if self.has_groups():
            for group_index, group in enumerate(self.groups):
                files = group.get("files", [])
                for script_index, path in enumerate(files):
                    self.flat_script_map.append({
                        "path": path,
                        "group_id": group.get("id"),
                        "group_name": group.get("name"),
                        "group_index": group_index,
                        "script_index": script_index,
                    })
        else:
            for script_index, path in enumerate(self.file_paths):
                self.flat_script_map.append({
                    "path": path,
                    "group_id": None,
                    "group_name": None,
                    "group_index": None,
                    "script_index": script_index,
                })
        self.file_paths = [entry["path"] for entry in self.flat_script_map]

    def get_current_selected_path(self):
        """Return the script path for current selection if any."""
        info = self.get_script_info_from_row(self.file_list.currentRow())
        return info.get("path") if info else None

    def refresh_file_list(self, preserve_path=None, preserve_group_id=None):
        """Rebuild the QListWidget based on current groups/files."""
        if preserve_path is None and preserve_group_id is None:
            current = self.file_list.currentItem()
            if current:
                data = current.data(Qt.UserRole) or {}
                if data.get("type") == "script":
                    preserve_path = data.get("path")
                elif data.get("type") == "group":
                    preserve_group_id = data.get("group_id")

        self.rebuild_flat_structure()

        self.file_list.clear()

        if self.has_groups():
            for group_index, group in enumerate(self.groups):
                files_in_group = group.get("files", [])
                collapsed = bool(group.get("collapsed", False))
                indicator = "[+]" if collapsed else "[-]"
                header_text = f"[组] {indicator} {group.get('name', '')} ({len(files_in_group)})"
                header = QListWidgetItem(header_text)
                header.setFlags(Qt.ItemIsEnabled)
                header.setBackground(QColor(240, 240, 240))
                header.setSizeHint(QSize(header.sizeHint().width(), 28))
                header.setData(Qt.UserRole, {
                    "type": "group",
                    "group_id": group.get("id"),
                    "group_index": group_index,
                    "name": group.get("name", ""),
                    "collapsed": collapsed,
                })
                self.file_list.addItem(header)

                if not collapsed:
                    for script_index, path in enumerate(files_in_group):
                        display_name = os.path.basename(path) or path
                        is_last = script_index == len(files_in_group) - 1
                        branch = "└─" if is_last else "├─"
                        item = QListWidgetItem(f"   {branch} {display_name}")
                        item.setSizeHint(QSize(item.sizeHint().width(), 28))
                        item.setToolTip(path)
                        item.setData(Qt.UserRole, {
                            "type": "script",
                            "group_id": group.get("id"),
                            "group_name": group.get("name"),
                            "group_index": group_index,
                            "script_index": script_index,
                            "path": path,
                        })
                        if path in self.breakpoint_paths:
                            item.setBackground(QColor(255, 220, 220))
                        self.file_list.addItem(item)
        else:
            for script_index, path in enumerate(self.file_paths):
                display_name = os.path.basename(path) or path
                item = QListWidgetItem(display_name)
                item.setSizeHint(QSize(item.sizeHint().width(), 28))
                item.setToolTip(path)
                item.setData(Qt.UserRole, {
                    "type": "script",
                    "group_id": None,
                    "group_name": None,
                    "group_index": None,
                    "script_index": script_index,
                    "path": path,
                })
                if path in self.breakpoint_paths:
                    item.setBackground(QColor(255, 220, 220))
                self.file_list.addItem(item)

        if preserve_path:
            for row in range(self.file_list.count()):
                data = self.file_list.item(row).data(Qt.UserRole)
                if data and data.get("path") == preserve_path:
                    self.file_list.setCurrentRow(row)
                    break
        elif preserve_group_id:
            for row in range(self.file_list.count()):
                data = self.file_list.item(row).data(Qt.UserRole)
                if data and data.get("type") == "group" and data.get("group_id") == preserve_group_id:
                    self.file_list.setCurrentRow(row)
                    break

    def get_script_info_from_row(self, row):
        """Return descriptor dict for a script item at row."""
        if row is None or row < 0:
            return None
        item = self.file_list.item(row)
        if not item:
            return None
        data = item.data(Qt.UserRole)
        if not data or data.get("type") != "script":
            return None
        return data

    def rebuild_groups_from_view(self):
        """Reconstruct group data based on current list widget order."""
        new_groups = []
        current_group = None
        for row in range(self.file_list.count()):
            item = self.file_list.item(row)
            if not item:
                continue
            data = item.data(Qt.UserRole) or {}
            if data.get("type") == "group":
                original = self.get_group_by_id(data.get("group_id"))
                name = data.get("name") or (original.get("name") if original else "")
                group_id = data.get("group_id") or (original.get("id") if original else str(uuid4()))
                collapsed = data.get("collapsed")
                if collapsed is None and original:
                    collapsed = original.get("collapsed", False)
                current_group = {
                    "id": group_id,
                    "name": name,
                    "files": [],
                    "collapsed": bool(collapsed) if collapsed is not None else False,
                }
                new_groups.append(current_group)
            elif data.get("type") == "script":
                if current_group is None:
                    return False
                path = data.get("path")
                if path:
                    current_group["files"].append(path)
        self.groups = new_groups
        return True

    def collect_python_files(self, folder, recursive):
        """Collect .py files under folder."""
        scripts = []
        if recursive:
            for root, dirs, files in os.walk(folder):
                dirs.sort()
                for fname in sorted(files):
                    if fname.lower().endswith(".py"):
                        scripts.append(os.path.join(root, fname))
        else:
            try:
                for fname in sorted(os.listdir(folder)):
                    file_path = os.path.join(folder, fname)
                    if os.path.isfile(file_path) and fname.lower().endswith(".py"):
                        scripts.append(file_path)
            except Exception:
                pass
        return scripts

    def add_group(self, name, files):
        """Append a new group using provided files."""
        normalized_files = [path for path in files if path]
        if not normalized_files:
            return
        group_name = self.ensure_unique_group_name(name or "新建组")
        self.groups.append({
            "id": str(uuid4()),
            "name": group_name,
            "files": normalized_files,
            "collapsed": False,
        })

    def add_python_folder(self):
        """Add folders as script groups."""
        if self.is_running:
            QMessageBox.warning(self, "执行中", "请先停止当前任务再添加文件夹")
            return

        dialog = QFileDialog(self, "选择脚本文件夹")
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)

        # Allow selecting multiple folders from the custom dialog view
        for view in dialog.findChildren(QListView):
            view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        for view in dialog.findChildren(QTreeView):
            view.setSelectionMode(QAbstractItemView.ExtendedSelection)

        path1 = self.config.get("Paths", "Path1", fallback="")
        if path1 and os.path.isdir(path1):
            dialog.setDirectory(path1)

        if dialog.exec_() != QDialog.Accepted:
            return

        selected_folders = sorted({os.path.normpath(path) for path in dialog.selectedFiles()})
        if not selected_folders:
            return

        include_sub = QMessageBox.question(
            self,
            "包含子目录",
            "是否包含子目录中的Python脚本?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        ) == QMessageBox.Yes

        if not self.has_groups() and self.file_paths:
            self.ensure_group_mode()

        added_groups = []
        total_scripts = 0
        empty_folders = []
        skipped_folders = []
        for folder in selected_folders:
            scripts = self.collect_python_files(folder, include_sub)
            if not scripts:
                empty_folders.append(folder)
                continue
            base_name = os.path.basename(folder.rstrip(os.sep)) or os.path.basename(folder)
            chooser = FolderScriptsDialog(folder, scripts, self)
            if chooser.exec_() != QDialog.Accepted:
                skipped_folders.append(folder)
                continue
            selected_scripts = list(chooser.selected_files())
            if not selected_scripts:
                skipped_folders.append(folder)
                continue
            self.add_group(base_name, selected_scripts)
            added_groups.append(base_name)
            total_scripts += len(selected_scripts)

        if added_groups:
            self.refresh_file_list()
            self.update_stats()
            message_lines = [
                f"成功导入 {total_scripts} 个脚本，新增 {len(added_groups)} 个分组。"
            ]
            if empty_folders:
                message_lines.append(f"{len(empty_folders)} 个文件夹未包含Python脚本。")
            if skipped_folders:
                message_lines.append(f"{len(skipped_folders)} 个文件夹被跳过。")
            QMessageBox.information(self, "导入完成", "\n".join(message_lines))
        else:
            if empty_folders or skipped_folders:
                message_parts = []
                if empty_folders:
                    message_parts.append("选定的文件夹中没有Python脚本")
                if skipped_folders:
                    message_parts.append("未确认或未勾选任何脚本")
                QMessageBox.information(self, "未导入脚本", "，".join(message_parts))
            else:
                QMessageBox.information(self, "未导入脚本", "未选择任何可用的脚本")

    def add_python_file_to_group(self, group_id):
        """Helper to add python script directly into a target group."""
        self.add_python_file(target_group_id=group_id)

    def update_file_paths_on_drag(self, parent, start, end, destination, row):
        """Synchronize internal data when list items are reordered by drag-and-drop."""
        if self.is_running:
            return

        model = self.file_list.model()
        blocker = QSignalBlocker(model)

        if self.has_groups():
            if not self.rebuild_groups_from_view():
                self.refresh_file_list()
                return
        else:
            ordered_paths = []
            for index in range(self.file_list.count()):
                data = self.file_list.item(index).data(Qt.UserRole) or {}
                if data.get("type") == "script":
                    path = data.get("path")
                    if path:
                        ordered_paths.append(path)
            self.file_paths = ordered_paths

        self.refresh_file_list()
        self.update_stats()

    def show_context_menu(self, position):
        """Show context menu for file_list."""
        menu = QMenu()
        idx = self.file_list.indexAt(position)
        row = idx.row()

        if row < 0:
            add_script_action = menu.addAction("添加Python脚本")
            add_script_action.triggered.connect(lambda: self.add_python_file())
            add_folder_action = menu.addAction("添加文件夹")
            add_folder_action.triggered.connect(self.add_python_folder)
            menu.exec_(self.file_list.viewport().mapToGlobal(position))
            return

        self.file_list.setCurrentRow(row)
        descriptor = self.file_list.item(row).data(Qt.UserRole) or {}
        item_type = descriptor.get("type")

        if item_type == "group":
            collapsed = bool(descriptor.get("collapsed", False))
            toggle_action = menu.addAction("展开组" if collapsed else "折叠组")
            toggle_action.triggered.connect(lambda _, gid=descriptor.get("group_id"): self.toggle_group_collapse(gid))

            rename_action = menu.addAction("重命名组")
            rename_action.triggered.connect(lambda _, gid=descriptor.get("group_id"): self.rename_group(gid))

            menu.addSeparator()

            move_up_action = menu.addAction("组上移")
            move_up_action.triggered.connect(lambda _, gid=descriptor.get("group_id"): self.move_group_up(gid))
            move_up_action.setEnabled(self.get_group_position(descriptor.get("group_id")) > 0)

            move_down_action = menu.addAction("组下移")
            move_down_action.triggered.connect(lambda _, gid=descriptor.get("group_id"): self.move_group_down(gid))
            move_down_action.setEnabled(self.get_group_position(descriptor.get("group_id")) < len(self.groups) - 1)

            add_script_action = menu.addAction("向该组添加脚本")
            add_script_action.triggered.connect(lambda _, gid=descriptor.get("group_id"): self.add_python_file_to_group(gid))

            delete_action = menu.addAction("删除组")
            delete_action.triggered.connect(lambda _, gid=descriptor.get("group_id"): self.delete_group(gid))
        elif item_type == "script":
            run_action = menu.addAction("运行此脚本")
            run_action.triggered.connect(self.run_single_file)

            menu.addSeparator()

            set_break_action = menu.addAction("设置/清除断点")
            set_break_action.triggered.connect(self.toggle_breakpoint)
            set_break_action.setEnabled(not self.is_running)

            menu.addSeparator()

            move_up_action = menu.addAction("上移")
            move_up_action.triggered.connect(self.move_selected_item_up)

            move_down_action = menu.addAction("下移")
            move_down_action.triggered.connect(self.move_selected_item_down)

            delete_action = menu.addAction("删除Python脚本")
            delete_action.triggered.connect(self.delete_selected_item)

            add_action = menu.addAction("添加Python脚本")
            add_action.triggered.connect(lambda _, gid=descriptor.get("group_id"): self.add_python_file(target_group_id=gid))
        else:
            add_script_action = menu.addAction("添加Python脚本")
            add_script_action.triggered.connect(lambda: self.add_python_file())

        menu.addSeparator()
        add_folder_action = menu.addAction("添加文件夹")
        add_folder_action.triggered.connect(self.add_python_folder)

        menu.exec_(self.file_list.viewport().mapToGlobal(position))

    def move_selected_item_up(self):
        """Move the selected script up within its group."""
        info = self.get_script_info_from_row(self.file_list.currentRow())
        if not info:
            return
        preserve_path = info.get("path")

        if self.has_groups():
            group = self.get_group_by_id(info.get("group_id"))
            if not group:
                return
            if info.get("script_index", 0) <= 0:
                return
            files = group.get("files", [])
            idx = info["script_index"]
            files.insert(idx - 1, files.pop(idx))
        else:
            idx = info.get("script_index", 0)
            if idx <= 0:
                return
            self.file_paths.insert(idx - 1, self.file_paths.pop(idx))

        self.refresh_file_list(preserve_path=preserve_path)
        self.update_stats()

    def move_selected_item_down(self):
        """Move the selected script down within its group."""
        info = self.get_script_info_from_row(self.file_list.currentRow())
        if not info:
            return
        preserve_path = info.get("path")

        if self.has_groups():
            group = self.get_group_by_id(info.get("group_id"))
            if not group:
                return
            files = group.get("files", [])
            idx = info.get("script_index", 0)
            if idx >= len(files) - 1:
                return
            files.insert(idx + 1, files.pop(idx))
        else:
            idx = info.get("script_index", 0)
            if idx >= len(self.file_paths) - 1:
                return
            self.file_paths.insert(idx + 1, self.file_paths.pop(idx))

        self.refresh_file_list(preserve_path=preserve_path)
        self.update_stats()

    def delete_selected_item(self):
        """Delete the selected script or group."""
        row = self.file_list.currentRow()
        if row < 0:
            return
        descriptor = self.file_list.item(row).data(Qt.UserRole) or {}

        if descriptor.get("type") == "group":
            self.delete_group(descriptor.get("group_id"))
            return

        info = self.get_script_info_from_row(row)
        if not info:
            return

        path = info.get("path")
        if self.has_groups():
            group = self.get_group_by_id(info.get("group_id"))
            if not group:
                return
            files = group.get("files", [])
            idx = info.get("script_index", 0)
            if 0 <= idx < len(files):
                files.pop(idx)
        else:
            idx = info.get("script_index", 0)
            if 0 <= idx < len(self.file_paths):
                self.file_paths.pop(idx)

        self.breakpoint_paths.discard(path)
        self.refresh_file_list()
        self.update_stats()

    def add_python_file(self, target_group_id=None):
        """Add new Python script to current list or target group."""
        if self.is_running:
            QMessageBox.warning(self, "执行中", "请先停止当前任务再添加脚本")
            return

        path1 = self.config.get("Paths", "Path1", fallback="")
        if not path1 or not os.path.exists(path1):
            path1 = os.path.expanduser("~")

        file_name, _ = QFileDialog.getOpenFileName(
            self, "添加Python脚本", path1, "Python脚本 (*.py)"
        )
        if not file_name:
            return

        if self.has_groups():
            target_group = self.get_group_by_id(target_group_id)
            if target_group is None:
                # 如果未指定组，则使用当前选中项所在组或第一个组
                current_info = self.get_script_info_from_row(self.file_list.currentRow())
                if current_info:
                    target_group = self.get_group_by_id(current_info.get("group_id"))
                if target_group is None:
                    target_group = self.groups[0] if self.groups else None
            if target_group is None:
                self.ensure_group_mode()
                target_group = self.groups[0]
            target_group.setdefault("files", []).append(file_name)
        else:
            self.file_paths.append(file_name)

        self.refresh_file_list(preserve_path=file_name)
        self.update_stats()

    def move_group_up(self, group_id):
        """Move the specified group up by one position."""
        index = self.get_group_position(group_id)
        if index <= 0:
            return
        self.groups.insert(index - 1, self.groups.pop(index))
        self.refresh_file_list()
        self.update_stats()

    def move_group_down(self, group_id):
        """Move the specified group down by one position."""
        index = self.get_group_position(group_id)
        if index < 0 or index >= len(self.groups) - 1:
            return
        self.groups.insert(index + 1, self.groups.pop(index))
        self.refresh_file_list()
        self.update_stats()

    def rename_group(self, group_id):
        """Rename an existing group."""
        group = self.get_group_by_id(group_id)
        if not group:
            return
        current_name = group.get("name", "")
        new_name, ok = QInputDialog.getText(self, "重命名组", "组名称:", QLineEdit.Normal, current_name)
        if not ok:
            return
        new_name = new_name.strip()
        if not new_name or new_name == current_name:
            return
        group["name"] = self.ensure_unique_group_name(new_name)
        self.refresh_file_list()

    def delete_group(self, group_id):
        """Delete a group and its associated scripts."""
        group = self.get_group_by_id(group_id)
        if not group:
            return
        reply = QMessageBox.question(
            self,
            "删除组",
            f"确定要删除组 '{group.get('name')}' 及其所有脚本吗?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        for path in group.get("files", []):
            self.breakpoint_paths.discard(path)

        self.groups = [g for g in self.groups if g.get("id") != group_id]
        if not self.groups:
            self.file_paths = []
        self.refresh_file_list()
        self.update_stats()

    def load_files(self):
        """Load Python files from the directory specified in Path1."""
        # 获取Path1配置值
        path1 = self.config.get("Paths", "Path1", fallback="")
        
        # 如果配置为空，使用用户主目录
        if not path1 or not os.path.exists(path1):
            path1 = os.path.expanduser("~")
        
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择Python脚本", path1, "Python脚本 (*.py)"
        )
        if files:
            self.groups = []
            self.file_paths = list(files)
            self.breakpoint_paths.clear()
            self.scheme_name = "自定义文件集合"
            self.refresh_file_list()
            self.update_stats()

    def load_scheme(self):
        """Load a test scheme and its path configurations from the directory specified in Path2."""
        # 获取Path2配置值
        path2 = self.config.get("Paths", "Path2", fallback="")
        
        # 如果配置为空，使用用户主目录
        if not path2 or not os.path.exists(path2):
            path2 = os.path.expanduser("~")
        
        file_name, _ = QFileDialog.getOpenFileName(
            self, "加载方案", path2, "JSON文件 (*.json)"
        )
        if file_name:
            try:
                with open(file_name, "r", encoding="utf-8") as file:
                    scheme_data = json.load(file)

                groups_payload = scheme_data.get("groups") if isinstance(scheme_data, dict) else None

                if groups_payload:
                    self.groups = []
                    for group in groups_payload:
                        if not isinstance(group, dict):
                            continue
                        group_name = group.get("name") or "未命名组"
                        group_files = group.get("files", [])
                        group_id = group.get("id") or str(uuid4())
                        self.groups.append({
                            "id": group_id,
                            "name": group_name,
                            "files": list(group_files),
                            "collapsed": bool(group.get("collapsed", False)),
                        })
                    self.rebuild_flat_structure()
                else:
                    # 兼容旧版本
                    if isinstance(scheme_data, dict) and "file_paths" in scheme_data:
                        self.file_paths = scheme_data["file_paths"]
                    elif isinstance(scheme_data, list):
                        self.file_paths = scheme_data
                    else:
                        self.file_paths = []
                    self.groups = []

                breakpoint_list = []
                if isinstance(scheme_data, dict):
                    breakpoint_list = scheme_data.get("breakpoints", [])

                self.breakpoint_paths = {path for path in breakpoint_list if path in self.file_paths}

                if isinstance(scheme_data, dict) and "config" in scheme_data:
                    config = scheme_data["config"] or {}
                    if not self.config.has_section("Paths"):
                        self.config.add_section("Paths")
                    for key, value in config.items():
                        if key.startswith("Path") and value:
                            self.config.set("Paths", key, value)
                    self.save_config()

                self.scheme_name = os.path.basename(file_name)
                self.refresh_file_list()
                self.update_stats()
                QMessageBox.information(self, "成功", "方案加载成功!")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载方案失败:\n{e}")

    def run_files(self):
        self.rebuild_flat_structure()

        if not self.file_paths:
            QMessageBox.warning(self, "没有文件", "请加载Python脚本以执行")
            return
            
        if self.is_running:
            QMessageBox.warning(self, "任务执行中", "请先停止当前任务或等待任务完成")
            return
        
        total_scripts = len(self.file_paths)
        scheme_label = self.scheme_name if self.scheme_name else "未命名方案"
        self.prepare_run_context(total_scripts, scheme_label)

        # Initialize execution variables
        self.progress_bar.setValue(0)
        self.console_output.clear()  # Clear console output before starting
        self.start_time = datetime.now()
        self.elapsed_time = timedelta(0)
        self.current_file_index = 0
        
        # Update start time display
        self.start_time_value.setText(self.start_time.strftime("%Y-%m-%d %H:%M:%S"))
        
        # Reset the current index
        self.current_value.setText(f"0 / {max(total_scripts, 1)}")
        self.update_pending_exec_count()
        
        # Start the elapsed time timer
        self.elapsed_timer.start(1000)  # Update every second
        
        breakpoint_indexes = {
            index for index, entry in enumerate(self.flat_script_map)
            if entry.get("path") in self.breakpoint_paths
        }

        # Create and start the execution thread
        self.execution_thread = FileExecutionThread(self.file_paths, scheme_label, breakpoint_indexes)
        self.execution_thread.progress_signal.connect(self.progress_bar.setValue)
        self.execution_thread.executed_signal.connect(self.add_executed_file)
        self.execution_thread.error_signal.connect(self.show_error_message)
        self.execution_thread.finished.connect(self.execution_complete)
        self.execution_thread.current_index_signal.connect(self.update_current_index)
        self.execution_thread.breakpoint_hit_signal.connect(self.handle_breakpoint_hit)
        self.execution_thread.console_output_signal.connect(self.add_console_output)  # 连接控制台输出信号
        self.execution_thread.test_result_signal.connect(self.add_test_result)  # 连接测试结果信号
        self.execution_thread.script_console_signal.connect(self.capture_script_console)
        
        # Update UI
        self.is_running = True
        self.is_paused = False
        self.update_button_states()
        
        self.execution_thread.start()

    def handle_breakpoint_hit(self, index):
        """Handle when a breakpoint is hit during execution."""
        self.pause_execution()
        QMessageBox.information(
            self, 
            "断点命中", 
            f"在脚本 {os.path.basename(self.file_paths[index])} 处暂停执行"
        )

    def update_current_index(self, index):
        """Update the current index display."""
        try:
            total_scripts = int(self.total_value.text())
        except ValueError:
            total_scripts = len(self.file_paths)
        total_scripts = max(total_scripts, 1)
        clamped_index = min(index, total_scripts)
        self.current_value.setText(f"{clamped_index} / {total_scripts}")
        self.current_file_index = index - 1
        self.update_pending_exec_count()

    def update_stats(self):
        """Update the statistics panel values."""
        self.scheme_value.setText(self.scheme_name)
        self.total_value.setText(str(len(self.file_paths)))
        self.current_value.setText(f"0 / {len(self.file_paths)}")
        self.update_pending_exec_count()

    def save_scheme(self):
        """Save the current file paths and path configurations as a test scheme."""
        # 获取Path2配置值
        path2 = self.config.get("Paths", "Path2", fallback="")
        
        # 如果配置为空，使用用户主目录
        if not path2 or not os.path.exists(path2):
            path2 = os.path.expanduser("~")
        
        self.rebuild_flat_structure()

        if not self.file_paths:
            QMessageBox.warning(self, "没有文件", "请加载Python脚本以保存方案")
            return
        
        file_name, _ = QFileDialog.getSaveFileName(
            self, "保存方案", path2, "JSON文件 (*.json)"
        )
        if file_name:
            try:
                # 创建包含文件路径和配置的方案数据
                scheme_data = {
                    "file_paths": self.file_paths,
                    "config": {
                        "Path1": self.config.get("Paths", "Path1", fallback=""),
                        "Path2": self.config.get("Paths", "Path2", fallback=""),
                        "Path3": self.config.get("Paths", "Path3", fallback=""),
                        "Path4": self.config.get("Paths", "Path4", fallback="")
                    }
                }

                if self.has_groups():
                    scheme_data["groups"] = [
                        {
                            "id": group.get("id"),
                            "name": group.get("name"),
                            "files": list(group.get("files", [])),
                            "collapsed": bool(group.get("collapsed", False)),
                        }
                        for group in self.groups
                    ]

                if self.breakpoint_paths:
                    scheme_data["breakpoints"] = sorted(self.breakpoint_paths)
                
                with open(file_name, 'w', encoding='utf-8') as file:
                    json.dump(scheme_data, file, indent=2, ensure_ascii=False)
                self.scheme_name = os.path.basename(file_name)
                self.update_stats()
                QMessageBox.information(self, "成功", "方案保存成功!")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存方案失败:\n{e}")

    def show_error_message(self, message):
        self.elapsed_timer.stop()
        self.is_running = False
        self.update_button_states()
        QMessageBox.critical(self, "执行错误", message)

    def execution_complete(self):
        self.elapsed_timer.stop()
        self.is_running = False
        self.is_paused = False
        self.update_button_states()
        
        # 更新测试结果统计
        self.update_test_result_stats()

        # 统计结果概览
        pass_count = 0
        fail_count = 0
        pending_count = 0
        for result in self.test_results:
            if "不合格" in result["result"]:
                fail_count += 1
            elif "合格" in result["result"]:
                pass_count += 1
            else:
                pending_count += 1

        self.finalize_run_record(pass_count, fail_count, pending_count)

        try:
            total_scripts = int(self.total_value.text())
        except ValueError:
            total_scripts = len(self.file_paths)
        total_scripts = max(total_scripts, 1)
        executed_display = min(self.executed_count, total_scripts)
        self.current_value.setText(f"{executed_display} / {total_scripts}")
        self.update_pending_exec_count()
        
        QMessageBox.information(
            self,
            "执行完成",
            (
                "脚本执行完成!\n"
                f"总用时: {self.elapsed_time_value.text()}\n"
                f"执行脚本: {self.executed_count}/{total_scripts}\n"
                f"测试结果: 合格 {pass_count}, 不合格 {fail_count}, 待判定 {pending_count}"
            ),
        )
        
    def closeEvent(self, event):
        """Handle close event with confirmation, especially when execution is running."""
        if self.is_running:
            # 创建确认对话框
            reply = QMessageBox.question(
                self, 
                '确认关闭',
                '当前有任务正在执行。应用程序将在当前脚本完成后关闭。\n您确定要关闭吗？',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 创建等待对话框
                wait_dialog = QMessageBox(self)
                wait_dialog.setWindowTitle("请等待")
                wait_dialog.setText("正在等待当前脚本执行完成...")
                wait_dialog.setStandardButtons(QMessageBox.NoButton)  # 没有按钮
                wait_dialog.setModal(True)
                wait_dialog.show()
                
                # 请求线程停止（不中断当前脚本）
                if self.execution_thread:
                    self.execution_thread.stop()
                    
                # 等待线程结束（当前脚本执行完成）
                while self.execution_thread and self.execution_thread.isRunning():
                    QApplication.processEvents()  # 处理事件，保持界面响应
                    time.sleep(0.1)  # 避免CPU占用过高
                    
                wait_dialog.close()
                event.accept()
            else:
                event.ignore()
        else:
            # 没有运行中的任务，直接关闭
            event.accept()

    def show_test_result_context_menu(self, position):
        """Show context menu for test result table."""
        # 获取选中的行
        selected_items = self.test_result_table.selectedItems()
        if not selected_items:
            return

        # 获取选中行的脚本名称
        row = selected_items[0].row()
        file_name = self.test_result_table.item(row, 1).text()

        # 创建菜单
        menu = QMenu()

        # 添加菜单项
        script_log_action = menu.addAction("Python脚本日志")
        script_log_action.triggered.connect(lambda: self.open_log("script", file_name))

        device_log_action = menu.addAction("Python设备日志")
        device_log_action.triggered.connect(lambda: self.open_log("device", file_name))

        # 显示菜单
        menu.exec_(self.test_result_table.viewport().mapToGlobal(position))

    def open_log(self, log_type, file_name):
        """打开日志文件

        Args:
            log_type: 日志类型，'script' 或 'device'
            file_name: Python脚本名称
        """
        # 获取Path4配置值（日志输出目录）
        log_dir = self.config.get("Paths", "Path4", fallback="")

        # 如果配置为空，使用用户主目录
        if not log_dir or not os.path.exists(log_dir):
            log_dir = os.path.expanduser("~")

        # 构建日志文件名称模式
        base_name = os.path.splitext(file_name)[0]
        if log_type == "device":
            pattern = f"*{base_name}*device*.log"
        else:
            pattern = f"*{base_name}*.log"

        # 在目录中搜索匹配的日志文件
        matching_files = glob.glob(os.path.join(log_dir, pattern))

        if not matching_files:
            QMessageBox.information(self, "未找到日志", f"未找到匹配 '{pattern}' 的日志文件\n目录: {log_dir}")
            return

        # 如果找到多个匹配文件，让用户选择
        if len(matching_files) > 1:
            file_to_open, ok = QInputDialog.getItem(
                self, "选择日志文件", "找到多个匹配的日志文件:", matching_files, 0, False
            )
            if not ok or not file_to_open:
                return
        else:
            file_to_open = matching_files[0]

        # 打开日志文件
        try:
            if sys.platform == 'win32':
                os.startfile(file_to_open)
            else:
                # 对于非Windows系统，可以使用xdg-open或open命令
                subprocess.Popen(['xdg-open', file_to_open])
        except Exception as e:
            QMessageBox.critical(self, "打开失败", f"无法打开日志文件:\n{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Set application icon globally
    icon_path = resource_path("Icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    window = TestSequenceApp()
    window.show()
    sys.exit(app.exec_())