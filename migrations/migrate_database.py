"""数据库迁移工具

执行数据库结构升级。
"""

import sqlite3
import os
import sys
from datetime import datetime

# 设置UTF-8编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_db_path():
    """获取数据库路径"""
    # 尝试多个可能的数据库位置
    possible_paths = [
        'AppCode/data/app.db',
        'data/app.db',
        'data/script_executor.db'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # 如果都不存在，返回默认路径
    return 'AppCode/data/app.db'


def backup_database(db_path):
    """备份数据库"""
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return None
    
    backup_dir = 'backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'app_db_backup_{timestamp}.db')
    
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"[OK] 数据库已备份到: {backup_path}")
    
    return backup_path


def check_column_exists(cursor, table, column):
    """检查列是否存在"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def check_table_exists(cursor, table):
    """检查表是否存在"""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    )
    return cursor.fetchone() is not None


def migrate_v1_1(db_path):
    """执行 v1.1 迁移"""
    print("\n" + "="*60)
    print("开始执行数据库迁移 v1.1")
    print("="*60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 第一部分：扩展执行结果状态
        print("\n[1/3] 扩展执行结果状态...")
        
        # 确保 batch_executions 表存在
        if not check_table_exists(cursor, 'batch_executions'):
            cursor.execute('''
                CREATE TABLE batch_executions (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    total_scripts INTEGER,
                    completed_scripts INTEGER DEFAULT 0,
                    successful_scripts INTEGER DEFAULT 0,
                    failed_scripts INTEGER DEFAULT 0,
                    status TEXT NOT NULL,
                    start_time TEXT,
                    end_time TEXT,
                    user_id TEXT,
                    params TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("  [OK] 创建 batch_executions 表")
        
        # 添加 test_result 字段
        if not check_column_exists(cursor, 'execution_history', 'test_result'):
            cursor.execute(
                "ALTER TABLE execution_history ADD COLUMN test_result VARCHAR(20) DEFAULT '-'"
            )
            print("  [OK] 添加 execution_history.test_result 字段")
        else:
            print("  [-] execution_history.test_result 字段已存在")
        
        # 添加批次统计字段
        for field in ['pending_scripts', 'error_scripts', 'timeout_scripts']:
            if not check_column_exists(cursor, 'batch_executions', field):
                cursor.execute(
                    f"ALTER TABLE batch_executions ADD COLUMN {field} INTEGER DEFAULT 0"
                )
                print(f"  [OK] 添加 batch_executions.{field} 字段")
            else:
                print(f"  [-] batch_executions.{field} 字段已存在")
        
        # 更新现有数据
        cursor.execute("""
            UPDATE execution_history
            SET test_result = CASE
                WHEN status = 'SUCCESS' THEN '合格'
                WHEN status = 'FAILED' THEN '不合格'
                WHEN status = 'ERROR' THEN '执行错误'
                WHEN status = 'TIMEOUT' THEN '超时'
                WHEN status = 'PENDING' THEN '待判定'
                ELSE '-'
            END
            WHERE test_result = '-'
        """)
        updated_count = cursor.rowcount
        print(f"  [OK] 更新了 {updated_count} 条历史记录的测试结果")
        
        # 第二部分：测试方案管理
        print("\n[2/3] 创建测试方案管理表...")
        
        if not check_table_exists(cursor, 'test_suites'):
            cursor.execute("""
                CREATE TABLE test_suites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    description TEXT,
                    script_paths TEXT NOT NULL,
                    script_count INTEGER DEFAULT 0,
                    created_by VARCHAR(50),
                    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_executed_time DATETIME,
                    execution_count INTEGER DEFAULT 0
                )
            """)
            print("  [OK] 创建 test_suites 表")
        else:
            print("  [-] test_suites 表已存在")
        
        # 添加方案关联字段
        for field in ['suite_id', 'suite_name']:
            if not check_column_exists(cursor, 'batch_executions', field):
                field_type = 'INTEGER' if field == 'suite_id' else 'VARCHAR(100)'
                cursor.execute(
                    f"ALTER TABLE batch_executions ADD COLUMN {field} {field_type}"
                )
                print(f"  [OK] 添加 batch_executions.{field} 字段")
            else:
                print(f"  [-] batch_executions.{field} 字段已存在")
        
        # 第三部分：创建索引
        print("\n[3/3] 创建索引...")
        
        indexes = [
            ('idx_execution_history_test_result', 'execution_history', 'test_result'),
            ('idx_execution_history_batch_id', 'execution_history', 'batch_id'),
            ('idx_batch_executions_suite_id', 'batch_executions', 'suite_id'),
            ('idx_batch_executions_status', 'batch_executions', 'status'),
            ('idx_test_suites_name', 'test_suites', 'name'),
        ]
        
        for idx_name, table, column in indexes:
            try:
                cursor.execute(
                    f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})"
                )
                print(f"  [OK] 创建索引 {idx_name}")
            except sqlite3.OperationalError as e:
                if 'already exists' in str(e):
                    print(f"  [-] 索引 {idx_name} 已存在")
                else:
                    raise
        
        # 提交更改
        conn.commit()
        
        # 验证结果
        print("\n" + "="*60)
        print("迁移验证")
        print("="*60)
        
        cursor.execute("SELECT COUNT(*) FROM execution_history")
        exec_count = cursor.fetchone()[0]
        print(f"执行历史记录数: {exec_count}")
        
        cursor.execute("SELECT COUNT(*) FROM batch_executions")
        batch_count = cursor.fetchone()[0]
        print(f"批次执行记录数: {batch_count}")
        
        cursor.execute("SELECT COUNT(*) FROM test_suites")
        suite_count = cursor.fetchone()[0]
        print(f"测试方案数: {suite_count}")
        
        print("\n" + "="*60)
        print("[SUCCESS] 数据库迁移 v1.1 完成！")
        print("="*60)
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        conn.close()


def main():
    """主函数"""
    print("数据库迁移工具 v1.1")
    print("="*60)
    
    # 获取数据库路径
    db_path = get_db_path()
    print(f"数据库路径: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"\n警告: 数据库文件不存在，将在首次运行时创建")
        print("跳过迁移...")
        return
    
    # 备份数据库
    backup_path = backup_database(db_path)
    if backup_path:
        print(f"如果迁移失败，可以从备份恢复: {backup_path}")
    
    # 执行迁移
    success = migrate_v1_1(db_path)
    
    if success:
        print("\n迁移成功！可以启动应用程序。")
    else:
        print("\n迁移失败！请检查错误信息。")
        if backup_path:
            print(f"可以从备份恢复: {backup_path}")
        sys.exit(1)


if __name__ == '__main__':
    main()