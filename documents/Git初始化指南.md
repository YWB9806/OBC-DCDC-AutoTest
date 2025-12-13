# Git初始化和首次部署指南

## 🔧 问题说明

当前项目还不是Git仓库，需要先初始化Git并连接到GitHub。

---

## 📋 步骤1: 初始化Git仓库

```bash
# 在项目根目录执行
cd D:\AI\Projects\Python脚本批量执行工具

# 初始化Git仓库
git init

# 配置用户信息（如果还没配置）
git config user.name "YWB9806"
git config user.email "your.email@example.com"
```

---

## 📋 步骤2: 连接到GitHub仓库

### 方式A: 如果GitHub仓库已存在

```bash
# 添加远程仓库
git remote add origin https://github.com/YWB9806/OBC-DCDC-AutoTest.git

# 验证远程仓库
git remote -v
```

### 方式B: 如果GitHub仓库不存在

1. 访问：https://github.com/new
2. 创建新仓库：
   - Repository name: `OBC-DCDC-AutoTest`
   - Description: `Python脚本批量执行工具`
   - Public 或 Private（根据需要选择）
   - 不要勾选 "Initialize this repository with a README"
3. 创建后，执行：

```bash
git remote add origin https://github.com/YWB9806/OBC-DCDC-AutoTest.git
```

---

## 📋 步骤3: 添加.gitignore文件

创建 `.gitignore` 文件，排除不需要提交的文件：

```bash
# 创建.gitignore
echo # Python > .gitignore
echo __pycache__/ >> .gitignore
echo *.py[cod] >> .gitignore
echo *$py.class >> .gitignore
echo *.so >> .gitignore
echo .Python >> .gitignore
echo build/ >> .gitignore
echo dist/ >> .gitignore
echo *.egg-info/ >> .gitignore
echo .pytest_cache/ >> .gitignore
echo .coverage >> .gitignore
echo htmlcov/ >> .gitignore
echo # IDE >> .gitignore
echo .vscode/ >> .gitignore
echo .idea/ >> .gitignore
echo *.swp >> .gitignore
echo *.swo >> .gitignore
echo # 数据库 >> .gitignore
echo *.db >> .gitignore
echo *.sqlite >> .gitignore
echo # 日志 >> .gitignore
echo *.log >> .gitignore
echo logs/ >> .gitignore
echo # 备份 >> .gitignore
echo backups/ >> .gitignore
echo # 临时文件 >> .gitignore
echo *.tmp >> .gitignore
echo temp/ >> .gitignore
```

---

## 📋 步骤4: 首次提交

```bash
# 添加所有文件
git add .

# 首次提交
git commit -m "feat: 初始提交 - Python脚本批量执行工具

- 完整的应用程序代码
- 版本发布和自动更新系统
- GitHub Actions自动构建配置
- 完整的文档"

# 设置主分支名称为main
git branch -M main

# 推送到GitHub
git push -u origin main
```

---

## 📋 步骤5: 创建首个Release

```bash
# 创建标签
git tag -a v1.0.0 -m "Release version 1.0.0

首个正式版本发布

主要功能：
- Python脚本批量执行
- 用户认证和权限管理
- 实时输出监控
- 执行历史记录
- 测试套件管理
- 性能监控
- 自动更新检查"

# 推送标签（触发GitHub Actions自动构建）
git push origin v1.0.0
```

---

## 📋 步骤6: 监控构建

1. 访问：https://github.com/YWB9806/OBC-DCDC-AutoTest/actions
2. 查看构建进度
3. 等待构建完成

---

## ✅ 完整命令序列

```bash
# 1. 初始化
cd D:\AI\Projects\Python脚本批量执行工具
git init
git config user.name "YWB9806"
git config user.email "your.email@example.com"

# 2. 连接远程仓库
git remote add origin https://github.com/YWB9806/OBC-DCDC-AutoTest.git

# 3. 添加文件
git add .

# 4. 提交
git commit -m "feat: 初始提交 - Python脚本批量执行工具"

# 5. 推送
git branch -M main
git push -u origin main

# 6. 创建标签
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

---

## 🔐 如果需要身份验证

### 使用Personal Access Token

1. 访问：https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 勾选 `repo` 权限
4. 生成并复制token
5. 推送时使用token作为密码

### 或者使用SSH

```bash
# 生成SSH密钥
ssh-keygen -t ed25519 -C "your.email@example.com"

# 添加到GitHub
# 复制公钥内容：
type %USERPROFILE%\.ssh\id_ed25519.pub

# 访问 https://github.com/settings/keys 添加SSH密钥

# 修改远程仓库URL为SSH
git remote set-url origin git@github.com:YWB9806/OBC-DCDC-AutoTest.git
```

---

## 🐛 常见问题

### Q: 推送时要求输入用户名密码？

**A**: GitHub已不支持密码认证，需要使用Personal Access Token或SSH密钥。

### Q: 推送被拒绝？

**A**: 可能是远程仓库有内容，执行：
```bash
git pull origin main --allow-unrelated-histories
git push origin main
```

### Q: 文件太大无法推送？

**A**: 检查.gitignore是否正确排除了大文件（如dist/、build/等）

---

## 📞 需要帮助？

如果遇到问题，请提供：
1. 完整的错误信息
2. 执行的命令
3. 当前的Git状态（`git status`）

---

**创建时间**: 2025-12-13