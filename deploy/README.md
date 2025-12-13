# 部署脚本说明

本目录包含用于构建和部署应用程序的各种脚本。

## 📁 文件说明

### build_all.sh
本地构建脚本，用于在当前平台构建应用程序。

**用法**:
```bash
chmod +x build_all.sh
./build_all.sh
```

**功能**:
- 自动检测当前平台
- 清理旧的构建文件
- 安装依赖
- 使用PyInstaller构建
- 创建压缩包
- 可选的测试运行

**支持平台**:
- Linux
- macOS
- Windows (Git Bash/MSYS2)

---

## 🚀 快速开始

### 1. 准备环境

```bash
# 安装Python 3.8+
python --version

# 安装依赖
pip install -r ../requirements.txt
pip install pyinstaller
```

### 2. 本地构建

```bash
# Linux/macOS
./build_all.sh

# Windows (PowerShell)
python -m PyInstaller ../build.spec
```

### 3. 测试构建结果

```bash
# Linux
cd ../dist/PythonScriptBatchExecutor
./PythonScriptBatchExecutor

# macOS
open ../dist/PythonScriptBatchExecutor.app

# Windows
cd ..\dist\PythonScriptBatchExecutor
PythonScriptBatchExecutor.exe
```

---

## 📦 构建输出

构建完成后，文件将位于 `dist/` 目录：

```
dist/
├── PythonScriptBatchExecutor/          # 应用程序目录
│   ├── PythonScriptBatchExecutor       # 可执行文件 (Linux/macOS)
│   ├── PythonScriptBatchExecutor.exe   # 可执行文件 (Windows)
│   ├── _internal/                      # 依赖文件
│   └── ...
└── PythonScriptBatchExecutor-*.zip     # 压缩包
```

---

## 🔧 自定义构建

### 修改构建配置

编辑 `../build.spec` 文件：

```python
# 添加数据文件
datas = [
    ('path/to/file', 'destination'),
]

# 添加隐藏导入
hiddenimports = [
    'module_name',
]

# 排除模块
excludes = [
    'unused_module',
]
```

### 添加图标

1. 准备图标文件：
   - Windows: `assets/icon.ico`
   - macOS: `assets/icon.icns`
   - Linux: `assets/icon.png`

2. 在 `build.spec` 中引用：
```python
exe = EXE(
    ...
    icon='assets/icon.ico',
)
```

---

## 🌐 多平台构建

### 使用GitHub Actions（推荐）

推送标签即可自动构建所有平台：

```bash
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0
```

### 手动多平台构建

需要在每个平台上分别运行：

1. **Windows**:
```powershell
python -m PyInstaller build.spec
Compress-Archive -Path dist\PythonScriptBatchExecutor -DestinationPath dist\App-Windows.zip
```

2. **Linux**:
```bash
pyinstaller build.spec
cd dist && tar -czf App-Linux.tar.gz PythonScriptBatchExecutor
```

3. **macOS**:
```bash
pyinstaller build.spec
cd dist && tar -czf App-macOS.tar.gz PythonScriptBatchExecutor.app
```

---

## 🐛 常见问题

### 问题1: 缺少模块

**错误**: `ModuleNotFoundError: No module named 'xxx'`

**解决**:
```python
# 在 build.spec 中添加
hiddenimports = ['xxx']
```

### 问题2: 打包体积过大

**解决**:
```python
# 在 build.spec 中排除不需要的模块
excludes = [
    'matplotlib',
    'numpy',
    'pandas',
]
```

### 问题3: 运行时找不到文件

**解决**:
```python
# 在 build.spec 中添加数据文件
datas = [
    ('config/app_config.json', 'config'),
]
```

### 问题4: Linux上缺少库

**解决**:
```bash
# 安装必要的系统库
sudo apt-get install -y libxcb-xinerama0 libxcb-cursor0
```

---

## 📊 构建优化

### 减小体积

1. 使用UPX压缩：
```python
exe = EXE(
    ...
    upx=True,
)
```

2. 排除不需要的模块
3. 使用虚拟环境构建

### 提高启动速度

1. 使用目录模式而非单文件模式
2. 减少导入的模块
3. 延迟加载大型库

---

## 🔐 代码签名

### Windows

```powershell
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist\App.exe
```

### macOS

```bash
codesign --deep --force --verify --verbose --sign "Developer ID" dist/App.app
```

---

## 📝 检查清单

构建前检查：

- [ ] 版本号已更新
- [ ] 依赖已安装
- [ ] 测试已通过
- [ ] 配置文件正确
- [ ] 图标文件存在
- [ ] 文档已更新

构建后检查：

- [ ] 应用可以正常启动
- [ ] 所有功能正常
- [ ] 文件大小合理
- [ ] 压缩包完整

---

## 📞 获取帮助

如遇到问题：

1. 查看 [发布部署指南](../documents/发布部署指南.md)
2. 查看 [PyInstaller文档](https://pyinstaller.org/)
3. 提交 [Issue](https://github.com/YWB9806/OBC-DCDC-AutoTest/issues)

---

**最后更新**: 2025-12-13