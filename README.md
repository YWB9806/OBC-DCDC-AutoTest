# OBC-DCDC AutoTest

一款基于 PyQt5 的桌面应用程序，用于批量管理和执行 Python 测试脚本，专为车载 OBC/DCDC ECU 自动化测试设计。

[![GitHub release](https://img.shields.io/github/v/release/YWB9806/OBC-DCDC-AutoTest)](https://github.com/YWB9806/OBC-DCDC-AutoTest/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 功能特性

- **脚本批量执行**：支持多脚本顺序执行，适用于需要硬件资源独占的 ECU 测试场景
- **测试方案管理**：创建和管理测试套件，一键加载并执行方案中的所有脚本
- **实时输出监控**：实时显示脚本输出，支持 ANSI 颜色和智能编码检测（UTF-8/GBK）
- **测试报告生成**：通过 Excel 模板自动生成测试报告，支持列映射配置和数据筛选
- **用户权限管理**：管理员/普通用户双角色，基于角色的权限控制（RBAC）
- **执行历史记录**：完整记录每次执行的输出、结果、耗时，支持按日期/方案/批次筛选
- **数据备份恢复**：自动备份数据库，支持一键恢复
- **自动更新检查**：支持从 GitHub Releases 检测并下载新版本

## 下载

前往 [Releases 页面](https://github.com/YWB9806/OBC-DCDC-AutoTest/releases) 下载最新版本。

| 平台 | 下载文件 |
|------|----------|
| Windows | `OBC-DCDC-AutoTest-Windows.zip` |
| Linux | `OBC-DCDC-AutoTest-Linux.tar.gz` |
| macOS | `OBC-DCDC-AutoTest-macOS.tar.gz` |

下载后解压，双击 `OBC-DCDC-AutoTest.exe`（Windows）即可运行，无需安装 Python 环境。

## 源码运行

### 环境要求

- Python 3.8+
- Windows / Linux / macOS

### 安装步骤

```bash
# 克隆项目
git clone https://github.com/YWB9806/OBC-DCDC-AutoTest.git
cd OBC-DCDC-AutoTest

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动程序
python run.py
```

> 注意：请使用 `python run.py` 启动，不要直接运行 `python AppCode/main.py`。

## 测试报告

1. 准备 Excel 报告模板（包含表头行）
2. 在"测试报告"标签页导入模板
3. 配置列映射：指定匹配列和数据字段的对应关系
4. 选择日期范围、测试方案、执行批次
5. 点击"加载数据"，然后"生成预览"或"导出报告"

## 项目结构

```
OBC-DCDC-AutoTest/
├── AppCode/                        # 应用代码
│   ├── core/                      # 核心层（执行引擎、脚本管理、DI容器）
│   ├── services/                  # 服务层（执行、脚本、用户、备份等）
│   ├── repositories/              # 数据访问层
│   ├── data_access/               # 数据库实现（SQLite）
│   ├── infrastructure/            # 基础设施（缓存、日志、配置）
│   ├── ui/                        # UI层（主窗口、各个面板、对话框）
│   └── utils/                     # 工具模块
├── config/                        # 配置文件
├── documents/                     # 开发文档
├── tests/                         # 测试用例
├── TestScripts/                   # 测试脚本目录
├── build.spec                     # PyInstaller 打包配置
├── requirements.txt               # 依赖列表
├── version.py                     # 版本信息
└── run.py                         # 启动入口
```

## 文档

详细文档请查看 [`documents/`](documents/) 目录：

- [架构设计文档](documents/架构设计文档.md)
- [数据库设计文档](documents/数据库设计文档.md)
- [API 接口文档](documents/API接口文档.md)
- [部署指南](documents/部署指南.md)
- [插件开发指南](documents/插件开发指南.md)

## 开发

```bash
# 运行测试
pytest

# 代码格式化
black AppCode/

# 代码检查
pylint AppCode/
```

## 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 [MIT](LICENSE) 许可证。
