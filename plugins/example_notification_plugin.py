"""示例通知插件

演示如何创建一个通知发送插件。
"""

from typing import Dict, Any, List
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from AppCode.interfaces.i_plugin import INotificationPlugin


class ExampleNotificationPlugin(INotificationPlugin):
    """示例通知插件"""
    
    def __init__(self):
        """初始化插件"""
        self._context = None
        self._config = {
            'notification_types': ['console', 'file'],  # console, file, email
            'log_file': 'notifications.log',
            'email_enabled': False,
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587,
            'sender_email': 'noreply@example.com',
            'sender_password': '',
            'recipients': []
        }
    
    def get_name(self) -> str:
        """获取插件名称"""
        return "ExampleNotificationPlugin"
    
    def get_version(self) -> str:
        """获取插件版本"""
        return "1.0.0"
    
    def get_description(self) -> str:
        """获取插件描述"""
        return "示例通知插件，支持控制台、文件和邮件通知"
    
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
                - message: 通知消息
                - level: 通知级别 (info/warning/error)
                - data: 附加数据
            
        Returns:
            发送结果
        """
        message = kwargs.get('message', '')
        level = kwargs.get('level', 'info')
        data = kwargs.get('data', {})
        
        if not message:
            return {'success': False, 'error': 'No message provided'}
        
        # 发送通知
        result = self.send_notification(message, level, data)
        
        return result
    
    def cleanup(self):
        """清理插件资源"""
        print(f"[{self.get_name()}] Plugin cleaned up")
    
    def get_config_schema(self) -> Dict[str, Any]:
        """获取配置模式
        
        Returns:
            配置模式
        """
        return {
            'notification_types': 'list - 通知类型 (console/file/email)',
            'log_file': 'string - 日志文件路径',
            'email_enabled': 'boolean - 是否启用邮件通知',
            'smtp_server': 'string - SMTP服务器地址',
            'smtp_port': 'int - SMTP端口',
            'sender_email': 'string - 发件人邮箱',
            'sender_password': 'string - 发件人密码',
            'recipients': 'list - 收件人列表'
        }
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置
        
        Args:
            config: 新配置
        """
        self._config.update(config)
        print(f"[{self.get_name()}] Config updated")
    
    def send_notification(
        self,
        message: str,
        level: str = 'info',
        data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """发送通知
        
        Args:
            message: 通知消息
            level: 通知级别
            data: 附加数据
            
        Returns:
            发送结果
        """
        results = []
        
        # 格式化消息
        formatted_message = self._format_message(message, level, data)
        
        # 根据配置发送不同类型的通知
        for notification_type in self._config['notification_types']:
            if notification_type == 'console':
                result = self._send_console_notification(formatted_message, level)
                results.append(result)
            
            elif notification_type == 'file':
                result = self._send_file_notification(formatted_message, level)
                results.append(result)
            
            elif notification_type == 'email' and self._config['email_enabled']:
                result = self._send_email_notification(formatted_message, level, data)
                results.append(result)
        
        # 汇总结果
        success = all(r['success'] for r in results)
        
        return {
            'success': success,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
    
    def _format_message(
        self,
        message: str,
        level: str,
        data: Dict[str, Any] = None
    ) -> str:
        """格式化消息"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        level_upper = level.upper()
        
        formatted = f"[{timestamp}] [{level_upper}] {message}"
        
        if data:
            formatted += f"\n附加数据: {data}"
        
        return formatted
    
    def _send_console_notification(self, message: str, level: str) -> Dict[str, Any]:
        """发送控制台通知"""
        try:
            # 根据级别使用不同的输出
            if level == 'error':
                print(f"\033[91m{message}\033[0m")  # 红色
            elif level == 'warning':
                print(f"\033[93m{message}\033[0m")  # 黄色
            else:
                print(f"\033[92m{message}\033[0m")  # 绿色
            
            return {
                'success': True,
                'type': 'console',
                'message': 'Console notification sent'
            }
        
        except Exception as e:
            return {
                'success': False,
                'type': 'console',
                'error': str(e)
            }
    
    def _send_file_notification(self, message: str, level: str) -> Dict[str, Any]:
        """发送文件通知（写入日志文件）"""
        try:
            log_file = self._config['log_file']
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(message + '\n')
            
            return {
                'success': True,
                'type': 'file',
                'message': f'Notification written to {log_file}'
            }
        
        except Exception as e:
            return {
                'success': False,
                'type': 'file',
                'error': str(e)
            }
    
    def _send_email_notification(
        self,
        message: str,
        level: str,
        data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """发送邮件通知"""
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self._config['sender_email']
            msg['To'] = ', '.join(self._config['recipients'])
            msg['Subject'] = f"[{level.upper()}] 系统通知"
            
            # 邮件正文
            body = message
            if data:
                body += f"\n\n详细信息:\n{self._format_data(data)}"
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 发送邮件
            with smtplib.SMTP(self._config['smtp_server'], self._config['smtp_port']) as server:
                server.starttls()
                server.login(self._config['sender_email'], self._config['sender_password'])
                server.send_message(msg)
            
            return {
                'success': True,
                'type': 'email',
                'message': f'Email sent to {len(self._config["recipients"])} recipients'
            }
        
        except Exception as e:
            return {
                'success': False,
                'type': 'email',
                'error': str(e)
            }
    
    def _format_data(self, data: Dict[str, Any]) -> str:
        """格式化附加数据"""
        lines = []
        for key, value in data.items():
            lines.append(f"  {key}: {value}")
        return '\n'.join(lines)
    
    def get_supported_channels(self) -> List[str]:
        """获取支持的通知渠道
        
        Returns:
            支持的渠道列表
        """
        return ['console', 'file', 'email']
    
    def test_connection(self, channel: str) -> bool:
        """测试通知渠道连接
        
        Args:
            channel: 通知渠道
            
        Returns:
            是否连接成功
        """
        if channel == 'console':
            return True
        
        elif channel == 'file':
            try:
                log_file = self._config['log_file']
                with open(log_file, 'a') as f:
                    pass
                return True
            except:
                return False
        
        elif channel == 'email':
            try:
                if not self._config['email_enabled']:
                    return False
                
                with smtplib.SMTP(self._config['smtp_server'], self._config['smtp_port'], timeout=5) as server:
                    server.starttls()
                    server.login(self._config['sender_email'], self._config['sender_password'])
                return True
            except:
                return False
        
        return False