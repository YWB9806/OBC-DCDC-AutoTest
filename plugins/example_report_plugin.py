"""示例报告插件

演示如何创建一个报告生成插件。
"""

from typing import Dict, Any, Optional
from datetime import datetime

from AppCode.interfaces.i_plugin import IReportPlugin


class ExampleReportPlugin(IReportPlugin):
    """示例报告插件"""
    
    def __init__(self):
        """初始化插件"""
        self._context = None
        self._config = {
            'title': '测试执行报告',
            'include_charts': True,
            'format': 'html'
        }
    
    def get_name(self) -> str:
        """获取插件名称"""
        return "ExampleReportPlugin"
    
    def get_version(self) -> str:
        """获取插件版本"""
        return "1.0.0"
    
    def get_description(self) -> str:
        """获取插件描述"""
        return "示例报告生成插件，用于演示插件系统的使用"
    
    def get_author(self) -> str:
        """获取插件作者"""
        return "System"
    
    def initialize(self, context: Dict[str, Any]) -> bool:
        """初始化插件
        
        Args:
            context: 应用上下文
            
        Returns:
            是否初始化成功
        """
        try:
            self._context = context
            print(f"[{self.get_name()}] Plugin initialized")
            return True
        except Exception as e:
            print(f"[{self.get_name()}] Initialization failed: {e}")
            return False
    
    def execute(self, *args, **kwargs) -> Any:
        """执行插件
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            执行结果
        """
        # 获取数据
        data = kwargs.get('data', {})
        
        # 生成报告
        report = self.generate_report(data)
        
        return report
    
    def cleanup(self):
        """清理插件资源"""
        print(f"[{self.get_name()}] Plugin cleaned up")
    
    def get_config_schema(self) -> Dict[str, Any]:
        """获取配置模式
        
        Returns:
            配置模式
        """
        return {
            'title': 'string - 报告标题',
            'include_charts': 'boolean - 是否包含图表',
            'format': 'string - 报告格式 (html/pdf/markdown)'
        }
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置
        
        Args:
            config: 新配置
        """
        self._config.update(config)
        print(f"[{self.get_name()}] Config updated: {self._config}")
    
    def generate_report(self, data: Dict[str, Any]) -> str:
        """生成报告
        
        Args:
            data: 报告数据
            
        Returns:
            报告内容
        """
        title = self._config.get('title', '测试报告')
        format_type = self._config.get('format', 'html')
        
        if format_type == 'html':
            return self._generate_html_report(title, data)
        elif format_type == 'markdown':
            return self._generate_markdown_report(title, data)
        else:
            return self._generate_text_report(title, data)
    
    def _generate_html_report(self, title: str, data: Dict[str, Any]) -> str:
        """生成HTML报告"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .summary {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="summary">
        <h2>执行摘要</h2>
        <p>总执行数: {data.get('total', 0)}</p>
        <p>成功数: {data.get('success', 0)}</p>
        <p>失败数: {data.get('failed', 0)}</p>
        <p>成功率: {data.get('success_rate', 0):.2f}%</p>
    </div>
    
    <h2>详细结果</h2>
    <table>
        <tr>
            <th>脚本名称</th>
            <th>状态</th>
            <th>执行时间</th>
            <th>备注</th>
        </tr>
"""
        
        # 添加详细数据
        for item in data.get('details', []):
            html += f"""
        <tr>
            <td>{item.get('name', 'N/A')}</td>
            <td>{item.get('status', 'N/A')}</td>
            <td>{item.get('duration', 'N/A')}</td>
            <td>{item.get('note', '')}</td>
        </tr>
"""
        
        html += """
    </table>
</body>
</html>
"""
        return html
    
    def _generate_markdown_report(self, title: str, data: Dict[str, Any]) -> str:
        """生成Markdown报告"""
        md = f"""# {title}

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 执行摘要

- 总执行数: {data.get('total', 0)}
- 成功数: {data.get('success', 0)}
- 失败数: {data.get('failed', 0)}
- 成功率: {data.get('success_rate', 0):.2f}%

## 详细结果

| 脚本名称 | 状态 | 执行时间 | 备注 |
|---------|------|---------|------|
"""
        
        # 添加详细数据
        for item in data.get('details', []):
            md += f"| {item.get('name', 'N/A')} | {item.get('status', 'N/A')} | {item.get('duration', 'N/A')} | {item.get('note', '')} |\n"
        
        return md
    
    def _generate_text_report(self, title: str, data: Dict[str, Any]) -> str:
        """生成文本报告"""
        text = f"""{title}
{'=' * len(title)}

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

执行摘要
--------
总执行数: {data.get('total', 0)}
成功数: {data.get('success', 0)}
失败数: {data.get('failed', 0)}
成功率: {data.get('success_rate', 0):.2f}%

详细结果
--------
"""
        
        # 添加详细数据
        for item in data.get('details', []):
            text += f"\n脚本: {item.get('name', 'N/A')}\n"
            text += f"状态: {item.get('status', 'N/A')}\n"
            text += f"执行时间: {item.get('duration', 'N/A')}\n"
            text += f"备注: {item.get('note', '')}\n"
            text += "-" * 40 + "\n"
        
        return text
    
    def get_supported_formats(self) -> list:
        """获取支持的报告格式
        
        Returns:
            支持的格式列表
        """
        return ['html', 'markdown', 'text']
    
    def save_report(self, report: str, file_path: str) -> bool:
        """保存报告到文件
        
        Args:
            report: 报告内容
            file_path: 文件路径
            
        Returns:
            是否保存成功
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"[{self.get_name()}] Report saved to {file_path}")
            return True
        except Exception as e:
            print(f"[{self.get_name()}] Failed to save report: {e}")
            return False