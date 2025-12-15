@echo off
chcp 65001 >nul
echo ============================================================
echo Git提交脚本 - v1.0.6
echo ============================================================
echo.

echo 1. 检查Git状态...
git status
echo.

echo 2. 添加所有修改的文件...
git add .
echo.

echo 3. 提交更改...
git commit -m "Release v1.0.6: 修复测试结果判定问题并提供数据修复工具

主要更新：
- 修复执行引擎中测试结果提取逻辑
- 添加v1.0.4数据修复工具
- 提供完整的数据修复手册

详细内容请查看CHANGELOG.md"
echo.

echo 4. 创建版本标签...
git tag -a v1.0.6 -m "Release v1.0.6

修复内容：
- 测试结果判定逻辑修复
- v1.0.4历史数据修复工具
- 完整的使用文档

详见：CHANGELOG.md"
echo.

echo 5. 推送到远程仓库...
echo 即将执行: git push origin main
echo 即将执行: git push origin v1.0.6
echo.
echo 按任意键继续推送，或按Ctrl+C取消...
pause >nul

git push origin main
git push origin v1.0.6

echo.
echo ============================================================
echo ✅ 提交完成！
echo ============================================================
echo.
echo 版本: v1.0.6
echo 标签: v1.0.6
echo 分支: main
echo.
echo 下一步：
echo 1. 访问 GitHub 仓库查看提交
echo 2. 在 GitHub 上创建 Release（如需要）
echo 3. 更新文档和发布说明
echo.
pause