# Python脚本批量执行工具

一款基于PyQt5的桌面应用程序，用于批量管理和执行Python测试脚本。

## 📋 项目状态

**当前版本**: v1.0.0 (开发中)  
**开发阶段**: 阶段1 - 基础架构搭建

### ✅ 已完成
- [x] 完整的架构设计文档
- [x] 数据库设计文档
- [x] API接口文档
- [x] 开发规范文档
- [x] 工具模块 (utils/)
  - [x] 常量定义 (constants.py)
  - [x] 自定义异常 (exceptions.py)
  - [x] 验证器 (validators.py)
  - [x] 装饰器 (decorators.py)
- [x] 配置管理 (config.py)
- [x] 主程序入口 (main.py)

### 🚧 进行中
- [ ] 基础设施层 (infrastructure/)
- [ ] 领域层 (core/)
- [ ] 应用服务层 (services/)
- [ ] UI层 (ui/)

## 🎯 功能特性

- 🚀 **高性能**: 支持多进程并行执行，充分利用多核CPU
- 📊 **实时监控**: 实时显示执行状态和性能指标
- 📝 **详细日志**: 完整的执行历史和日志记录
- 👥 **权限管理**: 支持管理员和普通用户两种角色
- 🔌 **插件系统**: 可扩展的插件架构
- 🌐 **API接口**: RESTful API支持CI/CD集成

## 📦 安装

### 环境要求
- Python 3.8+
- PyQt5 5.15+

### 安装步骤

```bash
# 1. 克隆项目
git clone <repository_url>
cd Python脚本批量执行工具

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt
```

## 🚀 快速开始

### 启动方式

**方式1：使用启动脚本（推荐）**
```bash
python run.py
```

**方式2：使用模块方式**
```bash
python -m AppCode.main
```

**注意**：不要直接运行 `python AppCode/main.py`，会导致模块导入错误。

## 📁 项目结构

```
Python脚本批量执行工具/
├── AppCode/                    # 应用代码
│   ├── utils/                 # 工具模块
│   │   ├── constants.py      # 常量定义
│   │   ├── exceptions.py     # 自定义异常
│   │   ├── validators.py     # 验证器
│   │   └── decorators.py     # 装饰器
│   ├── infrastructure/        # 基础设施层 (待实现)
│   ├── core/                  # 领域层 (待实现)
│   ├── services/              # 应用服务层 (待实现)
│   ├── ui/                    # UI层 (待实现)
│   ├── config.py             # 配置管理
│   └── main.py               # 主程序入口
├── documents/                 # 文档
│   ├── 软件开发手册.md
│   ├── 架构设计文档.md
│   ├── 数据库设计文档.md
│   ├── API接口文档.md
│   └── 开发规范文档.md
├── TestScripts/              # 测试脚本目录
├── requirements.txt          # 依赖包列表
└── README.md                 # 本文件
```

## 📖 文档

详细文档请查看 `documents/` 目录：

- [软件开发手册](documents/软件开发手册.md) - 项目总览和导航
- [架构设计文档](documents/架构设计文档.md) - 系统架构详细说明
- [数据库设计文档](documents/数据库设计文档.md) - 数据库表结构设计
- [API接口文档](documents/API接口文档.md) - RESTful API规范
- [开发规范文档](documents/开发规范文档.md) - 编码规范和最佳实践
- [阶段1修复说明](documents/阶段1修复说明.md) - 最新Bug修复和功能增强

## 🆕 最近更新 (2025-12-12)

### Bug修复
1. ✅ **修复脚本执行状态卡住问题** - 状态现在能正确更新到"执行完毕"
2. ✅ **添加实时输出显示** - 带时间戳和脚本名称的彩色输出
3. ✅ **改进脚本选择交互** - 使用复选框模式，支持全选/反选
4. ✅ **修复时间显示功能** - 实时显示执行时间（HH:MM:SS）

详见：[阶段1修复说明](documents/阶段1修复说明.md)

## ⚠️ 常见问题

### Q: 运行时出现 "ModuleNotFoundError: No module named 'AppCode'"
**A:** 请使用 `python run.py` 启动，不要直接运行 `python AppCode/main.py`

### Q: 脚本输出不实时显示
**A:** 在测试脚本中使用 `print(..., flush=True)` 或设置环境变量 `PYTHONUNBUFFERED=1`

### Q: 如何选择多个脚本执行？
**A:** 在脚本浏览器中，直接点击脚本前的复选框即可，支持全选/反选按钮

## 🛠️ 开发

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/unit/test_validators.py

# 生成覆盖率报告
pytest --cov=AppCode --cov-report=html
```

### 代码检查

```bash
# 代码格式化
black AppCode/

# 代码检查
pylint AppCode/

# 类型检查
mypy AppCode/
```

## 🤝 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 LICENSE 文件

## 👥 团队

- 开发团队

## 📞 联系方式

- 技术支持: support@example.com
- 问题反馈: issues@example.com

---

**注意**: 本项目专为车载ECU测试设计，脚本按顺序执行以确保硬件资源独占。