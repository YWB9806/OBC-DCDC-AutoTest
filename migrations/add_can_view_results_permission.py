"""数据库迁移：添加can_view_results权限字段

为users表添加can_view_results字段，并将admin账户升级为super_admin。
"""

import sqlite3
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from AppCode.utils.constants import UserRole


def migrate():
    """执行迁移"""
    db_path = os.path.join("AppCode", "data", "app.db")
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        print("首次运行时会自动创建，无需迁移")
        return
    
    print(f"开始迁移数据库: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. 检查can_view_results字段是否已存在
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'can_view_results' not in columns:
            print("添加can_view_results字段...")
            cursor.execute("""
                ALTER TABLE users ADD COLUMN can_view_results INTEGER DEFAULT 0
            """)
            print("✓ can_view_results字段添加成功")
        else:
            print("✓ can_view_results字段已存在")
        
        # 2. 将admin账户升级为super_admin并授予权限
        cursor.execute("SELECT id, username, role FROM users WHERE username = 'admin'")
        admin = cursor.fetchone()
        
        if admin:
            admin_id, username, role = admin
            print(f"找到admin账户: ID={admin_id}, 当前角色={role}")
            
            if role != UserRole.SUPER_ADMIN:
                print("升级admin为super_admin...")
                cursor.execute("""
                    UPDATE users 
                    SET role = ?, can_view_results = 1 
                    WHERE id = ?
                """, (UserRole.SUPER_ADMIN, admin_id))
                print("✓ admin账户已升级为super_admin")
            else:
                # 确保super_admin有查看结果权限
                cursor.execute("""
                    UPDATE users 
                    SET can_view_results = 1 
                    WHERE id = ?
                """, (admin_id,))
                print("✓ admin账户已是super_admin")
        else:
            print("⚠ 未找到admin账户，将在首次运行时自动创建")
        
        # 3. 更新所有admin角色为super_admin（如果有其他管理员）
        cursor.execute("""
            UPDATE users 
            SET role = ?, can_view_results = 1 
            WHERE role = ? AND role != ?
        """, (UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.SUPER_ADMIN))
        
        updated = cursor.rowcount
        if updated > 0:
            print(f"✓ 升级了 {updated} 个admin账户为super_admin")
        
        # 提交更改
        conn.commit()
        print("\n✓ 数据库迁移完成！")
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ 迁移失败: {e}")
        raise
    
    finally:
        conn.close()


if __name__ == '__main__':
    migrate()