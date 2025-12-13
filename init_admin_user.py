# -*- coding: utf-8 -*-
"""
初始化超级管理员账户
"""
import sqlite3
import hashlib
from datetime import datetime

def hash_password(password):
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_admin_user():
    """初始化超级管理员账户"""
    db_path = 'AppCode/data/app.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 检查并添加 can_view_results 字段
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'can_view_results' not in columns:
            print("添加 can_view_results 字段...")
            cursor.execute("""
                ALTER TABLE users ADD COLUMN can_view_results INTEGER DEFAULT 0
            """)
            conn.commit()
            print("字段添加成功")
        
        # 2. 检查是否已存在admin用户
        cursor.execute("SELECT id, role FROM users WHERE username = 'admin'")
        existing_user = cursor.fetchone()
        
        # 从环境变量或配置文件读取密码（生产环境应使用更安全的方式）
        import os
        admin_password = os.environ.get('ADMIN_PASSWORD', 'YWB9806')
        
        if existing_user:
            # 更新现有admin用户
            hashed_password = hash_password(admin_password)
            cursor.execute("""
                UPDATE users
                SET password_hash = ?,
                    role = 'super_admin',
                    is_active = 1,
                    can_view_results = 1
                WHERE username = 'admin'
            """, (hashed_password,))
            print("已更新超级管理员账户")
        else:
            # 创建新的admin用户
            hashed_password = hash_password(admin_password)
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, email, is_active, can_view_results, created_at)
                VALUES (?, ?, 'super_admin', 'admin@example.com', 1, 1, ?)
            """, ('admin', hashed_password, datetime.now().isoformat()))
            print("已创建超级管理员账户")
        
        conn.commit()
        
        # 3. 验证创建结果
        cursor.execute("""
            SELECT username, role, is_active, can_view_results, email
            FROM users WHERE username = 'admin'
        """)
        result = cursor.fetchone()
        
        print("\n" + "="*50)
        print("超级管理员账户信息：")
        print("="*50)
        print(f"用户名: admin")
        print(f"密码: ******** (已加密)")
        print(f"角色: {result[1] if result else 'N/A'}")
        print(f"状态: {'激活' if result and result[2] else '未激活'}")
        print(f"可查看结果: {'是' if result and result[3] else '否'}")
        print(f"邮箱: {result[4] if result else 'N/A'}")
        print("="*50)
        print("\n请妥善保管管理员密码！")
        print("提示：可通过环境变量 ADMIN_PASSWORD 设置自定义密码\n")
        
    except Exception as e:
        print(f"初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    init_admin_user()