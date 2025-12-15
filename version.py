"""
版本配置文件
用于管理应用程序版本信息和更新检查
"""

__version__ = "1.0.7"
__version_info__ = (1, 0, 7)

# 版本信息
VERSION = {
    "major": 1,
    "minor": 0,
    "patch": 7,
    "build": 0,
    "release_date": "2025-12-15",
    "release_type": "stable"  # stable, beta, alpha
}

# 应用信息
APP_INFO = {
    "name": "Python脚本批量执行工具",
    "name_en": "OBC-DCDC AutoTest",
    "description": "一个功能强大的Python脚本批量执行和管理工具",
    "author": "YWB9806",
    "author_email": "your.email@example.com",
    "license": "MIT",
    "homepage": "https://github.com/YWB9806/OBC-DCDC-AutoTest",
    "repository": "https://github.com/YWB9806/OBC-DCDC-AutoTest",
    "issues": "https://github.com/YWB9806/OBC-DCDC-AutoTest/issues"
}

# 更新配置
UPDATE_CONFIG = {
    # GitHub Release API
    "github_api": "https://api.github.com/repos/YWB9806/OBC-DCDC-AutoTest/releases/latest",
    
    # 更新检查间隔（秒）
    "check_interval": 86400,  # 24小时
    
    # 是否自动检查更新（v1.0.4改为手动检查）
    "auto_check": False,
    
    # 是否显示预发布版本
    "show_prerelease": False,
    
    # 下载地址模板
    "download_url_template": "https://github.com/YWB9806/OBC-DCDC-AutoTest/releases/download/{version}/OBC-DCDC-AutoTest-{version}-{platform}.{ext}"
}

# 平台信息
PLATFORM_INFO = {
    "windows": {
        "name": "Windows",
        "extension": "exe",
        "installer_extension": "msi"
    },
    "linux": {
        "name": "Linux",
        "extension": "AppImage",
        "installer_extension": "deb"
    },
    "darwin": {
        "name": "macOS",
        "extension": "dmg",
        "installer_extension": "pkg"
    }
}


def get_version_string():
    """获取版本字符串"""
    return __version__


def get_full_version_string():
    """获取完整版本字符串（包含构建号）"""
    v = VERSION
    version_str = f"{v['major']}.{v['minor']}.{v['patch']}"
    if v['build'] > 0:
        version_str += f".{v['build']}"
    if v['release_type'] != 'stable':
        version_str += f"-{v['release_type']}"
    return version_str


def get_version_info():
    """获取版本信息字典"""
    return {
        "version": get_version_string(),
        "full_version": get_full_version_string(),
        "version_info": __version_info__,
        "release_date": VERSION['release_date'],
        "release_type": VERSION['release_type'],
        **APP_INFO
    }


def compare_versions(version1: str, version2: str) -> int:
    """
    比较两个版本号
    
    Args:
        version1: 版本号1 (如 "1.0.0")
        version2: 版本号2 (如 "1.0.1")
    
    Returns:
        -1: version1 < version2
         0: version1 == version2
         1: version1 > version2
    """
    def parse_version(version: str) -> tuple:
        """解析版本号为元组"""
        # 移除预发布标签
        version = version.split('-')[0]
        parts = version.split('.')
        return tuple(int(p) for p in parts)
    
    v1 = parse_version(version1)
    v2 = parse_version(version2)
    
    if v1 < v2:
        return -1
    elif v1 > v2:
        return 1
    else:
        return 0


def is_newer_version(current: str, latest: str) -> bool:
    """
    检查是否有新版本
    
    Args:
        current: 当前版本
        latest: 最新版本
    
    Returns:
        True: 有新版本
        False: 无新版本
    """
    return compare_versions(current, latest) < 0


if __name__ == "__main__":
    # 测试代码
    print("=" * 60)
    print("版本信息")
    print("=" * 60)
    
    info = get_version_info()
    for key, value in info.items():
        print(f"{key:20s}: {value}")
    
    print("\n" + "=" * 60)
    print("版本比较测试")
    print("=" * 60)
    
    test_cases = [
        ("1.0.0", "1.0.1", -1),
        ("1.0.1", "1.0.0", 1),
        ("1.0.0", "1.0.0", 0),
        ("1.0.0", "2.0.0", -1),
        ("2.0.0", "1.9.9", 1),
    ]
    
    for v1, v2, expected in test_cases:
        result = compare_versions(v1, v2)
        status = "✓" if result == expected else "✗"
        print(f"{status} compare_versions('{v1}', '{v2}') = {result} (expected: {expected})")
    
    print("\n" + "=" * 60)
    print("新版本检查测试")
    print("=" * 60)
    
    test_cases = [
        ("1.0.0", "1.0.1", True),
        ("1.0.1", "1.0.0", False),
        ("1.0.0", "1.0.0", False),
    ]
    
    for current, latest, expected in test_cases:
        result = is_newer_version(current, latest)
        status = "✓" if result == expected else "✗"
        print(f"{status} is_newer_version('{current}', '{latest}') = {result} (expected: {expected})")