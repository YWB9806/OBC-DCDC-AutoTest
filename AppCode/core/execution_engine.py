"""执行引擎实现

负责脚本的执行、监控和控制。
"""

import subprocess
import threading
import time
import queue
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import psutil  # 用于进程暂停/恢复

from AppCode.interfaces.i_execution_engine import IExecutionEngine
from AppCode.utils.constants import ExecutionStatus
from AppCode.utils.exceptions import ExecutionError
from AppCode.core.output_monitor import OutputMonitor


class ExecutionEngine(IExecutionEngine):
    """执行引擎实现"""
    
    def __init__(self, logger=None, max_workers: int = 1, config_manager=None):
        """初始化执行引擎
        
        Args:
            logger: 日志记录器
            max_workers: 最大并发执行数（车载ECU测试必须为1，硬件资源独占）
            config_manager: 配置管理器
        """
        self.logger = logger
        self.max_workers = 1  # 强制设置为1，确保顺序执行
        self.config_manager = config_manager
        self._executions = {}  # execution_id -> execution_info
        self._processes = {}   # execution_id -> subprocess.Popen
        self._threads = {}     # execution_id -> threading.Thread
        self._lock = threading.Lock()
        self._task_queue = queue.Queue()
        self._worker_threads = []
        self._running = False
        self._paused_executions = set()  # 新增：暂停的执行ID集合
        self._pause_lock = threading.Lock()  # 新增：暂停操作锁
        
        # 从配置读取超时时间，默认3600秒（1小时）
        if config_manager:
            self._timeout = config_manager.get('execution.script_timeout', 3600)
        else:
            self._timeout = 3600
        
        if self.logger:
            self.logger.info(f"ExecutionEngine initialized with timeout: {self._timeout}s")
    
    def execute_script(
        self,
        script_path: str,
        params: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable] = None,
        batch_id: Optional[str] = None
    ) -> str:
        """执行脚本
        
        Args:
            script_path: 脚本路径
            params: 执行参数
            callback: 完成回调函数
            batch_id: 批次ID（如果属于批次执行）
            
        Returns:
            执行ID
        """
        execution_id = self._generate_execution_id()
        
        execution_info = {
            'id': execution_id,
            'script_path': script_path,
            'params': params or {},
            'status': ExecutionStatus.PENDING,
            'start_time': None,
            'end_time': None,
            'output': [],
            'error': None,
            'callback': callback,
            'progress': 0,
            'batch_id': batch_id  # 添加batch_id
        }
        
        with self._lock:
            self._executions[execution_id] = execution_info
        
        # 添加到任务队列
        self._task_queue.put(execution_id)
        
        if self.logger:
            self.logger.info(f"Script execution queued: {execution_id} - {script_path}")
        
        # 确保工作线程运行
        self._ensure_workers_running()
        
        return execution_id
    
    def execute_batch(
        self,
        script_paths: list,
        params: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable] = None
    ) -> str:
        """批量执行脚本
        
        Args:
            script_paths: 脚本路径列表
            params: 执行参数
            callback: 完成回调函数
            
        Returns:
            批次执行ID
        """
        batch_id = self._generate_execution_id()
        
        if self.logger:
            self.logger.info(f"Batch execution started: {batch_id} - {len(script_paths)} scripts")
        
        # 为每个脚本创建执行任务
        execution_ids = []
        for script_path in script_paths:
            exec_id = self.execute_script(script_path, params, batch_id=batch_id)
            execution_ids.append(exec_id)
        
        # 创建批次信息
        batch_info = {
            'id': batch_id,
            'execution_ids': execution_ids,
            'status': ExecutionStatus.RUNNING,
            'start_time': datetime.now(),
            'callback': callback
        }
        
        with self._lock:
            self._executions[batch_id] = batch_info
        
        # 启动批次监控线程
        monitor_thread = threading.Thread(
            target=self._monitor_batch,
            args=(batch_id,),
            daemon=True
        )
        monitor_thread.start()
        
        return batch_id
    
    def cancel_execution(self, execution_id: str) -> bool:
        """取消执行（改进版 - 避免死锁）
        
        Args:
            execution_id: 执行ID
            
        Returns:
            是否成功取消
        """
        # 第一步：收集需要取消的执行ID（在锁内）
        exec_ids_to_cancel = []
        
        with self._lock:
            if execution_id not in self._executions:
                return False
            
            execution_info = self._executions[execution_id]
            
            # 如果是批次执行，收集所有子任务ID
            if 'execution_ids' in execution_info:
                exec_ids_to_cancel = execution_info['execution_ids'].copy()
                execution_info['status'] = ExecutionStatus.CANCELLED
            else:
                exec_ids_to_cancel = [execution_id]
        
        # 第二步：在锁外取消所有执行（避免死锁）
        success = True
        for exec_id in exec_ids_to_cancel:
            if not self._cancel_single_execution(exec_id):
                success = False
        
        return success
    
    def _cancel_single_execution(self, execution_id: str) -> bool:
        """取消单个执行（内部方法）
        
        Args:
            execution_id: 执行ID
            
        Returns:
            是否成功取消
        """
        # 获取执行信息和进程引用
        with self._lock:
            if execution_id not in self._executions:
                return False
            
            execution_info = self._executions[execution_id]
            
            # 只处理单个执行
            if 'execution_ids' in execution_info:
                return False  # 批次执行应该调用 cancel_execution
            
            if execution_info['status'] not in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]:
                return False
            
            execution_info['status'] = ExecutionStatus.CANCELLED
            
            # 获取进程引用
            process = self._processes.get(execution_id)
        
        # 在锁外终止进程（避免长时间持有锁）
        if process:
            try:
                self._terminate_process_safe(process, execution_id)
                if self.logger:
                    self.logger.info(f"Execution cancelled: {execution_id}")
                return True
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to terminate process {execution_id}: {e}")
                return False
        
        if self.logger:
            self.logger.info(f"Execution cancelled (no process): {execution_id}")
        return True
    
    def skip_current_script(self, execution_id: str) -> bool:
        """跳过当前正在执行的脚本，立即执行下一条（修复版 - 避免死锁）
        
        Args:
            execution_id: 执行ID（可以是单个脚本ID或批次ID）
            
        Returns:
            是否成功跳过
        """
        # 第一步：在锁内查找需要跳过的执行ID
        exec_id_to_skip = None
        
        with self._lock:
            if execution_id not in self._executions:
                if self.logger:
                    self.logger.warning(f"Skip failed: execution not found: {execution_id}")
                return False
            
            execution_info = self._executions[execution_id]
            
            # 如果是批次执行，找到当前正在运行的脚本
            if 'execution_ids' in execution_info:
                for exec_id in execution_info['execution_ids']:
                    if exec_id in self._executions:
                        exec_info = self._executions[exec_id]
                        if exec_info['status'] == ExecutionStatus.RUNNING:
                            # 找到正在运行的脚本
                            exec_id_to_skip = exec_id
                            break
                
                if not exec_id_to_skip:
                    if self.logger:
                        self.logger.warning(f"Skip failed: no running script in batch: {execution_id}")
                    return False
            else:
                # 单个脚本执行
                if execution_info['status'] != ExecutionStatus.RUNNING:
                    if self.logger:
                        self.logger.warning(f"Skip failed: script not running: {execution_id}")
                    return False
                
                exec_id_to_skip = execution_id
        
        # 第二步：在锁外取消找到的执行（避免死锁）
        if exec_id_to_skip:
            if self.logger:
                self.logger.info(f"Skipping execution: {exec_id_to_skip}")
            return self._cancel_single_execution(exec_id_to_skip)
        
        return False
    
    def _terminate_process_safe(self, process, execution_id: str):
        """安全地终止进程
        
        Args:
            process: 进程对象
            execution_id: 执行ID
        """
        try:
            # 首先尝试温和终止
            process.terminate()
            try:
                process.wait(timeout=1)  # 减少超时时间到1秒
                if self.logger:
                    self.logger.info(f"Process terminated gracefully: {execution_id}")
                return
            except subprocess.TimeoutExpired:
                pass
            
            # 温和终止失败，强制杀死
            if self.logger:
                self.logger.warning(f"Process did not terminate, killing: {execution_id}")
            process.kill()
            
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                # 最后的尝试：使用系统命令
                import platform
                if platform.system() == 'Windows':
                    try:
                        import os
                        os.system(f'taskkill /F /T /PID {process.pid} >nul 2>&1')
                        if self.logger:
                            self.logger.info(f"Used taskkill for PID {process.pid}")
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"taskkill failed: {e}")
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error terminating process: {e}")
            raise
    
    def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """获取执行状态
        
        Args:
            execution_id: 执行ID
            
        Returns:
            执行状态信息
        """
        with self._lock:
            if execution_id not in self._executions:
                return {'status': ExecutionStatus.UNKNOWN}
            
            execution_info = self._executions[execution_id].copy()
            
            # 移除回调函数（不可序列化）
            execution_info.pop('callback', None)
            
            return execution_info
    
    def pause_execution(self, execution_id: str) -> bool:
        """暂停执行（异步版本 - 避免阻塞UI）
        
        Args:
            execution_id: 执行ID
            
        Returns:
            是否成功暂停
        """
        # 第一步：检查是否是批次执行并收集子任务ID（在锁内）
        exec_ids_to_pause = []
        
        with self._lock:
            if execution_id not in self._executions:
                return False
            
            execution_info = self._executions[execution_id]
            
            # 如果是批次执行，收集所有子任务ID
            if 'execution_ids' in execution_info:
                exec_ids_to_pause = execution_info['execution_ids'].copy()
                execution_info['status'] = ExecutionStatus.PAUSED
            else:
                exec_ids_to_pause = [execution_id]
        
        # 第二步：在后台线程中暂停所有执行（避免阻塞UI）
        def pause_in_background():
            for exec_id in exec_ids_to_pause:
                self._pause_single_execution(exec_id)
        
        pause_thread = threading.Thread(target=pause_in_background, daemon=True)
        pause_thread.start()
        
        return True
    
    def _pause_single_execution(self, execution_id: str) -> bool:
        """暂停单个执行（内部方法）- 真正暂停进程
        
        Args:
            execution_id: 执行ID
            
        Returns:
            是否成功暂停
        """
        # 第一步：获取执行信息和进程引用（在锁内，快速完成）
        process = None
        should_pause_process = False
        
        with self._lock:
            if execution_id not in self._executions:
                if self.logger:
                    self.logger.warning(f"暂停失败: 执行不存在: {execution_id}")
                return False
            
            execution_info = self._executions[execution_id]
            
            # 只处理单个执行
            if 'execution_ids' in execution_info:
                return False  # 批次执行应该调用 pause_execution
            
            current_status = execution_info['status']
            
            # 如果是PENDING状态，直接标记为PAUSED（不需要暂停进程）
            if current_status == ExecutionStatus.PENDING:
                execution_info['status'] = ExecutionStatus.PAUSED
                if self.logger:
                    self.logger.info(f"等待中的任务已标记为暂停: {execution_id}")
                return True
            
            # 如果已经完成或失败，不需要暂停
            if current_status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED,
                                 ExecutionStatus.CANCELLED, ExecutionStatus.TIMEOUT,
                                 ExecutionStatus.ERROR]:
                if self.logger:
                    self.logger.debug(f"任务已完成，无需暂停 (status={current_status}): {execution_id}")
                return True  # 返回True，因为这不是错误
            
            # 只能暂停正在运行的任务
            if current_status != ExecutionStatus.RUNNING:
                if self.logger:
                    self.logger.warning(f"暂停失败: 状态不是运行中 (status={current_status}): {execution_id}")
                return False
            
            # 获取进程对象
            process = self._processes.get(execution_id)
            if not process:
                if self.logger:
                    self.logger.warning(f"暂停失败: 进程不存在: {execution_id}")
                return False
            
            should_pause_process = True
        
        # 第二步：在锁外暂停进程（避免长时间持有锁导致UI卡顿）
        if should_pause_process and process:
            try:
                # 检查进程是否还存在
                try:
                    parent = psutil.Process(process.pid)
                except psutil.NoSuchProcess:
                    if self.logger:
                        self.logger.warning(f"暂停失败: 进程已结束 (PID: {process.pid}): {execution_id}")
                    # 进程已结束，更新状态
                    with self._lock:
                        if execution_id in self._executions:
                            # 不改变状态，让执行完成流程处理
                            pass
                    return False
                
                # 暂停主进程
                try:
                    parent.suspend()
                    if self.logger:
                        self.logger.debug(f"主进程已暂停 (PID: {process.pid})")
                except psutil.AccessDenied:
                    if self.logger:
                        self.logger.error(f"暂停失败: 权限不足 (PID: {process.pid}): {execution_id}")
                    return False
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"暂停主进程失败: {e} (PID: {process.pid}): {execution_id}")
                    return False
                
                # 暂停所有子进程（容错处理）
                try:
                    children = parent.children(recursive=True)
                    for child in children:
                        try:
                            child.suspend()
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                            # 忽略已结束、无权限或僵尸进程
                            pass
                        except Exception as e:
                            if self.logger:
                                self.logger.debug(f"暂停子进程失败 (忽略): {e}")
                except Exception as e:
                    # 获取子进程列表失败，不影响主进程暂停
                    if self.logger:
                        self.logger.debug(f"获取子进程列表失败 (忽略): {e}")
                
                # 标记为暂停
                with self._lock:
                    if execution_id in self._executions:
                        self._executions[execution_id]['status'] = ExecutionStatus.PAUSED
                
                with self._pause_lock:
                    self._paused_executions.add(execution_id)
                
                if self.logger:
                    self.logger.info(f"执行已暂停: {execution_id} (PID: {process.pid})")
                
                return True
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"暂停失败 (未知错误): {e}: {execution_id}", exc_info=True)
                return False
        
        return False
    
    def resume_execution(self, execution_id: str) -> bool:
        """恢复执行（异步版本 - 避免阻塞UI）
        
        Args:
            execution_id: 执行ID
            
        Returns:
            是否成功恢复
        """
        # 第一步：检查是否是批次执行并收集子任务ID（在锁内）
        exec_ids_to_resume = []
        
        with self._lock:
            if execution_id not in self._executions:
                return False
            
            execution_info = self._executions[execution_id]
            
            # 如果是批次执行，收集所有子任务ID
            if 'execution_ids' in execution_info:
                exec_ids_to_resume = execution_info['execution_ids'].copy()
                execution_info['status'] = ExecutionStatus.RUNNING
            else:
                exec_ids_to_resume = [execution_id]
        
        # 第二步：在后台线程中恢复所有执行（避免阻塞UI）
        def resume_in_background():
            for exec_id in exec_ids_to_resume:
                self._resume_single_execution(exec_id)
        
        resume_thread = threading.Thread(target=resume_in_background, daemon=True)
        resume_thread.start()
        
        return True
    
    def _resume_single_execution(self, execution_id: str) -> bool:
        """恢复单个执行（内部方法）- 真正恢复进程
        
        Args:
            execution_id: 执行ID
            
        Returns:
            是否成功恢复
        """
        # 第一步：获取执行信息和进程引用（在锁内，快速完成）
        process = None
        should_resume_process = False
        
        with self._lock:
            if execution_id not in self._executions:
                if self.logger:
                    self.logger.warning(f"恢复失败: 执行不存在: {execution_id}")
                return False
            
            execution_info = self._executions[execution_id]
            
            # 只处理单个执行
            if 'execution_ids' in execution_info:
                return False  # 批次执行应该调用 resume_execution
            
            # 只能恢复暂停的任务
            if execution_info['status'] != ExecutionStatus.PAUSED:
                if self.logger:
                    self.logger.warning(f"恢复失败: 状态不是暂停 (status={execution_info['status']}): {execution_id}")
                return False
            
            # 获取进程对象
            process = self._processes.get(execution_id)
            
            # 如果没有进程对象，说明任务还没开始执行（之前是PENDING状态被暂停的）
            if not process:
                # 直接将状态改回PENDING，让工作线程继续处理
                execution_info['status'] = ExecutionStatus.PENDING
                if self.logger:
                    self.logger.info(f"等待中的任务已恢复为PENDING状态: {execution_id}")
                return True
            
            should_resume_process = True
        
        # 第二步：在锁外恢复进程（避免长时间持有锁导致UI卡顿）
        if should_resume_process and process:
            try:
                # 检查进程是否还存在
                try:
                    parent = psutil.Process(process.pid)
                except psutil.NoSuchProcess:
                    if self.logger:
                        self.logger.warning(f"恢复失败: 进程已结束 (PID: {process.pid}): {execution_id}")
                    # 进程已结束，清理暂停标记
                    with self._pause_lock:
                        self._paused_executions.discard(execution_id)
                    return False
                
                # 恢复所有子进程（容错处理）
                try:
                    children = parent.children(recursive=True)
                    for child in children:
                        try:
                            child.resume()
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                            # 忽略已结束、无权限或僵尸进程
                            pass
                        except Exception as e:
                            if self.logger:
                                self.logger.debug(f"恢复子进程失败 (忽略): {e}")
                except Exception as e:
                    # 获取子进程列表失败，不影响主进程恢复
                    if self.logger:
                        self.logger.debug(f"获取子进程列表失败 (忽略): {e}")
                
                # 恢复主进程
                try:
                    parent.resume()
                    if self.logger:
                        self.logger.debug(f"主进程已恢复 (PID: {process.pid})")
                except psutil.AccessDenied:
                    if self.logger:
                        self.logger.error(f"恢复失败: 权限不足 (PID: {process.pid}): {execution_id}")
                    return False
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"恢复主进程失败: {e} (PID: {process.pid}): {execution_id}")
                    return False
                
                # 恢复运行状态
                with self._lock:
                    if execution_id in self._executions:
                        self._executions[execution_id]['status'] = ExecutionStatus.RUNNING
                
                with self._pause_lock:
                    self._paused_executions.discard(execution_id)
                
                if self.logger:
                    self.logger.info(f"执行已恢复: {execution_id} (PID: {process.pid})")
                
                return True
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"恢复失败 (未知错误): {e}: {execution_id}", exc_info=True)
                return False
        
        return False
    
    def _is_paused(self, execution_id: str) -> bool:
        """检查执行是否暂停
        
        Args:
            execution_id: 执行ID
            
        Returns:
            是否暂停
        """
        with self._pause_lock:
            return execution_id in self._paused_executions
    
    def get_execution_output(self, execution_id: str) -> list:
        """获取执行输出
        
        Args:
            execution_id: 执行ID
            
        Returns:
            输出行列表
        """
        with self._lock:
            if execution_id in self._executions:
                return self._executions[execution_id].get('output', []).copy()
        return []
    
    def _ensure_workers_running(self):
        """确保工作线程运行"""
        if not self._running:
            self._running = True
            for i in range(self.max_workers):
                worker = threading.Thread(
                    target=self._worker_loop,
                    daemon=True,
                    name=f"ExecutionWorker-{i}"
                )
                worker.start()
                self._worker_threads.append(worker)
    
    def _worker_loop(self):
        """工作线程循环"""
        while self._running:
            try:
                # 从队列获取任务（超时1秒）
                execution_id = self._task_queue.get(timeout=1)
                
                with self._lock:
                    if execution_id not in self._executions:
                        continue
                    execution_info = self._executions[execution_id]
                    
                    # 检查任务自身是否被暂停
                    if execution_info['status'] == ExecutionStatus.PAUSED:
                        # 任务已暂停，将任务放回队列末尾
                        self._task_queue.put(execution_id)
                        time.sleep(0.5)  # 避免忙等待
                        continue
                    
                    # 检查任务是否属于已暂停的批次
                    batch_id = execution_info.get('batch_id')
                    if batch_id and batch_id in self._executions:
                        batch_info = self._executions[batch_id]
                        if batch_info.get('status') == ExecutionStatus.PAUSED:
                            # 批次已暂停，标记任务为暂停并放回队列
                            execution_info['status'] = ExecutionStatus.PAUSED
                            self._task_queue.put(execution_id)
                            time.sleep(0.5)  # 避免忙等待
                            continue
                    
                    # 检查任务是否被取消
                    if execution_info['status'] == ExecutionStatus.CANCELLED:
                        continue
                
                # 执行脚本
                self._execute_script_internal(execution_id, execution_info)
                
            except queue.Empty:
                continue
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Worker error: {e}")
    
    def _execute_script_internal(self, execution_id: str, execution_info: Dict[str, Any]):
        """内部执行脚本"""
        output_monitor = None
        try:
            # 检查是否已取消
            with self._lock:
                if execution_info['status'] == ExecutionStatus.CANCELLED:
                    return
            
            # 更新状态（使用锁保护）
            with self._lock:
                execution_info['status'] = ExecutionStatus.RUNNING
                execution_info['start_time'] = datetime.now()
            
            if self.logger:
                self.logger.info(f"Executing script: {execution_info['script_path']}")
            
            # 创建输出监控器（用于捕获Log4NetWrapper等输出）
            def on_file_output(line):
                with self._lock:
                    execution_info['output'].append(f"[FILE] {line}")
            
            output_monitor = OutputMonitor(
                execution_info['script_path'],
                output_callback=on_file_output
            )
            output_monitor.start()
            
            # 构建命令
            cmd = ['python', execution_info['script_path']]
            
            # 添加参数
            for key, value in execution_info['params'].items():
                cmd.extend([f'--{key}', str(value)])
            
            # 启动进程（实时输出模式，使用unbuffered模式）
            import os
            import sys
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'  # 禁用Python输出缓冲
            env['PYTHONIOENCODING'] = 'utf-8'  # 设置Python输出编码为UTF-8，支持emoji等特殊字符
            
            # Windows平台下隐藏控制台窗口
            startupinfo = None
            creationflags = 0
            if sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                creationflags = subprocess.CREATE_NO_WINDOW
            
            # 使用二进制模式读取，避免编码问题
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,  # 行缓冲
                env=env,
                startupinfo=startupinfo,
                creationflags=creationflags
            )
            
            with self._lock:
                self._processes[execution_id] = process
            
            # 智能解码函数：尝试多种编码
            def smart_decode(byte_data):
                """智能解码二进制数据，尝试UTF-8和GBK编码"""
                if not byte_data:
                    return ""
                
                # 首先尝试UTF-8（支持emoji）
                try:
                    return byte_data.decode('utf-8')
                except UnicodeDecodeError:
                    pass
                
                # 如果UTF-8失败，尝试GBK（支持C# DLL输出）
                try:
                    return byte_data.decode('gbk')
                except UnicodeDecodeError:
                    pass
                
                # 如果都失败，使用UTF-8并替换错误字符
                return byte_data.decode('utf-8', errors='replace')
            
            # 实时读取输出
            stderr_lines = []
            timeout = getattr(self, '_timeout', 3600)
            start_time = time.time()
            no_output_count = 0  # 连续无输出计数
            max_no_output = 100  # 最大连续无输出次数（1秒）
            
            while True:
                # 检查超时
                if time.time() - start_time > timeout:
                    if self.logger:
                        self.logger.warning(f"Script execution timeout: {execution_id}")
                    try:
                        process.terminate()
                        process.wait(timeout=3)
                    except:
                        process.kill()
                    with self._lock:
                        execution_info['output'].append("执行超时")
                        execution_info['status'] = ExecutionStatus.TIMEOUT
                        execution_info['end_time'] = datetime.now()
                    break
                
                # 检查是否被取消（使用锁保护）
                with self._lock:
                    if execution_info['status'] == ExecutionStatus.CANCELLED:
                        break
                
                if execution_info['status'] == ExecutionStatus.CANCELLED:
                    try:
                        process.terminate()
                        process.wait(timeout=3)
                    except:
                        process.kill()
                    break
                
                # 先检查进程是否已经结束
                poll_result = process.poll()
                
                # 读取stdout（二进制模式）
                line_bytes = process.stdout.readline()
                if line_bytes:
                    line = smart_decode(line_bytes).rstrip()
                    with self._lock:
                        execution_info['output'].append(line)
                    
                    # 更新进度（简单估算）
                    execution_info['progress'] = min(90, len(execution_info['output']) * 2)
                    no_output_count = 0  # 重置无输出计数
                else:
                    no_output_count += 1
                
                # 如果进程已结束，读取所有剩余输出后退出
                if poll_result is not None:
                    # 读取剩余输出
                    remaining_bytes = process.stdout.read()
                    if remaining_bytes:
                        remaining = smart_decode(remaining_bytes)
                        for line in remaining.split('\n'):
                            if line.strip():
                                with self._lock:
                                    execution_info['output'].append(line.rstrip())
                    
                    # 读取stderr
                    stderr_bytes = process.stderr.read()
                    if stderr_bytes:
                        stderr_output = smart_decode(stderr_bytes)
                        stderr_lines = stderr_output.strip().split('\n')
                    
                    if self.logger:
                        self.logger.info(f"Process ended with return code: {poll_result} for {execution_id}")
                    break
                
                # 如果长时间没有输出且进程状态未知，主动检查进程状态
                if no_output_count >= max_no_output:
                    poll_result = process.poll()
                    if poll_result is not None:
                        if self.logger:
                            self.logger.info(f"Process detected as ended (no output) with return code: {poll_result} for {execution_id}")
                        # 读取所有剩余输出
                        remaining_bytes = process.stdout.read()
                        if remaining_bytes:
                            remaining = smart_decode(remaining_bytes)
                            for line in remaining.split('\n'):
                                if line.strip():
                                    with self._lock:
                                        execution_info['output'].append(line.rstrip())
                        
                        stderr_bytes = process.stderr.read()
                        if stderr_bytes:
                            stderr_output = smart_decode(stderr_bytes)
                            stderr_lines = stderr_output.strip().split('\n')
                        break
                    no_output_count = 0  # 重置计数
                
                # 短暂休眠避免CPU占用过高
                time.sleep(0.01)
            
            return_code = process.returncode
            
            # 更新状态（使用锁保护）
            with self._lock:
                # 只有在未被取消或超时的情况下才更新为成功/失败
                if execution_info['status'] not in [ExecutionStatus.CANCELLED, ExecutionStatus.TIMEOUT]:
                    execution_info['end_time'] = datetime.now()
                    
                    if return_code == 0:
                        execution_info['status'] = ExecutionStatus.SUCCESS
                        # 解析测试结果
                        execution_info['test_result'] = self._parse_test_result(execution_info['output'])
                    else:
                        execution_info['status'] = ExecutionStatus.FAILED
                        execution_info['error'] = '\n'.join(stderr_lines) if stderr_lines else f"Exit code: {return_code}"
                        execution_info['test_result'] = 'fail'
                    
                    execution_info['progress'] = 100
                else:
                    # 已取消或超时，确保设置结束时间
                    if not execution_info.get('end_time'):
                        execution_info['end_time'] = datetime.now()
                    # 设置测试结果
                    if execution_info['status'] == ExecutionStatus.CANCELLED:
                        execution_info['test_result'] = 'pending'
                    elif execution_info['status'] == ExecutionStatus.TIMEOUT:
                        execution_info['test_result'] = 'timeout'
            
            if self.logger:
                self.logger.info(
                    f"Script execution completed: {execution_id} - "
                    f"Status: {execution_info['status']}"
                )
            
            # 调用回调
            if execution_info.get('callback'):
                try:
                    execution_info['callback'](execution_id, execution_info)
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Callback error: {e}")
        
        except Exception as e:
            with self._lock:
                # 只有在未被取消或超时的情况下才更新为错误
                if execution_info['status'] not in [ExecutionStatus.CANCELLED, ExecutionStatus.TIMEOUT]:
                    execution_info['status'] = ExecutionStatus.ERROR
                    execution_info['error'] = str(e)
                    execution_info['test_result'] = 'error'
                execution_info['end_time'] = datetime.now()
            
            if self.logger:
                self.logger.error(f"Execution error for {execution_id}: {e}", exc_info=True)
        
        finally:
            # 停止输出监控器
            if output_monitor:
                output_monitor.stop()
            
            # 清理进程引用
            with self._lock:
                self._processes.pop(execution_id, None)
    
    def _monitor_batch(self, batch_id: str):
        """监控批次执行"""
        while True:
            time.sleep(1)
            
            with self._lock:
                if batch_id not in self._executions:
                    break
                
                batch_info = self._executions[batch_id]
                execution_ids = batch_info.get('execution_ids', [])
                
                # 检查所有子任务状态
                all_completed = True
                has_paused = False
                
                for exec_id in execution_ids:
                    if exec_id in self._executions:
                        exec_status = self._executions[exec_id]['status']
                        # 修复：PAUSED状态也算未完成
                        if exec_status in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING, ExecutionStatus.PAUSED]:
                            all_completed = False
                        if exec_status == ExecutionStatus.PAUSED:
                            has_paused = True
                
                # 如果有任务暂停，批次也标记为暂停
                if has_paused and batch_info['status'] != ExecutionStatus.PAUSED:
                    batch_info['status'] = ExecutionStatus.PAUSED
                    if self.logger:
                        self.logger.info(f"Batch execution paused: {batch_id}")
                
                # 如果批次是PAUSED状态但没有暂停的任务了，恢复为RUNNING
                if batch_info['status'] == ExecutionStatus.PAUSED and not has_paused and not all_completed:
                    batch_info['status'] = ExecutionStatus.RUNNING
                    if self.logger:
                        self.logger.info(f"Batch execution resumed: {batch_id}")
                
                if all_completed:
                    # 批次完成，检查是否有失败的任务
                    has_failed = False
                    for exec_id in execution_ids:
                        if exec_id in self._executions:
                            exec_status = self._executions[exec_id]['status']
                            if exec_status in [ExecutionStatus.FAILED, ExecutionStatus.ERROR,
                                             ExecutionStatus.TIMEOUT, ExecutionStatus.CANCELLED]:
                                has_failed = True
                                break
                    
                    # 根据子任务状态设置批次状态
                    if has_failed:
                        batch_info['status'] = ExecutionStatus.FAILED
                    else:
                        batch_info['status'] = ExecutionStatus.SUCCESS
                    
                    batch_info['end_time'] = datetime.now()
                    
                    if self.logger:
                        self.logger.info(f"Batch execution completed: {batch_id} - Status: {batch_info['status']}")
                    
                    # 调用回调
                    if batch_info.get('callback'):
                        try:
                            batch_info['callback'](batch_id, batch_info)
                        except Exception as e:
                            if self.logger:
                                self.logger.error(f"Batch callback error: {e}")
                    
                    break
    
    def register_callback(self, event: str, callback: Callable):
        """注册事件回调
        
        Args:
            event: 事件名称
            callback: 回调函数
        """
        # 简单实现，可以扩展为事件系统
        if self.logger:
            self.logger.info(f"Callback registered for event: {event}")
    
    def set_max_parallel(self, max_parallel: int):
        """设置最大并行数
        
        Args:
            max_parallel: 最大并行执行数
        
        Note:
            车载ECU测试场景下，此值固定为1，不允许修改
        """
        if max_parallel != 1:
            if self.logger:
                self.logger.warning(f"车载ECU测试必须顺序执行，忽略并行数设置: {max_parallel}")
        self.max_workers = 1  # 强制为1
        if self.logger:
            self.logger.info("执行模式: 顺序执行（车载ECU测试专用）")
    
    def set_timeout(self, timeout: int):
        """设置执行超时时间
        
        Args:
            timeout: 超时时间（秒）
        """
        self._timeout = timeout
        if self.logger:
            self.logger.info(f"Timeout set to: {timeout} seconds")
    
    def _parse_test_result(self, output_lines: list) -> str:
        """解析测试结果
        
        Args:
            output_lines: 输出行列表
            
        Returns:
            测试结果: 'pass', 'fail', 'pending', 'error', 'timeout'
        """
        # 从后往前查找，最后的结果最准确
        for line in reversed(output_lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            line_lower = line_stripped.lower()
            
            # 优先检查明确的合格标识（不合格中也包含"合格"，所以要先排除）
            # 添加对"通过"的支持
            if '合格' in line_stripped and '不合格' not in line_stripped:
                return 'pass'
            elif '通过' in line_stripped and '不通过' not in line_stripped:
                return 'pass'
            elif 'pass' in line_lower and 'fail' not in line_lower:
                return 'pass'
            
            # 检查不合格标识
            elif '不合格' in line_stripped:
                return 'fail'
            elif '不通过' in line_stripped:
                return 'fail'
            elif 'fail' in line_lower:
                return 'fail'
            
            # 检查待判定标识
            elif '待判定' in line_stripped or '需要确认' in line_stripped:
                return 'pending'
            elif 'pending' in line_lower or 'to be confirmed' in line_lower:
                return 'pending'
            
            # 检查错误标识（注意：排除"误差"这种正常的测试输出）
            elif 'exception' in line_lower or 'traceback' in line_lower:
                return 'error'
        
        # 如果没有找到明确的结果标识，返回待判定
        return 'pending'
    
    def _generate_execution_id(self) -> str:
        """生成执行ID"""
        import random
        # 使用时间戳 + 随机数 + 对象ID + 计数器确保唯一性
        timestamp = int(time.time() * 1000000)  # 微秒级时间戳
        random_part = random.randint(10000, 99999)
        return f"exec_{timestamp}_{random_part}_{id(self)}"
    
    def shutdown(self):
        """关闭执行引擎"""
        self._running = False
        
        # 取消所有执行
        with self._lock:
            for execution_id in list(self._executions.keys()):
                self.cancel_execution(execution_id)
        
        if self.logger:
            self.logger.info("Execution engine shutdown")