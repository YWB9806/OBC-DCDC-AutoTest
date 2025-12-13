"""执行服务

提供脚本执行相关的业务逻辑。
"""

from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import threading
import time
import random

from AppCode.core.execution_engine import ExecutionEngine
from AppCode.repositories.execution_history_repository import ExecutionHistoryRepository
from AppCode.repositories.batch_execution_repository import BatchExecutionRepository
from AppCode.utils.constants import ExecutionStatus


class ExecutionService:
    """执行服务"""
    
    def __init__(
        self,
        execution_engine: ExecutionEngine,
        execution_repo: ExecutionHistoryRepository,
        batch_repo: BatchExecutionRepository,
        logger=None
    ):
        """初始化执行服务
        
        Args:
            execution_engine: 执行引擎
            execution_repo: 执行历史仓储
            batch_repo: 批次执行仓储
            logger: 日志记录器
        """
        self.engine = execution_engine
        self.execution_repo = execution_repo
        self.batch_repo = batch_repo
        self.logger = logger
    
    def execute_single_script(
        self,
        script_path: str,
        params: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        suite_id: Optional[int] = None,
        suite_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """执行单个脚本
        
        Args:
            script_path: 脚本路径
            params: 执行参数
            user_id: 用户ID
            suite_id: 测试方案ID
            suite_name: 测试方案名称
            
        Returns:
            执行结果
        """
        if self.logger:
            self.logger.info(f"Executing script: {script_path}")
        
        try:
            # 创建执行回调
            def on_complete(execution_id, execution_info):
                self._save_execution_result(execution_id, execution_info, user_id, suite_id, suite_name)
            
            # 启动执行
            execution_id = self.engine.execute_script(
                script_path,
                params,
                callback=on_complete
            )
            
            # 创建执行记录
            self._create_execution_record(execution_id, script_path, params, user_id, suite_id, suite_name)
            
            return {
                'success': True,
                'execution_id': execution_id,
                'message': 'Script execution started'
            }
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to execute script: {e}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_batch_scripts(
        self,
        script_paths: List[str],
        params: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        suite_id: Optional[int] = None,
        suite_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """批量执行脚本
        
        Args:
            script_paths: 脚本路径列表
            params: 执行参数
            user_id: 用户ID
            suite_id: 测试方案ID
            suite_name: 测试方案名称
            
        Returns:
            执行结果
        """
        if self.logger:
            self.logger.info(f"Executing batch: {len(script_paths)} scripts, suite: {suite_name}")
        
        try:
            # 生成批次ID
            batch_id = self._generate_batch_id()
            
            # 创建批次记录
            self._create_batch_record(batch_id, script_paths, params, user_id, suite_id, suite_name)
            
            # 为每个脚本创建执行任务（关键修复：为每个脚本设置回调）
            execution_ids = []
            for script_path in script_paths:
                # 创建执行回调，传递suite和batch信息
                def on_complete(execution_id, execution_info, sp=script_path):
                    self._save_execution_result(
                        execution_id,
                        execution_info,
                        user_id,
                        suite_id,
                        suite_name,
                        batch_id
                    )
                    if self.logger:
                        self.logger.info(f"Saved execution result: {execution_id} for {sp}")
                
                # 启动执行（传递batch_id）
                exec_id = self.engine.execute_script(
                    script_path,
                    params,
                    callback=on_complete,
                    batch_id=batch_id
                )
                
                # 创建执行记录（包含batch_id）
                self._create_execution_record(
                    exec_id,
                    script_path,
                    params,
                    user_id,
                    suite_id,
                    suite_name,
                    batch_id
                )
                
                execution_ids.append(exec_id)
            
            # 创建批次监控回调
            def on_batch_complete(bid, batch_info):
                self._save_batch_result(bid, batch_info, user_id, suite_id, suite_name)
            
            # 更新批次信息
            batch_info = {
                'id': batch_id,
                'execution_ids': execution_ids,
                'status': ExecutionStatus.RUNNING,
                'start_time': datetime.now(),
                'callback': on_batch_complete
            }
            
            # 将批次信息存储到引擎中
            with self.engine._lock:
                self.engine._executions[batch_id] = batch_info
            
            # 启动批次监控线程
            monitor_thread = threading.Thread(
                target=self.engine._monitor_batch,
                args=(batch_id,),
                daemon=True
            )
            monitor_thread.start()
            
            return {
                'success': True,
                'batch_id': batch_id,
                'total_scripts': len(script_paths),
                'message': 'Batch execution started'
            }
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to execute batch: {e}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_execution(self, execution_id: str) -> Dict[str, Any]:
        """取消执行
        
        Args:
            execution_id: 执行ID
            
        Returns:
            操作结果
        """
        try:
            success = self.engine.cancel_execution(execution_id)
            
            if success:
                # 更新数据库记录
                self.execution_repo.update(execution_id, {
                    'status': ExecutionStatus.CANCELLED,
                    'end_time': datetime.now().isoformat()
                })
                
                return {
                    'success': True,
                    'message': 'Execution cancelled'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to cancel execution'
                }
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to cancel execution: {e}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def pause_execution(self, execution_id: str) -> Dict[str, Any]:
        """暂停执行
        
        Args:
            execution_id: 执行ID
            
        Returns:
            操作结果
        """
        try:
            success = self.engine.pause_execution(execution_id)
            
            if success:
                return {
                    'success': True,
                    'message': 'Execution paused'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to pause execution'
                }
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to pause execution: {e}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def resume_execution(self, execution_id: str) -> Dict[str, Any]:
        """恢复执行
        
        Args:
            execution_id: 执行ID
            
        Returns:
            操作结果
        """
        try:
            success = self.engine.resume_execution(execution_id)
            
            if success:
                return {
                    'success': True,
                    'message': 'Execution resumed'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to resume execution'
                }
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to resume execution: {e}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """获取执行状态
        
        Args:
            execution_id: 执行ID
            
        Returns:
            执行状态
        """
        # 先从引擎获取实时状态
        engine_status = self.engine.get_execution_status(execution_id)
        
        # 如果引擎返回None或状态为UNKNOWN，从数据库获取
        if engine_status is None or engine_status.get('status') == ExecutionStatus.UNKNOWN:
            db_record = self.execution_repo.get_by_id(execution_id)
            if db_record:
                return db_record
            # 如果数据库也没有，返回默认状态
            return {'status': ExecutionStatus.UNKNOWN}
        
        return engine_status
    
    def get_execution_output(self, execution_id: str) -> List[str]:
        """获取执行输出
        
        Args:
            execution_id: 执行ID
            
        Returns:
            输出行列表
        """
        # 先从引擎获取
        output = self.engine.get_execution_output(execution_id)
        
        # 如果引擎中没有，从数据库获取
        if not output:
            db_record = self.execution_repo.get_by_id(execution_id)
            if db_record and db_record.get('output'):
                output = db_record['output'].split('\n')
        
        return output
    
    def get_recent_executions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的执行记录
        
        Args:
            limit: 返回数量限制
            
        Returns:
            执行记录列表
        """
        return self.execution_repo.get_recent(limit)
    
    def get_execution_history(
        self,
        script_path: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        suite_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取执行历史
        
        Args:
            script_path: 脚本路径
            status: 执行状态
            start_date: 开始日期
            end_date: 结束日期
            suite_id: 测试方案ID
            
        Returns:
            执行历史列表
        """
        # 获取基础结果
        if script_path:
            results = self.execution_repo.get_by_script(script_path)
        elif start_date and end_date:
            results = self.execution_repo.get_by_date_range(start_date, end_date)
        else:
            results = self.execution_repo.get_recent(100)
        
        # 应用状态过滤
        if status:
            results = [r for r in results if r.get('status') == status]
        
        # 应用方案过滤
        if suite_id:
            results = [r for r in results if r.get('suite_id') == suite_id]
        
        return results
    
    def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """获取批次状态（优化版 - 减少数据库查询）
        
        Args:
            batch_id: 批次ID
            
        Returns:
            批次状态
        """
        # 从引擎获取实时状态
        engine_status = self.engine.get_execution_status(batch_id)
        
        # 如果引擎中没有，从数据库获取
        if engine_status.get('status') == ExecutionStatus.UNKNOWN:
            db_record = self.batch_repo.get_by_id(batch_id)
            if db_record:
                return db_record
        
        # 获取批次中的所有执行（优化：直接从引擎获取，避免数据库查询）
        if 'execution_ids' in engine_status:
            executions = []
            for exec_id in engine_status['execution_ids']:
                # 直接从引擎获取状态，不查询数据库
                exec_status = self.engine.get_execution_status(exec_id)
                if exec_status and exec_status.get('status') != ExecutionStatus.UNKNOWN:
                    executions.append(exec_status)
            
            engine_status['executions'] = executions
        
        return engine_status
    
    def retry_failed_execution(self, execution_id: str) -> Dict[str, Any]:
        """重试失败的执行
        
        Args:
            execution_id: 执行ID
            
        Returns:
            新的执行结果
        """
        # 获取原执行记录
        original = self.execution_repo.get_by_id(execution_id)
        if not original:
            return {
                'success': False,
                'error': 'Execution not found'
            }
        
        # 重新执行
        return self.execute_single_script(
            original['script_path'],
            original.get('params'),
            original.get('user_id')
        )
    
    def _generate_batch_id(self) -> str:
        """生成批次ID"""
        timestamp = int(time.time() * 1000000)
        random_part = random.randint(10000, 99999)
        return f"batch_{timestamp}_{random_part}"
    
    def _create_execution_record(
        self,
        execution_id: str,
        script_path: str,
        params: Optional[Dict[str, Any]],
        user_id: Optional[str],
        suite_id: Optional[int] = None,
        suite_name: Optional[str] = None,
        batch_id: Optional[str] = None
    ):
        """创建执行记录"""
        record = {
            'id': execution_id,
            'script_path': script_path,
            'params': str(params) if params else None,
            'user_id': user_id,
            'suite_id': suite_id,
            'suite_name': suite_name,
            'batch_id': batch_id,
            'status': ExecutionStatus.PENDING,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'output': None,
            'error': None,
            'test_result': 'pending'
        }
        
        self.execution_repo.create(record)
        
        if self.logger:
            self.logger.info(f"Created execution record: {execution_id}, batch: {batch_id}, suite: {suite_name}")
    
    def _create_batch_record(
        self,
        batch_id: str,
        script_paths: List[str],
        params: Optional[Dict[str, Any]],
        user_id: Optional[str],
        suite_id: Optional[int] = None,
        suite_name: Optional[str] = None
    ):
        """创建批次记录"""
        record = {
            'id': batch_id,
            'name': suite_name if suite_name else f"Batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'total_scripts': len(script_paths),
            'completed_scripts': 0,
            'successful_scripts': 0,
            'failed_scripts': 0,
            'pending_scripts': len(script_paths),
            'error_scripts': 0,
            'timeout_scripts': 0,
            'status': ExecutionStatus.RUNNING,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'user_id': user_id,
            'suite_id': suite_id,
            'suite_name': suite_name,
            'params': str(params) if params else None
        }
        
        self.batch_repo.create(record)
        
        if self.logger:
            self.logger.info(f"Created batch record: {batch_id}, suite: {suite_name}")
    
    def _save_execution_result(
        self,
        execution_id: str,
        execution_info: Dict[str, Any],
        user_id: Optional[str],
        suite_id: Optional[int] = None,
        suite_name: Optional[str] = None,
        batch_id: Optional[str] = None
    ):
        """保存执行结果"""
        # 确保时间格式正确
        end_time = execution_info.get('end_time')
        if isinstance(end_time, datetime):
            end_time = end_time.isoformat()
        
        update_data = {
            'status': execution_info.get('status'),
            'end_time': end_time,
            'output': '\n'.join(execution_info.get('output', [])),
            'error': execution_info.get('error'),
            'test_result': execution_info.get('test_result', 'pending'),
            'suite_id': suite_id,
            'suite_name': suite_name,
            'batch_id': batch_id
        }
        
        self.execution_repo.update(execution_id, update_data)
        
        if self.logger:
            self.logger.info(
                f"Execution result saved: {execution_id} - "
                f"status: {update_data['status']}, "
                f"test_result: {update_data['test_result']}, "
                f"suite: {suite_name}, "
                f"batch: {batch_id}"
            )
    
    def _save_batch_result(
        self,
        batch_id: str,
        batch_info: Dict[str, Any],
        user_id: Optional[str],
        suite_id: Optional[int] = None,
        suite_name: Optional[str] = None
    ):
        """保存批次结果
        
        Args:
            batch_id: 批次ID
            batch_info: 批次信息
            user_id: 用户ID
            suite_id: 测试方案ID
            suite_name: 测试方案名称
        """
        # 统计批次中的执行结果
        execution_ids = batch_info.get('execution_ids', [])
        successful = 0
        failed = 0
        pending = 0
        error = 0
        timeout = 0
        
        # 等待所有执行记录保存完成
        max_wait = 10  # 最多等待10秒
        wait_count = 0
        while wait_count < max_wait * 10:  # 每次等待0.1秒
            all_saved = True
            for exec_id in execution_ids:
                exec_record = self.execution_repo.get_by_id(exec_id)
                if not exec_record or exec_record.get('end_time') is None:
                    all_saved = False
                    break
            
            if all_saved:
                if self.logger:
                    self.logger.info(f"All execution records saved for batch: {batch_id}")
                break
            
            time.sleep(0.1)
            wait_count += 1
        
        # 统计结果
        for exec_id in execution_ids:
            exec_record = self.execution_repo.get_by_id(exec_id)
            if exec_record:
                status = exec_record.get('status')
                if status == ExecutionStatus.SUCCESS:
                    successful += 1
                elif status == ExecutionStatus.FAILED:
                    failed += 1
                elif status == ExecutionStatus.PENDING:
                    pending += 1
                elif status == ExecutionStatus.ERROR:
                    error += 1
                elif status == ExecutionStatus.TIMEOUT:
                    timeout += 1
        
        # 确保时间格式正确
        end_time = batch_info.get('end_time')
        if isinstance(end_time, datetime):
            end_time = end_time.isoformat()
        
        update_data = {
            'status': batch_info.get('status'),
            'end_time': end_time,
            'completed_scripts': len(execution_ids),
            'successful_scripts': successful,
            'failed_scripts': failed,
            'pending_scripts': pending,
            'error_scripts': error,
            'timeout_scripts': timeout,
            'suite_id': suite_id,
            'suite_name': suite_name
        }
        
        self.batch_repo.update(batch_id, update_data)
        
        # 更新测试方案执行次数
        if suite_id:
            try:
                # 从容器获取suite_service（修复导入路径）
                from AppCode.core.container import Container
                container = Container.get_instance()
                suite_service = container.resolve('test_suite_service')
                
                # 记录方案执行
                success = suite_service.record_execution(suite_id)
                if success and self.logger:
                    self.logger.info(f"Updated execution count for suite ID: {suite_id}")
                elif not success and self.logger:
                    self.logger.warning(f"Failed to update execution count for suite ID: {suite_id}")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error updating suite execution count: {e}", exc_info=True)
        
        if self.logger:
            self.logger.info(
                f"Batch result saved: {batch_id} - "
                f"total: {len(execution_ids)}, "
                f"success: {successful}, "
                f"failed: {failed}, "
                f"pending: {pending}"
            )