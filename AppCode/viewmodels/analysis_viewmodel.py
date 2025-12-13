"""分析视图模型

管理统计分析相关的UI数据和操作。
"""

from typing import Dict, List, Optional
from PyQt5.QtCore import QObject, pyqtSignal
from datetime import datetime, timedelta


class AnalysisViewModel(QObject):
    """分析视图模型"""
    
    # 信号定义
    statistics_updated = pyqtSignal(dict)  # 统计数据更新
    report_generated = pyqtSignal(str)     # 报告生成完成
    error_occurred = pyqtSignal(str)       # 错误发生
    
    def __init__(self, container):
        """初始化分析视图模型
        
        Args:
            container: 依赖注入容器
        """
        super().__init__()
        
        self.container = container
        self.logger = container.resolve('log_manager').get_logger('viewmodel')
        self.analysis_service = container.resolve('analysis_service')
        
        self._statistics = {}
        self._reports = {}
    
    def load_statistics(self, start_date: str = None, end_date: str = None):
        """加载统计数据
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
        """
        try:
            result = self.analysis_service.get_overall_statistics(
                start_date=start_date,
                end_date=end_date
            )
            
            if result['success']:
                self._statistics = result['statistics']
                self.statistics_updated.emit(self._statistics)
                self.logger.info("Statistics loaded successfully")
            else:
                error = result.get('error', 'Unknown error')
                self.error_occurred.emit(f"加载统计数据失败: {error}")
                self.logger.error(f"Failed to load statistics: {error}")
        
        except Exception as e:
            self.logger.error(f"Error loading statistics: {e}")
            self.error_occurred.emit(f"加载统计数据时出错: {e}")
    
    def get_statistics(self) -> Dict:
        """获取当前统计数据
        
        Returns:
            统计数据
        """
        return self._statistics
    
    def get_script_statistics(self, script_path: str) -> Optional[Dict]:
        """获取特定脚本的统计
        
        Args:
            script_path: 脚本路径
            
        Returns:
            脚本统计数据
        """
        try:
            result = self.analysis_service.get_script_statistics(script_path)
            
            if result['success']:
                return result['statistics']
            else:
                error = result.get('error', 'Unknown error')
                self.logger.error(f"Failed to get script statistics: {error}")
                return None
        
        except Exception as e:
            self.logger.error(f"Error getting script statistics: {e}")
            return None
    
    def get_daily_statistics(self, days: int = 30) -> List[Dict]:
        """获取每日统计
        
        Args:
            days: 天数
            
        Returns:
            每日统计列表
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            result = self.analysis_service.get_daily_statistics(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            if result['success']:
                return result['daily_stats']
            else:
                error = result.get('error', 'Unknown error')
                self.logger.error(f"Failed to get daily statistics: {error}")
                return []
        
        except Exception as e:
            self.logger.error(f"Error getting daily statistics: {e}")
            return []
    
    def generate_report(self, report_type: str = 'summary') -> Optional[str]:
        """生成报告
        
        Args:
            report_type: 报告类型 (summary/detailed/trend)
            
        Returns:
            报告内容
        """
        try:
            result = self.analysis_service.generate_report(report_type)
            
            if result['success']:
                content = result['content']
                self._reports[report_type] = content
                self.report_generated.emit(content)
                self.logger.info(f"Generated {report_type} report")
                return content
            else:
                error = result.get('error', 'Unknown error')
                self.error_occurred.emit(f"生成报告失败: {error}")
                self.logger.error(f"Failed to generate report: {error}")
                return None
        
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            self.error_occurred.emit(f"生成报告时出错: {e}")
            return None
    
    def export_report(self, report_type: str, file_path: str) -> bool:
        """导出报告
        
        Args:
            report_type: 报告类型
            file_path: 文件路径
            
        Returns:
            是否成功
        """
        try:
            # 如果报告未生成，先生成
            if report_type not in self._reports:
                content = self.generate_report(report_type)
                if not content:
                    return False
            else:
                content = self._reports[report_type]
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"Exported report to: {file_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error exporting report: {e}")
            self.error_occurred.emit(f"导出报告时出错: {e}")
            return False
    
    def get_top_scripts(self, limit: int = 10) -> List[Dict]:
        """获取最常执行的脚本
        
        Args:
            limit: 返回数量限制
            
        Returns:
            脚本列表
        """
        top_scripts = self._statistics.get('top_scripts', [])
        return top_scripts[:limit]
    
    def get_success_rate(self) -> float:
        """获取成功率
        
        Returns:
            成功率百分比
        """
        return self._statistics.get('success_rate', 0.0)
    
    def get_total_executions(self) -> int:
        """获取总执行次数
        
        Returns:
            执行次数
        """
        return self._statistics.get('total_executions', 0)
    
    def get_average_duration(self) -> float:
        """获取平均执行时长
        
        Returns:
            平均时长（秒）
        """
        return self._statistics.get('average_duration', 0.0)
    
    def get_status_distribution(self) -> Dict[str, int]:
        """获取状态分布
        
        Returns:
            状态分布字典
        """
        return self._statistics.get('scripts_by_status', {})
    
    def get_trend_data(self, days: int = 30) -> Dict:
        """获取趋势数据
        
        Args:
            days: 天数
            
        Returns:
            趋势数据
        """
        daily_stats = self.get_daily_statistics(days)
        
        dates = []
        executions = []
        success_rates = []
        
        for stat in daily_stats:
            dates.append(stat['date'])
            executions.append(stat['total'])
            success_rates.append(stat['success_rate'])
        
        return {
            'dates': dates,
            'executions': executions,
            'success_rates': success_rates
        }
    
    def refresh(self):
        """刷新统计数据"""
        self.load_statistics()