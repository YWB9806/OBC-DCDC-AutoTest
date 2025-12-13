"""示例分析器插件

演示如何创建一个数据分析插件。
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import statistics

from AppCode.interfaces.i_plugin import IAnalyzerPlugin


class ExampleAnalyzerPlugin(IAnalyzerPlugin):
    """示例分析器插件"""
    
    def __init__(self):
        """初始化插件"""
        self._context = None
        self._config = {
            'analysis_period_days': 7,
            'min_samples': 5,
            'include_trends': True
        }
    
    def get_name(self) -> str:
        """获取插件名称"""
        return "ExampleAnalyzerPlugin"
    
    def get_version(self) -> str:
        """获取插件版本"""
        return "1.0.0"
    
    def get_description(self) -> str:
        """获取插件描述"""
        return "示例数据分析插件，提供执行结果的统计分析功能"
    
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
                - data: 要分析的数据
            
        Returns:
            分析结果
        """
        data = kwargs.get('data', [])
        
        if not data:
            return {'error': 'No data provided'}
        
        # 执行分析
        analysis_result = self.analyze_data(data)
        
        return analysis_result
    
    def cleanup(self):
        """清理插件资源"""
        print(f"[{self.get_name()}] Plugin cleaned up")
    
    def get_config_schema(self) -> Dict[str, Any]:
        """获取配置模式
        
        Returns:
            配置模式
        """
        return {
            'analysis_period_days': 'int - 分析周期（天）',
            'min_samples': 'int - 最小样本数',
            'include_trends': 'boolean - 是否包含趋势分析'
        }
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置
        
        Args:
            config: 新配置
        """
        self._config.update(config)
        print(f"[{self.get_name()}] Config updated: {self._config}")
    
    def analyze_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析数据
        
        Args:
            data: 要分析的数据列表
            
        Returns:
            分析结果
        """
        if len(data) < self._config['min_samples']:
            return {
                'error': f"Insufficient data (minimum {self._config['min_samples']} samples required)",
                'sample_count': len(data)
            }
        
        # 基础统计
        basic_stats = self._calculate_basic_stats(data)
        
        # 趋势分析
        trends = None
        if self._config['include_trends']:
            trends = self._analyze_trends(data)
        
        # 异常检测
        anomalies = self._detect_anomalies(data)
        
        return {
            'basic_statistics': basic_stats,
            'trends': trends,
            'anomalies': anomalies,
            'sample_count': len(data),
            'analysis_time': datetime.now().isoformat()
        }
    
    def _calculate_basic_stats(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算基础统计信息"""
        # 提取数值数据
        durations = [item.get('duration', 0) for item in data if 'duration' in item]
        success_count = sum(1 for item in data if item.get('status') == 'success')
        
        stats = {
            'total_count': len(data),
            'success_count': success_count,
            'failure_count': len(data) - success_count,
            'success_rate': (success_count / len(data) * 100) if data else 0
        }
        
        if durations:
            stats.update({
                'avg_duration': statistics.mean(durations),
                'median_duration': statistics.median(durations),
                'min_duration': min(durations),
                'max_duration': max(durations),
                'std_duration': statistics.stdev(durations) if len(durations) > 1 else 0
            })
        
        return stats
    
    def _analyze_trends(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析趋势"""
        if len(data) < 2:
            return {'trend': 'insufficient_data'}
        
        # 按时间排序
        sorted_data = sorted(data, key=lambda x: x.get('timestamp', ''))
        
        # 计算成功率趋势
        half_point = len(sorted_data) // 2
        first_half = sorted_data[:half_point]
        second_half = sorted_data[half_point:]
        
        first_success_rate = sum(1 for item in first_half if item.get('status') == 'success') / len(first_half) * 100
        second_success_rate = sum(1 for item in second_half if item.get('status') == 'success') / len(second_half) * 100
        
        trend_direction = 'improving' if second_success_rate > first_success_rate else 'declining' if second_success_rate < first_success_rate else 'stable'
        
        return {
            'success_rate_trend': trend_direction,
            'first_period_success_rate': first_success_rate,
            'second_period_success_rate': second_success_rate,
            'change_percentage': second_success_rate - first_success_rate
        }
    
    def _detect_anomalies(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """检测异常"""
        anomalies = []
        
        # 提取执行时间
        durations = [item.get('duration', 0) for item in data if 'duration' in item]
        
        if len(durations) < 3:
            return anomalies
        
        # 计算平均值和标准差
        mean_duration = statistics.mean(durations)
        std_duration = statistics.stdev(durations)
        
        # 检测异常值（超过2个标准差）
        threshold = 2 * std_duration
        
        for item in data:
            duration = item.get('duration', 0)
            if abs(duration - mean_duration) > threshold:
                anomalies.append({
                    'item': item.get('name', 'Unknown'),
                    'duration': duration,
                    'expected_range': f"{mean_duration - threshold:.2f} - {mean_duration + threshold:.2f}",
                    'deviation': abs(duration - mean_duration)
                })
        
        return anomalies
    
    def get_supported_data_types(self) -> List[str]:
        """获取支持的数据类型
        
        Returns:
            支持的数据类型列表
        """
        return ['execution_results', 'performance_metrics', 'test_results']
    
    def generate_insights(self, analysis_result: Dict[str, Any]) -> List[str]:
        """生成洞察建议
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            洞察建议列表
        """
        insights = []
        
        # 基于统计数据生成建议
        stats = analysis_result.get('basic_statistics', {})
        
        success_rate = stats.get('success_rate', 0)
        if success_rate < 80:
            insights.append(f"成功率较低({success_rate:.1f}%)，建议检查失败原因")
        elif success_rate > 95:
            insights.append(f"成功率优秀({success_rate:.1f}%)，系统运行稳定")
        
        # 基于趋势生成建议
        trends = analysis_result.get('trends')
        if trends:
            trend = trends.get('success_rate_trend')
            if trend == 'declining':
                insights.append("成功率呈下降趋势，需要关注")
            elif trend == 'improving':
                insights.append("成功率呈上升趋势，优化措施有效")
        
        # 基于异常生成建议
        anomalies = analysis_result.get('anomalies', [])
        if len(anomalies) > 0:
            insights.append(f"检测到{len(anomalies)}个异常执行，建议详细检查")
        
        return insights