#!/bin/bash
# 快速发布脚本
# 用法: ./release.sh <version>
# 示例: ./release.sh 1.1.0

set -e  # 遇到错误立即退出

VERSION=$1

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查参数
if [ -z "$VERSION" ]; then
    echo -e "${RED}错误: 请提供版本号${NC}"
    echo "用法: ./release.sh <version>"
    echo "示例: ./release.sh 1.1.0"
    exit 1
fi

# 验证版本号格式
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}错误: 版本号格式不正确${NC}"
    echo "版本号应该是 x.y.z 格式，例如: 1.0.0"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🚀 开始发布版本 ${GREEN}$VERSION${NC}"
echo -e "${BLUE}========================================${NC}"

# 1. 检查工作目录是否干净
echo -e "\n${YELLOW}📋 检查工作目录...${NC}"
if [[ -n $(git status -s) ]]; then
    echo -e "${RED}警告: 工作目录有未提交的更改${NC}"
    git status -s
    read -p "是否继续? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 2. 更新版本号提示
echo -e "\n${YELLOW}📝 请手动更新 version.py 中的版本号为: $VERSION${NC}"
read -p "版本号已更新? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}已取消发布${NC}"
    exit 1
fi

# 3. 运行测试（如果有）
if [ -f "tests/run_all_tests.py" ]; then
    echo -e "\n${YELLOW}🧪 运行测试...${NC}"
    python tests/run_all_tests.py || {
        echo -e "${RED}测试失败，请修复后再发布${NC}"
        exit 1
    }
fi

# 4. 提交更改
echo -e "\n${YELLOW}💾 提交更改...${NC}"
git add .
git commit -m "chore: bump version to $VERSION" || echo "没有需要提交的更改"

# 5. 创建标签
echo -e "\n${YELLOW}🏷️  创建标签 v$VERSION...${NC}"
git tag -a "v$VERSION" -m "Release version $VERSION"

# 6. 推送到远程
echo -e "\n${YELLOW}📤 推送到远程仓库...${NC}"
git push origin main || git push origin master
git push origin "v$VERSION"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 发布完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${BLUE}📦 GitHub Actions 正在自动构建...${NC}"
echo -e "${BLUE}🔗 查看构建进度:${NC}"
echo -e "   https://github.com/YWB9806/OBC-DCDC-AutoTest/actions"
echo -e "\n${BLUE}📋 发布页面:${NC}"
echo -e "   https://github.com/YWB9806/OBC-DCDC-AutoTest/releases/tag/v$VERSION"