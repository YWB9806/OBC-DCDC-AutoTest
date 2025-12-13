"""主程序入口

启动Python脚本批量执行工具。
"""

import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from AppCode.core.container import Container
from AppCode.ui.main_window import MainWindow
from AppCode.ui.login_dialog_qt_modern import LoginDialog


def main():
    """主函数"""
    # 创建Qt应用
    app = QApplication(sys.argv)
    app.setApplicationName("Python脚本批量执行工具")
    app.setOrganizationName("ScriptExecutor")
    
    # 初始化依赖注入容器
    container = Container()
    
    # 获取用户服务
    user_service = container.resolve('user_service')
    
    # 显示登录对话框
    login_dialog = LoginDialog(user_service)
    
    if login_dialog.exec_() != LoginDialog.Accepted:
        # 用户取消登录或关闭对话框，退出应用
        sys.exit(0)
    
    # 获取登录结果
    login_result = login_dialog.get_result()
    
    if not login_result or not login_result.get('success'):
        QMessageBox.critical(None, "错误", "登录失败，应用程序将退出")
        sys.exit(1)
    
    # 创建主窗口
    main_window = MainWindow(container)
    
    # 设置当前用户并应用权限
    main_window.set_current_user(login_result)
    
    # 显示主窗口
    main_window.show()
    
    # 运行应用
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()