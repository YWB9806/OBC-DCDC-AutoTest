# Git提交指令 - v1.1.0

## 版本信息
- **版本号**: v1.1.0
- **发布日期**: 2025-12-23
- **主要更新**: 修复用户权限保存问题，支持默认用户创建

## 修改文件列表
1. `AppCode/services/user_service.py` - 修复create_user方法，添加can_view_results参数
2. `AppCode/ui/user_panel.py` - 修复用户创建时传递can_view_results值
3. `init_admin_user.py` - 支持创建默认用户（已脱敏）
4. `version.py` - 更新版本号到1.1.0
5. `CHANGELOG.md` - 添加v1.1.0更新日志

## Git提交步骤

### 1. 查看修改状态
```bash
git status
```

### 2. 添加修改的文件
```bash
git add AppCode/services/user_service.py
git add AppCode/ui/user_panel.py
git add init_admin_user.py
git add version.py
git add CHANGELOG.md
```

或者一次性添加所有修改：
```bash
git add .
```

### 3. 提交更改
```bash
git commit -m "fix: 修复用户权限保存问题并支持默认用户创建 (v1.1.0)

- 修复创建用户时can_view_results权限未正确保存的bug
- 在UserService.create_user()方法中添加can_view_results参数
- 在用户面板创建用户时正确传递权限值
- 超级管理员自动拥有查看结果权限
- 支持在init_admin_user.py中创建默认用户
- 对敏感信息进行脱敏处理
- 更新版本号到v1.1.0
- 更新CHANGELOG.md"
```

### 4. 推送到远程仓库
```bash
# 推送到main分支
git push origin main

# 或推送到master分支（根据你的仓库配置）
git push origin master
```

### 5. 创建版本标签（可选但推荐）
```bash
# 创建带注释的标签
git tag -a v1.1.0 -m "Release v1.1.0: 修复用户权限保存问题"

# 推送标签到远程
git push origin v1.1.0

# 或推送所有标签
git push origin --tags
```

## 完整的一键提交脚本

### Windows (PowerShell)
```powershell
# 保存为 commit_v1.1.0.ps1
git add .
git commit -m "fix: 修复用户权限保存问题并支持默认用户创建 (v1.1.0)

- 修复创建用户时can_view_results权限未正确保存的bug
- 在UserService.create_user()方法中添加can_view_results参数
- 在用户面板创建用户时正确传递权限值
- 超级管理员自动拥有查看结果权限
- 支持在init_admin_user.py中创建默认用户
- 对敏感信息进行脱敏处理
- 更新版本号到v1.1.0
- 更新CHANGELOG.md"

git push origin main
git tag -a v1.1.0 -m "Release v1.1.0: 修复用户权限保存问题"
git push origin v1.1.0

Write-Host "✅ 代码已成功提交并推送到远程仓库！"
Write-Host "✅ 版本标签 v1.1.0 已创建并推送！"
```

### Linux/macOS (Bash)
```bash
#!/bin/bash
# 保存为 commit_v1.1.0.sh

git add .
git commit -m "fix: 修复用户权限保存问题并支持默认用户创建 (v1.1.0)

- 修复创建用户时can_view_results权限未正确保存的bug
- 在UserService.create_user()方法中添加can_view_results参数
- 在用户面板创建用户时正确传递权限值
- 超级管理员自动拥有查看结果权限
- 支持在init_admin_user.py中创建默认用户
- 对敏感信息进行脱敏处理
- 更新版本号到v1.1.0
- 更新CHANGELOG.md"

git push origin main
git tag -a v1.1.0 -m "Release v1.1.0: 修复用户权限保存问题"
git push origin v1.1.0

echo "✅ 代码已成功提交并推送到远程仓库！"
echo "✅ 版本标签 v1.1.0 已创建并推送！"
```

## 注意事项

1. **确认分支**: 确保你在正确的分支上（通常是main或master）
2. **检查远程**: 确认远程仓库配置正确 `git remote -v`
3. **权限验证**: 确保你有推送权限
4. **敏感信息**: 已对init_admin_user.py中的敏感信息进行脱敏处理
5. **版本标签**: 建议创建版本标签便于版本管理和回滚

## 验证提交

提交后可以通过以下方式验证：

```bash
# 查看提交历史
git log --oneline -5

# 查看标签
git tag -l

# 查看远程分支状态
git branch -r
```

## 回滚方案（如需要）

如果提交后发现问题，可以使用以下命令回滚：

```bash
# 回滚到上一个提交（保留修改）
git reset --soft HEAD~1

# 回滚到上一个提交（丢弃修改）
git reset --hard HEAD~1

# 删除远程标签
git push origin :refs/tags/v1.1.0

# 删除本地标签
git tag -d v1.1.0