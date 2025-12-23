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
    """初始化超级管理员账户和默认用户"""
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
        
        # 3. 创建默认用户（可选）
        # 如需创建默认用户，请取消下面代码的注释并修改用户名和密码
        """
        default_username = 'your_username'  # 修改为实际用户名
        default_password = 'your_password'  # 修改为实际密码
        
        cursor.execute("SELECT id FROM users WHERE username = ?", (default_username,))
        existing_default_user = cursor.fetchone()
        
        if not existing_default_user:
            hashed_default_password = hash_password(default_password)
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, email, is_active, can_view_results, created_at)
                VALUES (?, ?, 'user', '', 1, 1, ?)
            ''', (default_username, hashed_default_password, datetime.now().isoformat()))
            print(f"已创建默认用户 {default_username}")
        else:
            # 更新现有用户，确保权限正确
            hashed_default_password = hash_password(default_password)
            cursor.execute('''
                UPDATE users
                SET password_hash = ?,
                    role = 'user',
                    is_active = 1,
                    can_view_results = 1
                WHERE username = ?
            ''', (hashed_default_password, default_username))
            print(f"已更新默认用户 {default_username}")
        """
        
        conn.commit()
        
        # 4. 验证创建结果
        cursor.execute("""
            SELECT username, role, is_active, can_view_results, email
            FROM users WHERE username = 'admin'
        """)
        results = cursor.fetchall()
        
        print("\n" + "="*50)
        print("用户账户信息：")
        print("="*50)
        for result in results:
            print(f"\n用户名: {result[0]}")
            print(f"密码: ******** (已加密)")
            print(f"角色: {result[1]}")
            print(f"状态: {'激活' if result[2] else '未激活'}")
            print(f"可查看结果: {'是' if result[3] else '否'}")
            print(f"邮箱: {result[4] if result[4] else '未设置'}")
        print("="*50)
        print("\n请妥善保管用户密码！")
        print("提示：可通过环境变量 ADMIN_PASSWORD 设置自定义管理员密码\n")
        
    except Exception as e:
        print(f"初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    init_admin_user()