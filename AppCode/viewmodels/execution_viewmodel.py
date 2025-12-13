"""执行视图模型

管理脚本执行相关的UI数据和操作。
"""

from typing import List, Dict, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QTimer


class ExecutionViewModel(QObject):
    """执行视图模型"""
    
    # 信号定义
    execution_started = pyqtSignal(str)      # 执行开始 (execution_id)
    execution_progress = pyqtSignal(str, int)  # 执行进度 (execution_id, progress)
    execution_finished = pyqtSignal(str, dict)  # 执行完成 (execution_id, result)
    execution_output = pyqtSignal(str, str)   # 执行输出 (execution_id, output)
    error_occurred = pyqtSignal(str)         # 错误发生
    
    def __init__(self, container):
        """初始化执行视图模型
        
        Args:
            container: 依赖注入容器
        """
        super().__init__()
        
        self.container = container
        self.logger = container.resolve('log_manager').get_logger('viewmodel')
        self.execution_service = container.resolve('execution_service')
        
        self._executions = {}  # execution_id -> execution_info
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_executions)
        self._update_timer.start(1000)  # 每秒更新一次
    
    def execute_script(self, script_path: str, config: Dict = None) -> Optional[str]:
        """执行单个脚本
        
        Args:
            script_path: 脚本路径
            config: 执行配置
            
        Returns:
            执行ID，失败返回None
        """
        try:
            result = self.execution_service.execute_script(script_path, config)
            
            if result['success']:
                execution_id = result['execution_id']
                self._executions[execution_id] = {
                    'id': execution_id,
                    'script': script_path,
                    'status': 'running',
                    'progress': 0,
                    'output': []
                }
                self.execution_started.emit(execution_id)
                self.logger.info(f"Started execution: {execution_id}")
                return execution_id
            else:
                error = result.get('error', 'Unknown error')
                self.error_occurred.emit(f"执行失败: {error}")
                self.logger.error(f"Failed to execute script: {error}")
                return None
        
        except Exception as e:
            self.logger.error(f"Error executing script: {e}")
            self.error_occurred.emit(f"执行脚本时出错: {e}")
            return None
    
    def execute_batch(self, script_paths: List[str], config: Dict = None) -> Optional[str]:
        """批量执行脚本
        
        Args:
            script_paths: 脚本路径列表
            config: 执行配置
            
        Returns:
            批次ID，失败返回None
        """
        try:
            result = self.execution_service.execute_batch(script_paths, config)
            
            if result['success']:
                batch_id = result['batch_id']
                self.logger.info(f"Started batch execution: {batch_id}")
                
                # 为批次中的每个脚本创建执行记录
                for execution_id in result.get('execution_ids', []):
                    self._executions[execution_id] = {
                        'id': execution_id,
                        'batch_id': batch_id,
                        'status': 'running',
                        'progress': 0,
                        'output': []
                    }
                    self.execution_started.emit(execution_id)
                
                return batch_id
            else:
                error = result.get('error', 'Unknown error')
                self.error_occurred.emit(f"批量执行失败: {error}")
                self.logger.error(f"Failed to execute batch: {error}")
                return None
        
        except Exception as e:
            self.logger.error(f"Error executing batch: {e}")
            self.error_occurred.emit(f"批量执行时出错: {e}")
            return None
    
    def stop_execution(self, execution_id: str) -> bool:
        """停止执行
        
        Args:
            execution_id: 执行ID
            
        Returns:
            是否成功
        """
        try:
            result = self.execution_service.stop_execution(execution_id)
            
            if result['success']:
                if execution_id in self._executions:
                    self._executions[execution_id]['status'] = 'stopped'
                self.logger.info(f"Stopped execution: {execution_id}")
                return True
            else:
                error = result.get('error', 'Unknown error')
                self.error_occurred.emit(f"停止执行失败: {error}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error stopping execution: {e}")
            self.error_occurred.emit(f"停止执行时出错: {e}")
            return False
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict]:
        """获取执行状态
        
        Args:
            execution_id: 执行ID
            
        Returns:
            执行状态信息
        """
        try:
            result = self.execution_service.get_execution_status(execution_id)
            
            if result['success']:
                return result['status']
            else:
                return None
        
        except Exception as e:
            self.logger.error(f"Error getting execution status: {e}")
            return None
    
    def get_execution_output(self, execution_id: str) -> List[str]:
        """获取执行输出
        
        Args:
            execution_id: 执行ID
            
        Returns:
            输出行列表
        """
        try:
            result = self.execution_service.get_execution_output(execution_id)
            
            if result['success']:
                return result['output']
            else:
                return []
        
        except Exception as e:
            self.logger.error(f"Error getting execution output: {e}")
            return []
    
    def get_active_executions(self) -> List[Dict]:
        """获取活动的执行
        
        Returns:
            活动执行列表
        """
        return [
            exec_info for exec_info in self._executions.values()
            if exec_info['status'] in ['running', 'pending']
        ]
    
    def get_all_executions(self) -> List[Dict]:
        """获取所有执行
        
        Returns:
            所有执行列表
        """
        return list(self._executions.values())
    
    def clear_finished_executions(self):
        """清除已完成的执行"""
        finished_ids = [
            exec_id for exec_id, exec_info in self._executions.items()
            if exec_info['status'] in ['completed', 'failed', 'stopped']
        ]
        
        for exec_id in finished_ids:
            del self._executions[exec_id]
        
        self.logger.info(f"Cleared {len(finished_ids)} finished executions")
    
    def _update_executions(self):
        """更新执行状态（定时器回调）"""
        for execution_id in list(self._executions.keys()):
            try:
                status = self.get_execution_status(execution_id)
                
                if status:
                    exec_info = self._executions[execution_id]
                    old_status = exec_info['status']
                    new_status = status.get('status', 'unknown')
                    
                    # 更新状态
                    exec_info['status'] = new_status
                    exec_info['progress'] = status.get('progress', 0)
                    
                    # 发送进度信号
                    self.execution_progress.emit(
                        execution_id,
                        exec_info['progress']
                    )
                    
                    # 获取新输出
                    output = self.get_execution_output(execution_id)
                    if output and len(output) > len(exec_info['output']):
                        new_lines = output[len(exec_info['output']):]
                        exec_info['output'] = output
                        for line in new_lines:
                            self.execution_output.emit(execution_id, line)
                    
                    # 如果状态变为完成，发送完成信号
                    if old_status == 'running' and new_status in ['completed', 'failed', 'stopped']:
                        result = {
                            'status': new_status,
                            'output': exec_info['output']
                        }
                        self.execution_finished.emit(execution_id, result)
            
            except Exception as e:
                self.logger.error(f"Error updating execution {execution_id}: {e}")