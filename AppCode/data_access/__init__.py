"""数据访问层

提供数据库访问接口。
"""

from .sqlite_data_access import SQLiteDataAccess

__all__ = ['SQLiteDataAccess']