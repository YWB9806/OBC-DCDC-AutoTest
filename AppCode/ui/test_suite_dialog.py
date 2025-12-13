"""测试方案对话框

提供测试方案的创建、编辑和管理界面。
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QInputDialog, QFileDialog, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from typing import List, Dict, Any, Optional
import json


class SaveSuiteDialog(QDialog):
    """保存测试方案对话框"""
    
    def __init__(self, script_paths: List[str], parent=None):
        """初始化对话框
        
        Args:
            script_paths: 要保存的脚本路径列表
            parent: 父窗口
        """
        super().__init__(parent)
        self.script_paths = script_paths
        self.suite_name = None
        self.suite_description = None
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("保存测试方案")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout(self)
        
        # 方案名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("方案名称:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入方案名称（必填）")
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # 方案描述
        layout.addWidget(QLabel("方案描述:"))
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("请输入方案描述（可选）")
        self.description_edit.setMaximumHeight(80)
        layout.addWidget(self.description_edit)
        
        # 脚本列表
        layout.addWidget(QLabel(f"包含脚本: {len(self.script_paths)} 个"))
        
        self.script_table = QTableWidget()
        self.script_table.setColumnCount(1)
        self.script_table.setHorizontalHeaderLabels(["脚本路径"])
        self.script_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.script_table.setMaximumHeight(200)
        
        for path in self.script_paths:
            row = self.script_table.rowCount()
            self.script_table.insertRow(row)
            self.script_table.setItem(row, 0, QTableWidgetItem(path))
        
        layout.addWidget(self.script_table)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _on_save(self):
        """保存按钮点击"""
        name = self.name_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "警告", "请输入方案名称")
            return
        
        self.suite_name = name
        self.suite_description = self.description_edit.toPlainText().strip()
        self.accept()
    
    def get_suite_info(self) -> Dict[str, Any]:
        """获取方案信息
        
        Returns:
            方案信息字典
        """
        return {
            'name': self.suite_name,
            'description': self.suite_description,
            'script_paths': self.script_paths
        }


class ManageSuitesDialog(QDialog):
    """管理测试方案对话框"""
    
    suite_selected = pyqtSignal(dict)  # 选择方案信号
    
    def __init__(self, container, parent=None):
        """初始化对话框
        
        Args:
            container: 依赖注入容器
            parent: 父窗口
        """
        super().__init__(parent)
        self.container = container
        self.logger = container.resolve('log_manager').get_logger('ui')
        self.suite_service = container.resolve('test_suite_service')
        
        self._init_ui()
        self._load_suites()
    
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("测试方案管理")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self._load_suites)
        toolbar_layout.addWidget(self.refresh_btn)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索方案...")
        self.search_edit.textChanged.connect(self._on_search)
        toolbar_layout.addWidget(self.search_edit)
        
        toolbar_layout.addStretch()
        
        self.import_btn = QPushButton("导入")
        self.import_btn.clicked.connect(self._on_import)
        toolbar_layout.addWidget(self.import_btn)
        
        self.export_btn = QPushButton("导出")
        self.export_btn.clicked.connect(self._on_export)
        toolbar_layout.addWidget(self.export_btn)
        
        layout.addLayout(toolbar_layout)
        
        # 方案列表
        self.suite_table = QTableWidget()
        self.suite_table.setColumnCount(6)
        self.suite_table.setHorizontalHeaderLabels([
            "ID", "方案名称", "脚本数", "执行次数", "最后执行", "操作"
        ])
        self.suite_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.suite_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.suite_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.suite_table)
        
        # 详情面板
        detail_layout = QVBoxLayout()
        detail_layout.addWidget(QLabel("方案详情:"))
        
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMaximumHeight(150)
        detail_layout.addWidget(self.detail_text)
        
        layout.addLayout(detail_layout)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
        # 连接信号
        self.suite_table.itemSelectionChanged.connect(self._on_selection_changed)
    
    def _load_suites(self):
        """加载方案列表"""
        try:
            suites = self.suite_service.list_suites()
            self._display_suites(suites)
            self.logger.info(f"Loaded {len(suites)} test suites")
        except Exception as e:
            self.logger.error(f"Error loading suites: {e}")
            QMessageBox.critical(self, "错误", f"加载方案失败: {e}")
    
    def _display_suites(self, suites: List[Dict[str, Any]]):
        """显示方案列表
        
        Args:
            suites: 方案列表
        """
        self.suite_table.setRowCount(0)
        
        for suite in suites:
            row = self.suite_table.rowCount()
            self.suite_table.insertRow(row)
            
            # ID - 居中对齐
            id_item = QTableWidgetItem(str(suite.get('id', '')))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.suite_table.setItem(row, 0, id_item)
            
            # 名称 - 左对齐（默认）
            name_item = QTableWidgetItem(suite.get('name', ''))
            self.suite_table.setItem(row, 1, name_item)
            
            # 脚本数 - 居中对齐
            script_count_item = QTableWidgetItem(str(suite.get('script_count', 0)))
            script_count_item.setTextAlignment(Qt.AlignCenter)
            self.suite_table.setItem(row, 2, script_count_item)
            
            # 执行次数 - 居中对齐
            exec_count_item = QTableWidgetItem(str(suite.get('execution_count', 0)))
            exec_count_item.setTextAlignment(Qt.AlignCenter)
            self.suite_table.setItem(row, 3, exec_count_item)
            
            # 最后执行时间 - 居中对齐
            last_exec = suite.get('last_executed_time', '-')
            if last_exec and last_exec != '-':
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(last_exec)
                    last_exec = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            last_exec_item = QTableWidgetItem(last_exec)
            last_exec_item.setTextAlignment(Qt.AlignCenter)
            self.suite_table.setItem(row, 4, last_exec_item)
            
            # 操作按钮
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            
            load_btn = QPushButton("加载")
            load_btn.clicked.connect(lambda checked, s=suite: self._on_load_suite(s))
            btn_layout.addWidget(load_btn)
            
            edit_btn = QPushButton("编辑")
            edit_btn.clicked.connect(lambda checked, s=suite: self._on_edit_suite(s))
            btn_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(lambda checked, s=suite: self._on_delete_suite(s))
            btn_layout.addWidget(delete_btn)
            
            self.suite_table.setCellWidget(row, 5, btn_widget)
    
    def _on_selection_changed(self):
        """选择变化"""
        selected_rows = self.suite_table.selectedItems()
        if not selected_rows:
            self.detail_text.clear()
            return
        
        row = selected_rows[0].row()
        suite_id = int(self.suite_table.item(row, 0).text())
        
        try:
            suite = self.suite_service.get_suite(suite_id)
            if suite:
                self._display_suite_detail(suite)
        except Exception as e:
            self.logger.error(f"Error loading suite detail: {e}")
    
    def _display_suite_detail(self, suite: Dict[str, Any]):
        """显示方案详情
        
        Args:
            suite: 方案信息
        """
        detail = f"方案名称: {suite.get('name', '')}\n"
        detail += f"描述: {suite.get('description', '无')}\n"
        detail += f"脚本数量: {suite.get('script_count', 0)}\n"
        detail += f"创建者: {suite.get('created_by', '未知')}\n"
        detail += f"创建时间: {suite.get('created_time', '')}\n"
        detail += f"执行次数: {suite.get('execution_count', 0)}\n\n"
        detail += "包含脚本:\n"
        
        script_paths = suite.get('script_paths', [])
        if isinstance(script_paths, str):
            try:
                script_paths = json.loads(script_paths)
            except:
                script_paths = []
        
        for i, path in enumerate(script_paths, 1):
            detail += f"{i}. {path}\n"
        
        self.detail_text.setText(detail)
    
    def _on_load_suite(self, suite: Dict[str, Any]):
        """加载方案"""
        self.suite_selected.emit(suite)
        self.accept()
    
    def _on_edit_suite(self, suite: Dict[str, Any]):
        """编辑方案"""
        # 获取新名称
        new_name, ok = QInputDialog.getText(
            self, "编辑方案", "方案名称:", 
            text=suite.get('name', '')
        )
        
        if not ok or not new_name.strip():
            return
        
        # 获取新描述
        new_desc, ok = QInputDialog.getMultiLineText(
            self, "编辑方案", "方案描述:",
            text=suite.get('description', '')
        )
        
        if not ok:
            return
        
        try:
            result = self.suite_service.update_suite(
                suite_id=suite['id'],
                name=new_name.strip(),
                description=new_desc.strip()
            )
            
            if result['success']:
                QMessageBox.information(self, "成功", "方案更新成功")
                self._load_suites()
            else:
                QMessageBox.warning(self, "失败", f"更新失败: {result.get('error', '')}")
        
        except Exception as e:
            self.logger.error(f"Error updating suite: {e}")
            QMessageBox.critical(self, "错误", f"更新方案时出错: {e}")
    
    def _on_delete_suite(self, suite: Dict[str, Any]):
        """删除方案"""
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除方案 '{suite.get('name', '')}' 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            result = self.suite_service.delete_suite(suite['id'])
            
            if result['success']:
                QMessageBox.information(self, "成功", "方案删除成功")
                self._load_suites()
            else:
                QMessageBox.warning(self, "失败", f"删除失败: {result.get('error', '')}")
        
        except Exception as e:
            self.logger.error(f"Error deleting suite: {e}")
            QMessageBox.critical(self, "错误", f"删除方案时出错: {e}")
    
    def _on_search(self, text: str):
        """搜索方案"""
        if not text.strip():
            self._load_suites()
            return
        
        try:
            suites = self.suite_service.search_suites(text.strip())
            self._display_suites(suites)
        except Exception as e:
            self.logger.error(f"Error searching suites: {e}")
    
    def _on_import(self):
        """导入方案"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入测试方案", "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            result = self.suite_service.import_suite_from_file(file_path)
            
            if result['success']:
                QMessageBox.information(self, "成功", "方案导入成功")
                self._load_suites()
            else:
                QMessageBox.warning(self, "失败", f"导入失败: {result.get('error', '')}")
        
        except Exception as e:
            self.logger.error(f"Error importing suite: {e}")
            QMessageBox.critical(self, "错误", f"导入方案时出错: {e}")
    
    def _on_export(self):
        """导出方案"""
        selected_rows = self.suite_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要导出的方案")
            return
        
        row = selected_rows[0].row()
        suite_id = int(self.suite_table.item(row, 0).text())
        suite_name = self.suite_table.item(row, 1).text()
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出测试方案", f"{suite_name}.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            result = self.suite_service.export_suite_to_file(suite_id, file_path)
            
            if result['success']:
                QMessageBox.information(self, "成功", f"方案已导出到: {file_path}")
            else:
                QMessageBox.warning(self, "失败", f"导出失败: {result.get('error', '')}")
        
        except Exception as e:
            self.logger.error(f"Error exporting suite: {e}")
            QMessageBox.critical(self, "错误", f"导出方案时出错: {e}")