@echo off
REM 快速发布脚本 (Windows版本)
REM 用法: release.bat <version>
REM 示例: release.bat 1.1.0

setlocal enabledelayedexpansion

set VERSION=%1

REM 检查参数
if "%VERSION%"=="" (
    echo [错误] 请提供版本号
    echo 用法: release.bat ^<version^>
    echo 示例: release.bat 1.1.0
    exit /b 1
)

echo ========================================
echo 🚀 开始发布版本 %VERSION%
echo ========================================

REM 1. 检查工作目录
echo.
echo 📋 检查工作目录...
git status -s
if errorlevel 1 (
    echo [警告] 工作目录有未提交的更改
    set /p CONTINUE="是否继续? (y/n): "
    if /i not "!CONTINUE!"=="y" exit /b 1
)

REM 2. 更新版本号提示
echo.
echo 📝 请手动更新 version.py 中的版本号为: %VERSION%
set /p UPDATED="版本号已更新? (y/n): "
if /i not "%UPDATED%"=="y" (
    echo [已取消] 发布已取消
    exit /b 1
)

REM 3. 运行测试（如果有）
if exist "tests\run_all_tests.py" (
    echo.
    echo 🧪 运行测试...
    python tests\run_all_tests.py
    if errorlevel 1 (
        echo [错误] 测试失败，请修复后再发布
        exit /b 1
    )
)

REM 4. 提交更改
echo.
echo 💾 提交更改...
git add .
git commit -m "chore: bump version to %VERSION%"

REM 5. 创建标签
echo.
echo 🏷️  创建标签 v%VERSION%...
git tag -a "v%VERSION%" -m "Release version %VERSION%"

REM 6. 推送到远程
echo.
echo 📤 推送到远程仓库...
git push origin main
if errorlevel 1 git push origin master
git push origin "v%VERSION%"

echo.
echo ========================================
echo ✅ 发布完成！
echo ========================================
echo.
echo 📦 GitHub Actions 正在自动构建...
echo 🔗 查看构建进度:
echo    https://github.com/YWB9806/OBC-DCDC-AutoTest/actions
echo.
echo 📋 发布页面:
echo    https://github.com/YWB9806/OBC-DCDC-AutoTest/releases/tag/v%VERSION%

endlocal