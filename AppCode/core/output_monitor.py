"""输出监控器

用于监控脚本执行的输出，包括标准输出和可能的输出文件。
"""

import os
import time
import threading
from typing import List, Callable, Optional
from pathlib import Path


class OutputMonitor:
    """输出监控器"""
    
    def __init__(self, script_path: str, output_callback: Optional[Callable] = None):
        """初始化输出监控器
        
        Args:
            script_path: 脚本路径
            output_callback: 输出回调函数
        """
        self.script_path = script_path
        self.output_callback = output_callback
        self.script_dir = os.path.dirname(os.path.abspath(script_path))
        self.script_name = os.path.basename(script_path)
        
        self._monitoring = False
        self._monitor_thread = None
        self._monitored_files = set()
        self._file_positions = {}
        
        # 可能的输出文件位置
        self._potential_output_dirs = [
            self.script_dir,
            os.path.join(self.script_dir, 'output'),
            os.path.join(self.script_dir, 'logs'),
            os.path.join(self.script_dir, '..', 'output'),
            os.path.join(self.script_dir, '..', 'logs'),
        ]
    
    def start(self):
        """开始监控"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self._monitor_thread.start()
    
    def stop(self):
        """停止监控"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
    
    def _monitor_loop(self):
        """监控循环"""
        while self._monitoring:
            try:
                # 查找新的输出文件
                self._discover_output_files()
                
                # 读取文件更新
                self._read_file_updates()
                
                time.sleep(0.5)  # 每0.5秒检查一次
            
            except Exception as e:
                # 静默处理错误，避免影响主流程
                pass
    
    def _discover_output_files(self):
        """发现输出文件"""
        for output_dir in self._potential_output_dirs:
            if not os.path.exists(output_dir):
                continue
            
            try:
                # 查找最近修改的文本文件
                for file_path in Path(output_dir).glob('*.txt'):
                    # 检查文件是否在最近1分钟内修改
                    mtime = os.path.getmtime(file_path)
                    if time.time() - mtime < 60:
                        file_str = str(file_path)
                        if file_str not in self._monitored_files:
                            self._monitored_files.add(file_str)
                            self._file_positions[file_str] = 0
                
                # 也查找log文件
                for file_path in Path(output_dir).glob('*.log'):
                    mtime = os.path.getmtime(file_path)
                    if time.time() - mtime < 60:
                        file_str = str(file_path)
                        if file_str not in self._monitored_files:
                            self._monitored_files.add(file_str)
                            self._file_positions[file_str] = 0
            
            except Exception:
                pass
    
    def _read_file_updates(self):
        """读取文件更新"""
        for file_path in list(self._monitored_files):
            try:
                if not os.path.exists(file_path):
                    continue
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    # 移动到上次读取的位置
                    f.seek(self._file_positions.get(file_path, 0))
                    
                    # 读取新内容
                    new_content = f.read()
                    
                    if new_content and self.output_callback:
                        # 按行分割并回调
                        lines = new_content.split('\n')
                        for line in lines:
                            if line.strip():
                                self.output_callback(line)
                    
                    # 更新位置
                    self._file_positions[file_path] = f.tell()
            
            except Exception:
                pass