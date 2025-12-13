"""结果分析器接口

定义结果分析的核心接口。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class IResultAnalyzer(ABC):
    """结果分析器接口
    
    负责执行结果的分析和统计。
    """
    
    @abstractmethod
    def analyze_execution(self, execution_id: int) -> Dict[str, Any]:
        """分析单次执行结果
        
        Args:
            execution_id: 执行ID
            
        Returns:
            分析结果字典
        """
        pass
    
    @abstractmethod
    def analyze_batch(self, batch_id: int) -> Dict[str, Any]:
        """分析批次执行结果
        
        Args:
            batch_id: 批次ID
            
        Returns:
            分析结果字典
        """
        pass
    
    @abstractmethod
    def get_statistics(self, start_date: str = None, 
                      end_date: str = None) -> Dict[str, Any]:
        """获取统计信息
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    def get_trend_analysis(self, days: int = 7) -> Dict[str, Any]:
        """获取趋势分析
        
        Args:
            days: 天数
            
        Returns:
            趋势分析结果
        """
        pass
    
    @abstractmethod
    def generate_report(self, report_type: str, **kwargs) -> str:
        """生成报告
        
        Args:
            report_type: 报告类型
            **kwargs: 报告参数
            
        Returns:
            报告内容或文件路径
        """
        pass
    
    @abstractmethod
    def export_results(self, format: str, data: List[Dict[str, Any]], 
                      output_path: str):
        """导出结果
        
        Args:
            format: 导出格式（csv/excel/json）
            data: 数据列表
            output_path: 输出路径
        """
        pass