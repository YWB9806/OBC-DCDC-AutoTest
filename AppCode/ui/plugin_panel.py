"""插件管理面板

提供插件的加载、卸载、配置和管理功能。
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional

from AppCode.core.plugin_manager import PluginManager


class PluginPanel(ttk.Frame):
    """插件管理面板"""
    
    def __init__(self, parent, plugin_manager: PluginManager):
        """初始化插件管理面板
        
        Args:
            parent: 父窗口
            plugin_manager: 插件管理器
        """
        super().__init__(parent)
        
        self.plugin_manager = plugin_manager
        
        self._create_widgets()
        self._refresh_plugin_list()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 标题
        title_label = ttk.Label(
            self,
            text="插件管理",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # 工具栏
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(
            toolbar,
            text="刷新列表",
            command=self._refresh_plugin_list
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            toolbar,
            text="加载插件",
            command=self._load_plugin
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            toolbar,
            text="卸载插件",
            command=self._unload_plugin
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            toolbar,
            text="重新加载",
            command=self._reload_plugin
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            toolbar,
            text="执行插件",
            command=self._execute_plugin
        ).pack(side=tk.LEFT, padx=5)
        
        # 插件列表
        list_frame = ttk.LabelFrame(self, text="已加载插件")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建表格
        columns = ("名称", "版本", "类型", "作者", "描述")
        self.plugin_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # 设置列
        self.plugin_tree.heading("名称", text="名称")
        self.plugin_tree.heading("版本", text="版本")
        self.plugin_tree.heading("类型", text="类型")
        self.plugin_tree.heading("作者", text="作者")
        self.plugin_tree.heading("描述", text="描述")
        
        self.plugin_tree.column("名称", width=150)
        self.plugin_tree.column("版本", width=80)
        self.plugin_tree.column("类型", width=100)
        self.plugin_tree.column("作者", width=100)
        self.plugin_tree.column("描述", width=300)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            command=self.plugin_tree.yview
        )
        self.plugin_tree.configure(yscrollcommand=scrollbar.set)
        
        self.plugin_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 插件详情
        detail_frame = ttk.LabelFrame(self, text="插件详情")
        detail_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.detail_text = tk.Text(
            detail_frame,
            height=8,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.detail_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 绑定选择事件
        self.plugin_tree.bind("<<TreeviewSelect>>", self._on_plugin_select)
    
    def _refresh_plugin_list(self):
        """刷新插件列表"""
        # 清空列表
        for item in self.plugin_tree.get_children():
            self.plugin_tree.delete(item)
        
        # 获取插件列表
        plugins = self.plugin_manager.list_plugins()
        
        # 添加到表格
        for plugin in plugins:
            self.plugin_tree.insert(
                "",
                tk.END,
                values=(
                    plugin['name'],
                    plugin['version'],
                    plugin['type'],
                    plugin['author'],
                    plugin['description']
                )
            )
    
    def _load_plugin(self):
        """加载插件"""
        # 选择插件文件
        file_path = filedialog.askopenfilename(
            title="选择插件文件",
            filetypes=[("Python文件", "*.py"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # 加载插件
            if self.plugin_manager.load_plugin(file_path):
                messagebox.showinfo("成功", "插件加载成功")
                self._refresh_plugin_list()
            else:
                messagebox.showerror("错误", "插件加载失败")
        
        except Exception as e:
            messagebox.showerror("错误", f"加载插件时出错：{str(e)}")
    
    def _unload_plugin(self):
        """卸载插件"""
        plugin_name = self._get_selected_plugin_name()
        
        if not plugin_name:
            messagebox.showwarning("警告", "请先选择一个插件")
            return
        
        # 确认
        if not messagebox.askyesno(
            "确认",
            f"确定要卸载插件 '{plugin_name}' 吗？"
        ):
            return
        
        try:
            if self.plugin_manager.unload_plugin(plugin_name):
                messagebox.showinfo("成功", "插件卸载成功")
                self._refresh_plugin_list()
            else:
                messagebox.showerror("错误", "插件卸载失败")
        
        except Exception as e:
            messagebox.showerror("错误", f"卸载插件时出错：{str(e)}")
    
    def _reload_plugin(self):
        """重新加载插件"""
        plugin_name = self._get_selected_plugin_name()
        
        if not plugin_name:
            messagebox.showwarning("警告", "请先选择一个插件")
            return
        
        try:
            if self.plugin_manager.reload_plugin(plugin_name):
                messagebox.showinfo("成功", "插件重新加载成功")
                self._refresh_plugin_list()
            else:
                messagebox.showerror("错误", "插件重新加载失败")
        
        except Exception as e:
            messagebox.showerror("错误", f"重新加载插件时出错：{str(e)}")
    
    def _execute_plugin(self):
        """执行插件"""
        plugin_name = self._get_selected_plugin_name()
        
        if not plugin_name:
            messagebox.showwarning("警告", "请先选择一个插件")
            return
        
        # 创建执行对话框
        dialog = PluginExecuteDialog(self, plugin_name, self.plugin_manager)
        self.wait_window(dialog)
    
    def _on_plugin_select(self, event):
        """插件选择事件"""
        plugin_name = self._get_selected_plugin_name()
        
        if not plugin_name:
            return
        
        # 获取插件实例
        plugin = self.plugin_manager.get_plugin(plugin_name)
        
        if not plugin:
            return
        
        # 显示详情
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete(1.0, tk.END)
        
        details = f"""名称: {plugin.get_name()}
版本: {plugin.get_version()}
作者: {plugin.get_author()}
描述: {plugin.get_description()}

配置模式:
{self._format_config_schema(plugin.get_config_schema())}
"""
        
        self.detail_text.insert(1.0, details)
        self.detail_text.config(state=tk.DISABLED)
    
    def _get_selected_plugin_name(self) -> Optional[str]:
        """获取选中的插件名称"""
        selection = self.plugin_tree.selection()
        
        if not selection:
            return None
        
        item = self.plugin_tree.item(selection[0])
        return item['values'][0]
    
    def _format_config_schema(self, schema: dict) -> str:
        """格式化配置模式"""
        if not schema:
            return "  无配置项"
        
        lines = []
        for key, value in schema.items():
            lines.append(f"  {key}: {value}")
        
        return "\n".join(lines)


class PluginExecuteDialog(tk.Toplevel):
    """插件执行对话框"""
    
    def __init__(self, parent, plugin_name: str, plugin_manager: PluginManager):
        """初始化对话框
        
        Args:
            parent: 父窗口
            plugin_name: 插件名称
            plugin_manager: 插件管理器
        """
        super().__init__(parent)
        
        self.plugin_name = plugin_name
        self.plugin_manager = plugin_manager
        
        self.title(f"执行插件 - {plugin_name}")
        self.geometry("500x400")
        self.resizable(False, False)
        
        # 居中显示
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 参数输入
        param_frame = ttk.LabelFrame(self, text="执行参数")
        param_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(param_frame, text="参数 (JSON格式):").pack(anchor=tk.W, padx=5, pady=5)
        
        self.param_text = tk.Text(param_frame, height=10)
        self.param_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.param_text.insert(1.0, "{}")
        
        # 结果显示
        result_frame = ttk.LabelFrame(self, text="执行结果")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.result_text = tk.Text(result_frame, height=10, state=tk.DISABLED)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 按钮
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            button_frame,
            text="执行",
            command=self._execute
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="关闭",
            command=self.destroy
        ).pack(side=tk.RIGHT, padx=5)
    
    def _execute(self):
        """执行插件"""
        try:
            # 解析参数
            import json
            param_str = self.param_text.get(1.0, tk.END).strip()
            params = json.loads(param_str) if param_str else {}
            
            # 执行插件
            result = self.plugin_manager.execute_plugin(
                self.plugin_name,
                **params
            )
            
            # 显示结果
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, f"执行成功！\n\n结果:\n{result}")
            self.result_text.config(state=tk.DISABLED)
        
        except json.JSONDecodeError as e:
            messagebox.showerror("错误", f"参数格式错误：{str(e)}")
        
        except Exception as e:
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, f"执行失败！\n\n错误:\n{str(e)}")
            self.result_text.config(state=tk.DISABLED)