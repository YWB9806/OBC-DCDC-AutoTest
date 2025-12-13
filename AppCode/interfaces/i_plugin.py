"""插件接口定义

定义插件系统的基础接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class IPlugin(ABC):
    """插件接口"""
    
    @abstractmethod
    def get_name(self) -> str:
        """获取插件名称
        
        Returns:
            插件名称
        """
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """获取插件版本
        
        Returns:
            版本号
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取插件描述
        
        Returns:
            插件描述
        """
        pass
    
    @abstractmethod
    def get_author(self) -> str:
        """获取插件作者
        
        Returns:
            作者名称
        """
        pass
    
    @abstractmethod
    def initialize(self, context: Dict[str, Any]) -> bool:
        """初始化插件
        
        Args:
            context: 应用上下文
            
        Returns:
            是否初始化成功
        """
        pass
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """执行插件功能
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            执行结果
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """清理插件资源"""
        pass
    
    def get_config_schema(self) -> Optional[Dict[str, Any]]:
        """获取配置模式
        
        Returns:
            配置模式定义（可选）
        """
        return None
    
    def on_config_changed(self, config: Dict[str, Any]):
        """配置变更回调
        
        Args:
            config: 新配置
        """
        pass


class IReportPlugin(IPlugin):
    """报告插件接口"""
    
    @abstractmethod
    def generate_report(
        self,
        execution_data: Dict[str, Any],
        output_path: str
    ) -> bool:
        """生成报告
        
        Args:
            execution_data: 执行数据
            output_path: 输出路径
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> list:
        """获取支持的报告格式
        
        Returns:
            格式列表（如：['pdf', 'html', 'excel']）
        """
        pass


class IAnalyzerPlugin(IPlugin):
    """分析器插件接口"""
    
    @abstractmethod
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析数据
        
        Args:
            data: 待分析数据
            
        Returns:
            分析结果
        """
        pass
    
    @abstractmethod
    def get_metrics(self) -> list:
        """获取支持的指标
        
        Returns:
            指标列表
        """
        pass


class INotificationPlugin(IPlugin):
    """通知插件接口"""
    
    @abstractmethod
    def send_notification(
        self,
        title: str,
        message: str,
        level: str = "info"
    ) -> bool:
        """发送通知
        
        Args:
            title: 通知标题
            message: 通知内容
            level: 通知级别（info/warning/error）
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def get_channels(self) -> list:
        """获取支持的通知渠道
        
        Returns:
            渠道列表（如：['email', 'sms', 'webhook']）
        """
        pass