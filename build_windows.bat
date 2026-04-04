@echo off
REM Windows平台打包脚本 - v1.2.0
REM 用于快速打包测试版本
REM 使用方法：在虚拟环境中运行此脚本

echo ========================================
echo 🚀 开始打包 OBC-DCDC-AutoTest v1.2.0
echo ========================================

REM 1. 检查Python环境
echo.
echo 📋 检查Python环境...
python --version
if errorlevel 1 (
    echo [错误] 未找到Python，请先激活虚拟环境
    echo 提示: 运行 script_executor\Scripts\activate
    pause
    exit /b 1
)

REM 2. 检查虚拟环境
echo.
echo 📋 检查虚拟环境...
python -c "import sys; print('虚拟环境:', sys.prefix)"

REM 3. 检查PyInstaller
echo.
echo 📋 检查PyInstaller...
python -c "import PyInstaller; print('PyInstaller版本:', PyInstaller.__version__)" 2>nul
if errorlevel 1 (
    echo [错误] 未安装PyInstaller
    echo 请在虚拟环境中安装: pip install pyinstaller
    pause
    exit /b 1
)

REM 4. 检查必要的依赖
echo.
echo 📋 检查项目依赖...
python -c "import PyQt5; print('PyQt5: OK')" 2>nul || echo [警告] PyQt5未安装
python -c "import sqlalchemy; print('SQLAlchemy: OK')" 2>nul || echo [警告] SQLAlchemy未安装

REM 5. 清理旧的构建文件
echo.
echo 🧹 清理旧的构建文件...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM 6. 开始打包
echo.
echo 📦 开始打包...
python -m PyInstaller build.spec

if errorlevel 1 (
    echo.
    echo [错误] 打包失败！
    pause
    exit /b 1
)

REM 7. 检查打包结果
echo.
echo ✅ 打包完成！
echo.
echo 📁 输出目录: dist\OBC-DCDC-AutoTest\
echo 📄 可执行文件: dist\OBC-DCDC-AutoTest\OBC-DCDC-AutoTest.exe
echo.

REM 8. 创建压缩包（可选）
set /p CREATE_ZIP="是否创建压缩包? (y/n): "
if /i "%CREATE_ZIP%"=="y" (
    echo.
    echo 📦 创建压缩包...
    powershell -Command "Compress-Archive -Path 'dist\OBC-DCDC-AutoTest' -DestinationPath 'dist\OBC-DCDC-AutoTest-v1.2.0-Windows.zip' -Force"
    echo ✅ 压缩包已创建: dist\OBC-DCDC-AutoTest-v1.2.0-Windows.zip
)

echo.
echo ========================================
echo ✅ 打包完成！
echo ========================================
echo.
echo 💡 提示:
echo    1. 可执行文件位于: dist\OBC-DCDC-AutoTest\
echo    2. 双击 OBC-DCDC-AutoTest.exe 运行程序
echo    3. 可以将整个文件夹复制到其他电脑测试
echo.

pause