"""启动脚本

从项目根目录启动应用程序。
"""

import sys
import os

# 将项目根目录添加到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 导入并运行主程序
from AppCode.main import main

if __name__ == '__main__':
    main()