"""登录诊断脚本

运行此脚本检查登录功能是否正常。
如果此脚本也崩溃，请将输出截图发给开发者。
"""

import sys
import os
import traceback
import time

print("=" * 60)
print("登录诊断脚本 v1.0")
print("=" * 60)

# Step 1: Check environment
print(f"\n[1] Python: {sys.version}")
print(f"[1] 路径: {sys.executable}")
print(f"[1] 工作目录: {os.getcwd()}")

# Step 2: Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
print(f"\n[2] 项目根目录已添加到路径")

# Step 3: Test PBKDF2 performance
print("\n[3] 测试密码哈希性能...")
import hashlib
salt = os.urandom(16)
t0 = time.time()
for i in range(3):
    start = time.time()
    key = hashlib.pbkdf2_hmac('sha256', b'test', salt, 100000)
    print(f"    第{i+1}次: {time.time()-start:.3f}秒")
print(f"    平均: {(time.time()-t0)/3:.3f}秒")

# Step 4: Create QApplication
print("\n[4] 创建 QApplication...")
try:
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
    print(f"    Qt版本: {QT_VERSION_STR}")
    print(f"    PyQt版本: {PYQT_VERSION_STR}")
except Exception as e:
    print(f"    [错误] {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 5: Initialize container
print("\n[5] 初始化依赖容器...")
try:
    t0 = time.time()
    from AppCode.core.container import Container
    container = Container()
    print(f"    容器创建完成 ({time.time()-t0:.3f}秒)")
except Exception as e:
    print(f"    [错误] {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 6: Get user service
print("\n[6] 获取用户服务...")
try:
    t0 = time.time()
    user_service = container.resolve('user_service')
    print(f"    用户服务已获取 ({time.time()-t0:.3f}秒)")
except Exception as e:
    print(f"    [错误] {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 7: Test direct login (bypass UI)
print("\n[7] 测试直接登录（不经过UI）...")
try:
    t0 = time.time()
    result = user_service.login('admin', 'admin')
    elapsed = time.time() - t0
    print(f"    耗时: {elapsed:.3f}秒")
    print(f"    结果: {result}")
except Exception as e:
    print(f"    [错误] {e}")
    traceback.print_exc()

# Step 8: Create LoginDialog
print("\n[8] 创建登录对话框...")
try:
    from AppCode.ui.login_dialog_qt_modern import LoginDialog
    t0 = time.time()
    dialog = LoginDialog(user_service)
    print(f"    对话框创建完成 ({time.time()-t0:.3f}秒)")
except Exception as e:
    print(f"    [错误] {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 9: Simulate login via UI
print("\n[9] 模拟UI登录...")
try:
    dialog.username_edit.setText('admin')
    dialog.password_edit.setText('admin')
    t0 = time.time()
    dialog._on_login()
    print(f"    _on_login() 调用完成 ({time.time()-t0:.4f}秒)")
except Exception as e:
    print(f"    [错误] {e}")
    traceback.print_exc()

# Step 10: Process events to trigger QTimer.singleShot
print("\n[10] 处理事件循环...")
try:
    from PyQt5.QtCore import QTimer
    for i in range(10):
        app.processEvents()
        time.sleep(0.1)
    if dialog.login_result:
        print(f"    登录成功! 用户: {dialog.login_result.get('user', {}).get('username')}")
    else:
        print(f"    登录结果为空，可能还在处理中...")
except Exception as e:
    print(f"    [错误] {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("诊断完成。如果以上所有步骤都通过，说明登录代码本身没有问题。")
print("请将此输出截图发给开发者以进一步排查。")
print("=" * 60)
