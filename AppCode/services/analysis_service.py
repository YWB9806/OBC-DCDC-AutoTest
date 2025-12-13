"""分析服务

提供结果分析和报告生成相关的业务逻辑。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from AppCode.core.result_analyzer import ResultAnalyzer
from AppCode.repositories.execution_history_repository import ExecutionHistoryRepository
from AppCode.repositories.batch_execution_repository import BatchExecutionRepository


class AnalysisService:
    """分析服务"""
    
    def __init__(
        self,
        result_analyzer: ResultAnalyzer,
        execution_repo: ExecutionHistoryRepository,
        batch_repo: BatchExecutionRepository,
        logger=None
    ):
        """初始化分析服务
        
        Args:
            result_analyzer: 结果分析器
            execution_repo: 执行历史仓储
            batch_repo: 批次执行仓储
            logger: 日志记录器
        """
        self.analyzer = result_analyzer
        self.execution_repo = execution_repo
        self.batch_repo = batch_repo
        self.logger = logger
    
    def analyze_execution(self, execution_id: str) -> Dict[str, Any]:
        """分析单次执行
        
        Args:
            execution_id: 执行ID
            
        Returns:
            分析结果
        """
        try:
            analysis = self.analyzer.analyze_execution_result(execution_id)
            
            if self.logger:
                self.logger.info(f"Analyzed execution: {execution_id}")
            
            return {
                'success': True,
                'analysis': analysis
            }
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to analyze execution: {e}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_batch(self, batch_id: str) -> Dict[str, Any]:
        """分析批次执行
        
        Args:
            batch_id: 批次ID
            
        Returns:
            分析结果
        """
        try:
            analysis = self.analyzer.analyze_batch_result(batch_id)
            
            if self.logger:
                self.logger.info(f"Analyzed batch: {batch_id}")
            
            return {
                'success': True,
                'analysis': analysis
            }
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to analyze batch: {e}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_overall_statistics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取总体统计信息
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            统计信息
        """
        try:
            # 如果没有指定日期，默认最近30天
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).isoformat()
            if not end_date:
                end_date = datetime.now().isoformat()
            
            stats = self.analyzer.get_statistics(start_date, end_date)
            
            # 添加额外的统计信息
            stats['execution_repo_stats'] = self.execution_repo.get_statistics()
            stats['batch_repo_stats'] = self.batch_repo.get_statistics()
            
            return {
                'success': True,
                'statistics': stats
            }
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get statistics: {e}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_report(
        self,
        report_type: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """生成报告
        
        Args:
            report_type: 报告类型 (summary/detailed/trend)
            params: 报告参数
            
        Returns:
            报告内容
        """
        try:
            params = params or {}
            
            # 设置默认日期范围
            if 'start_date' not in params:
                params['start_date'] = (datetime.now() - timedelta(days=7)).isoformat()
            if 'end_date' not in params:
                params['end_date'] = datetime.now().isoformat()
            
            report_content = self.analyzer.generate_report(report_type, params)
            
            if self.logger:
                self.logger.info(f"Generated {report_type} report")
            
            return {
                'success': True,
                'report_type': report_type,
                'content': report_content,
                'generated_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to generate report: {e}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def compare_executions(
        self,
        execution_id1: str,
        execution_id2: str
    ) -> Dict[str, Any]:
        """比较两次执行
        
        Args:
            execution_id1: 第一个执行ID
            execution_id2: 第二个执行ID
            
        Returns:
            比较结果
        """
        try:
            comparison = self.analyzer.compare_results(execution_id1, execution_id2)
            
            return {
                'success': True,
                'comparison': comparison
            }
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to compare executions: {e}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_performance_metrics(
        self,
        script_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取性能指标
        
        Args:
            script_path: 脚本路径（可选）
            
        Returns:
            性能指标
        """
        try:
            if script_path:
                executions = self.execution_repo.get_by_script(script_path)
            else:
                executions = self.execution_repo.get_all()
            
            if not executions:
                return {
                    'success': True,
                    'metrics': {
                        'total_executions': 0,
                        'average_duration': 0,
                        'min_duration': 0,
                        'max_duration': 0
                    }
                }
            
            durations = []
            for execution in executions:
                if execution.get('start_time') and execution.get('end_time'):
                    start = datetime.fromisoformat(execution['start_time'])
                    end = datetime.fromisoformat(execution['end_time'])
                    duration = (end - start).total_seconds()
                    durations.append(duration)
            
            metrics = {
                'total_executions': len(executions),
                'average_duration': sum(durations) / len(durations) if durations else 0,
                'min_duration': min(durations) if durations else 0,
                'max_duration': max(durations) if durations else 0,
                'total_duration': sum(durations) if durations else 0
            }
            
            return {
                'success': True,
                'metrics': metrics
            }
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get performance metrics: {e}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_failure_analysis(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取失败分析
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            失败分析
        """
        try:
            # 获取失败的执行
            if start_date and end_date:
                all_executions = self.execution_repo.get_by_date_range(start_date, end_date)
            else:
                all_executions = self.execution_repo.get_all()
            
            failed_executions = [
                e for e in all_executions
                if e.get('status') == 'failed'
            ]
            
            # 分析失败原因
            error_types = {}
            failed_scripts = {}
            
            for execution in failed_executions:
                error = execution.get('error', 'Unknown error')
                error_types[error] = error_types.get(error, 0) + 1
                
                script = execution.get('script_path', 'Unknown')
                failed_scripts[script] = failed_scripts.get(script, 0) + 1
            
            # 排序
            top_errors = sorted(
                error_types.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            top_failed_scripts = sorted(
                failed_scripts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            analysis = {
                'total_failures': len(failed_executions),
                'failure_rate': (
                    len(failed_executions) / len(all_executions) * 100
                    if all_executions else 0
                ),
                'top_errors': top_errors,
                'top_failed_scripts': top_failed_scripts
            }
            
            return {
                'success': True,
                'analysis': analysis
            }
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to analyze failures: {e}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_trend_analysis(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取趋势分析
        
        Args:
            days: 分析天数
            
        Returns:
            趋势分析
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            executions = self.execution_repo.get_by_date_range(
                start_date.isoformat(),
                end_date.isoformat()
            )
            
            # 按日期分组
            daily_stats = {}
            
            for execution in executions:
                if execution.get('start_time'):
                    date = execution['start_time'][:10]  # YYYY-MM-DD
                    
                    if date not in daily_stats:
                        daily_stats[date] = {
                            'total': 0,
                            'successful': 0,
                            'failed': 0
                        }
                    
                    daily_stats[date]['total'] += 1
                    
                    if execution.get('status') == 'success':
                        daily_stats[date]['successful'] += 1
                    elif execution.get('status') == 'failed':
                        daily_stats[date]['failed'] += 1
            
            # 计算每日成功率
            for date, stats in daily_stats.items():
                if stats['total'] > 0:
                    stats['success_rate'] = (
                        stats['successful'] / stats['total'] * 100
                    )
                else:
                    stats['success_rate'] = 0
            
            return {
                'success': True,
                'trend': {
                    'period': f'{days} days',
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'daily_stats': daily_stats
                }
            }
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to analyze trend: {e}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def export_report(
        self,
        report_type: str,
        format: str = 'txt',
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """导出报告
        
        Args:
            report_type: 报告类型
            format: 导出格式 (txt/json/csv)
            params: 报告参数
            
        Returns:
            导出结果
        """
        try:
            # 生成报告
            report_result = self.generate_report(report_type, params)
            
            if not report_result['success']:
                return report_result
            
            # 根据格式导出
            if format == 'txt':
                content = report_result['content']
            elif format == 'json':
                import json
                content = json.dumps(report_result, indent=2, ensure_ascii=False)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported format: {format}'
                }
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'report_{report_type}_{timestamp}.{format}'
            
            return {
                'success': True,
                'filename': filename,
                'content': content,
                'format': format
            }
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to export report: {e}")
            
            return {
                'success': False,
                'error': str(e)
            }