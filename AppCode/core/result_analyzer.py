"""结果分析器实现

负责执行结果的分析、统计和报告生成。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from AppCode.interfaces.i_result_analyzer import IResultAnalyzer
from AppCode.utils.constants import ExecutionStatus


class ResultAnalyzer(IResultAnalyzer):
    """结果分析器实现"""
    
    def __init__(self, logger=None, data_access=None):
        """初始化结果分析器
        
        Args:
            logger: 日志记录器
            data_access: 数据访问层
        """
        self.logger = logger
        self.data_access = data_access
    
    def analyze_execution_result(self, execution_id: str) -> Dict[str, Any]:
        """分析单次执行结果
        
        Args:
            execution_id: 执行ID
            
        Returns:
            分析结果
        """
        if not self.data_access:
            return {'error': 'Data access not available'}
        
        # 获取执行记录
        execution = self.data_access.get_by_id('execution_history', execution_id)
        if not execution:
            return {'error': 'Execution not found'}
        
        analysis = {
            'execution_id': execution_id,
            'script_path': execution.get('script_path'),
            'status': execution.get('status'),
            'start_time': execution.get('start_time'),
            'end_time': execution.get('end_time'),
            'duration': None,
            'success': execution.get('status') == ExecutionStatus.SUCCESS,
            'output_lines': 0,
            'error_count': 0,
            'warning_count': 0
        }
        
        # 计算执行时长
        if execution.get('start_time') and execution.get('end_time'):
            start = datetime.fromisoformat(execution['start_time'])
            end = datetime.fromisoformat(execution['end_time'])
            duration = (end - start).total_seconds()
            analysis['duration'] = duration
        
        # 分析输出
        output = execution.get('output', '')
        if output:
            lines = output.split('\n')
            analysis['output_lines'] = len(lines)
            
            # 统计错误和警告
            for line in lines:
                line_lower = line.lower()
                if 'error' in line_lower or 'exception' in line_lower:
                    analysis['error_count'] += 1
                elif 'warning' in line_lower:
                    analysis['warning_count'] += 1
        
        if self.logger:
            self.logger.info(f"Analyzed execution: {execution_id}")
        
        return analysis
    
    def analyze_batch_result(self, batch_id: str) -> Dict[str, Any]:
        """分析批次执行结果
        
        Args:
            batch_id: 批次ID
            
        Returns:
            批次分析结果
        """
        if not self.data_access:
            return {'error': 'Data access not available'}
        
        # 获取批次记录
        batch = self.data_access.get_by_id('batch_executions', batch_id)
        if not batch:
            return {'error': 'Batch not found'}
        
        # 获取批次中的所有执行
        executions = self.data_access.query(
            'execution_history',
            {'batch_id': batch_id}
        )
        
        analysis = {
            'batch_id': batch_id,
            'total_scripts': len(executions),
            'successful': 0,
            'failed': 0,
            'cancelled': 0,
            'total_duration': 0,
            'average_duration': 0,
            'start_time': batch.get('start_time'),
            'end_time': batch.get('end_time'),
            'scripts': []
        }
        
        durations = []
        
        for execution in executions:
            status = execution.get('status')
            
            if status == ExecutionStatus.SUCCESS:
                analysis['successful'] += 1
            elif status == ExecutionStatus.FAILED:
                analysis['failed'] += 1
            elif status == ExecutionStatus.CANCELLED:
                analysis['cancelled'] += 1
            
            # 计算时长
            if execution.get('start_time') and execution.get('end_time'):
                start = datetime.fromisoformat(execution['start_time'])
                end = datetime.fromisoformat(execution['end_time'])
                duration = (end - start).total_seconds()
                durations.append(duration)
                analysis['total_duration'] += duration
            
            # 添加脚本信息
            analysis['scripts'].append({
                'script_path': execution.get('script_path'),
                'status': status,
                'duration': durations[-1] if durations else None
            })
        
        # 计算平均时长
        if durations:
            analysis['average_duration'] = sum(durations) / len(durations)
        
        # 计算成功率
        if analysis['total_scripts'] > 0:
            analysis['success_rate'] = (
                analysis['successful'] / analysis['total_scripts'] * 100
            )
        else:
            analysis['success_rate'] = 0
        
        if self.logger:
            self.logger.info(f"Analyzed batch: {batch_id}")
        
        return analysis
    
    def get_statistics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取统计信息
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            统计信息
        """
        if not self.data_access:
            return {'error': 'Data access not available'}
        
        # 构建查询条件
        conditions = {}
        if start_date:
            conditions['start_time>='] = start_date
        if end_date:
            conditions['start_time<='] = end_date
        
        # 查询执行记录
        executions = self.data_access.query('execution_history', conditions)
        
        stats = {
            'total_executions': len(executions),
            'successful': 0,
            'failed': 0,
            'cancelled': 0,
            'total_duration': 0,
            'average_duration': 0,
            'scripts_by_status': defaultdict(int),
            'scripts_by_category': defaultdict(int),
            'daily_executions': defaultdict(int),
            'top_scripts': []
        }
        
        durations = []
        script_counts = defaultdict(int)
        
        for execution in executions:
            status = execution.get('status')
            
            # 统计状态
            if status == ExecutionStatus.SUCCESS:
                stats['successful'] += 1
            elif status == ExecutionStatus.FAILED:
                stats['failed'] += 1
            elif status == ExecutionStatus.CANCELLED:
                stats['cancelled'] += 1
            
            stats['scripts_by_status'][status] += 1
            
            # 统计时长
            if execution.get('start_time') and execution.get('end_time'):
                start = datetime.fromisoformat(execution['start_time'])
                end = datetime.fromisoformat(execution['end_time'])
                duration = (end - start).total_seconds()
                durations.append(duration)
                stats['total_duration'] += duration
                
                # 按日期统计
                date_key = start.strftime('%Y-%m-%d')
                stats['daily_executions'][date_key] += 1
            
            # 统计脚本
            script_path = execution.get('script_path', '')
            script_counts[script_path] += 1
        
        # 计算平均时长
        if durations:
            stats['average_duration'] = sum(durations) / len(durations)
        
        # 计算成功率
        if stats['total_executions'] > 0:
            stats['success_rate'] = (
                stats['successful'] / stats['total_executions'] * 100
            )
        else:
            stats['success_rate'] = 0
        
        # 获取最常执行的脚本
        stats['top_scripts'] = sorted(
            script_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # 转换defaultdict为普通dict
        stats['scripts_by_status'] = dict(stats['scripts_by_status'])
        stats['scripts_by_category'] = dict(stats['scripts_by_category'])
        stats['daily_executions'] = dict(stats['daily_executions'])
        
        if self.logger:
            self.logger.info(f"Generated statistics for {stats['total_executions']} executions")
        
        return stats
    
    def generate_report(
        self,
        report_type: str,
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """生成报告
        
        Args:
            report_type: 报告类型 (summary/detailed/trend)
            params: 报告参数
            
        Returns:
            报告内容
        """
        params = params or {}
        
        if report_type == 'summary':
            return self._generate_summary_report(params)
        elif report_type == 'detailed':
            return self._generate_detailed_report(params)
        elif report_type == 'trend':
            return self._generate_trend_report(params)
        else:
            return f"Unknown report type: {report_type}"
    
    def _generate_summary_report(self, params: Dict[str, Any]) -> str:
        """生成摘要报告"""
        stats = self.get_statistics(
            params.get('start_date'),
            params.get('end_date')
        )
        
        report = []
        report.append("=" * 60)
        report.append("执行摘要报告")
        report.append("=" * 60)
        report.append(f"总执行次数: {stats['total_executions']}")
        report.append(f"成功: {stats['successful']}")
        report.append(f"失败: {stats['failed']}")
        report.append(f"取消: {stats['cancelled']}")
        report.append(f"成功率: {stats['success_rate']:.2f}%")
        report.append(f"总执行时长: {stats['total_duration']:.2f}秒")
        report.append(f"平均执行时长: {stats['average_duration']:.2f}秒")
        report.append("")
        report.append("最常执行的脚本:")
        for script, count in stats['top_scripts'][:5]:
            report.append(f"  {script}: {count}次")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def _generate_detailed_report(self, params: Dict[str, Any]) -> str:
        """生成详细报告"""
        if not self.data_access:
            return "数据访问不可用"
        
        conditions = {}
        if params.get('start_date'):
            conditions['start_time>='] = params['start_date']
        if params.get('end_date'):
            conditions['start_time<='] = params['end_date']
        
        executions = self.data_access.query('execution_history', conditions)
        
        report = []
        report.append("=" * 80)
        report.append("详细执行报告")
        report.append("=" * 80)
        
        for execution in executions:
            report.append(f"\n执行ID: {execution.get('id')}")
            report.append(f"脚本: {execution.get('script_path')}")
            report.append(f"状态: {execution.get('status')}")
            report.append(f"开始时间: {execution.get('start_time')}")
            report.append(f"结束时间: {execution.get('end_time')}")
            
            if execution.get('error'):
                report.append(f"错误: {execution.get('error')}")
            
            report.append("-" * 80)
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def _generate_trend_report(self, params: Dict[str, Any]) -> str:
        """生成趋势报告"""
        stats = self.get_statistics(
            params.get('start_date'),
            params.get('end_date')
        )
        
        report = []
        report.append("=" * 60)
        report.append("执行趋势报告")
        report.append("=" * 60)
        report.append("\n每日执行次数:")
        
        for date, count in sorted(stats['daily_executions'].items()):
            report.append(f"  {date}: {count}次")
        
        report.append("\n按状态分布:")
        for status, count in stats['scripts_by_status'].items():
            report.append(f"  {status}: {count}次")
        
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def compare_results(
        self,
        execution_id1: str,
        execution_id2: str
    ) -> Dict[str, Any]:
        """比较两次执行结果
        
        Args:
            execution_id1: 第一个执行ID
            execution_id2: 第二个执行ID
            
        Returns:
            比较结果
        """
        result1 = self.analyze_execution_result(execution_id1)
        result2 = self.analyze_execution_result(execution_id2)
        
        comparison = {
            'execution1': result1,
            'execution2': result2,
            'differences': {}
        }
        
        # 比较时长
        if result1.get('duration') and result2.get('duration'):
            duration_diff = result2['duration'] - result1['duration']
            comparison['differences']['duration'] = {
                'diff': duration_diff,
                'percentage': (duration_diff / result1['duration'] * 100) if result1['duration'] > 0 else 0
            }
        
        # 比较状态
        comparison['differences']['status_changed'] = (
            result1.get('status') != result2.get('status')
        )
        
        # 比较输出行数
        if result1.get('output_lines') and result2.get('output_lines'):
            comparison['differences']['output_lines_diff'] = (
                result2['output_lines'] - result1['output_lines']
            )
        
        return comparison
    
    def analyze_execution(self, execution_id: str) -> Dict[str, Any]:
        """分析执行结果（接口方法）
        
        Args:
            execution_id: 执行ID
            
        Returns:
            分析结果
        """
        return self.analyze_execution_result(execution_id)
    
    def analyze_batch(self, batch_id: str) -> Dict[str, Any]:
        """分析批次结果（接口方法）
        
        Args:
            batch_id: 批次ID
            
        Returns:
            分析结果
        """
        return self.analyze_batch_result(batch_id)
    
    def get_trend_analysis(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取趋势分析（接口方法）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            趋势分析
        """
        return self.get_statistics(start_date, end_date)
    
    def export_results(
        self,
        execution_ids: List[str],
        format: str = 'json'
    ) -> str:
        """导出结果（接口方法）
        
        Args:
            execution_ids: 执行ID列表
            format: 导出格式
            
        Returns:
            导出内容
        """
        results = []
        for exec_id in execution_ids:
            result = self.analyze_execution_result(exec_id)
            results.append(result)
        
        if format == 'json':
            import json
            return json.dumps(results, indent=2, ensure_ascii=False)
        else:
            # 简单文本格式
            lines = []
            for result in results:
                lines.append(f"Execution: {result.get('execution_id')}")
                lines.append(f"Status: {result.get('status')}")
                lines.append(f"Duration: {result.get('duration')}s")
                lines.append("-" * 40)
            return "\n".join(lines)