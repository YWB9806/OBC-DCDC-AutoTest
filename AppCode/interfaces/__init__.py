"""核心接口定义

定义系统中各模块的接口规范。
"""

from .i_script_manager import IScriptManager
from .i_execution_engine import IExecutionEngine
from .i_data_access import (
    IDataAccess,
    IExecutionHistoryRepository,
    IBatchExecutionRepository,
    IUserRepository
)
from .i_result_analyzer import IResultAnalyzer

__all__ = [
    'IScriptManager',
    'IExecutionEngine',
    'IDataAccess',
    'IExecutionHistoryRepository',
    'IBatchExecutionRepository',
    'IUserRepository',
    'IResultAnalyzer',
]