#!/bin/bash
# 本地构建所有平台的脚本
# 注意：需要在对应平台上运行

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🔨 开始构建所有平台${NC}"
echo -e "${BLUE}========================================${NC}"

# 获取版本号
VERSION=$(python -c "from version import get_version_string; print(get_version_string())")
echo -e "\n${YELLOW}📦 当前版本: ${GREEN}$VERSION${NC}"

# 检测当前平台
PLATFORM=$(uname -s)
echo -e "${YELLOW}🖥️  当前平台: ${GREEN}$PLATFORM${NC}"

# 清理旧的构建
echo -e "\n${YELLOW}🧹 清理旧的构建文件...${NC}"
rm -rf build dist

# 安装依赖
echo -e "\n${YELLOW}📦 检查依赖...${NC}"
pip install -r requirements.txt
pip install pyinstaller

# 构建
echo -e "\n${YELLOW}🔨 开始构建...${NC}"
pyinstaller build.spec

# 创建压缩包
echo -e "\n${YELLOW}📦 创建压缩包...${NC}"
cd dist

case "$PLATFORM" in
    Linux*)
        echo -e "${YELLOW}创建 Linux 压缩包...${NC}"
        tar -czf "OBC-DCDC-AutoTest-${VERSION}-Linux.tar.gz" OBC-DCDC-AutoTest
        echo -e "${GREEN}✅ Linux 构建完成${NC}"
        ;;
    Darwin*)
        echo -e "${YELLOW}创建 macOS 压缩包...${NC}"
        tar -czf "OBC-DCDC-AutoTest-${VERSION}-macOS.tar.gz" OBC-DCDC-AutoTest.app
        echo -e "${GREEN}✅ macOS 构建完成${NC}"
        ;;
    MINGW*|MSYS*|CYGWIN*)
        echo -e "${YELLOW}创建 Windows 压缩包...${NC}"
        # 在Windows上使用PowerShell创建zip
        powershell -Command "Compress-Archive -Path OBC-DCDC-AutoTest -DestinationPath OBC-DCDC-AutoTest-${VERSION}-Windows.zip"
        echo -e "${GREEN}✅ Windows 构建完成${NC}"
        ;;
    *)
        echo -e "${YELLOW}未知平台，创建通用压缩包...${NC}"
        tar -czf "OBC-DCDC-AutoTest-${VERSION}-${PLATFORM}.tar.gz" OBC-DCDC-AutoTest
        ;;
esac

cd ..

# 显示结果
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✅ 构建完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "\n${YELLOW}📁 构建文件位置:${NC}"
ls -lh dist/*.{zip,tar.gz} 2>/dev/null || ls -lh dist/

# 测试运行
echo -e "\n${YELLOW}🧪 是否测试运行? (y/n)${NC}"
read -r TEST_RUN

if [[ $TEST_RUN =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}启动应用...${NC}"
    case "$PLATFORM" in
        Linux*)
            ./dist/OBC-DCDC-AutoTest/OBC-DCDC-AutoTest
            ;;
        Darwin*)
            open ./dist/OBC-DCDC-AutoTest.app
            ;;
        MINGW*|MSYS*|CYGWIN*)
            ./dist/OBC-DCDC-AutoTest/OBC-DCDC-AutoTest.exe
            ;;
    esac
fi

echo -e "\n${GREEN}🎉 所有操作完成！${NC}"