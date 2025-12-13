"""
更新检查服务
负责检查应用程序更新、下载更新信息
"""

import json
import logging
import platform
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib import request
from urllib.error import URLError, HTTPError

from version import (
    get_version_string,
    get_full_version_string,
    is_newer_version,
    UPDATE_CONFIG,
    PLATFORM_INFO
)


class UpdateService:
    """更新检查服务"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._last_check_time: Optional[datetime] = None
        self._cached_update_info: Optional[Dict[str, Any]] = None
        self._check_interval = UPDATE_CONFIG.get('check_interval', 86400)
        
    def check_for_updates(self, force: bool = False) -> Optional[Dict[str, Any]]:
        """
        检查更新
        
        Args:
            force: 是否强制检查（忽略检查间隔）
        
        Returns:
            更新信息字典，如果没有更新则返回None
            {
                'has_update': bool,
                'latest_version': str,
                'current_version': str,
                'release_notes': str,
                'download_url': str,
                'release_date': str,
                'is_prerelease': bool
            }
        """
        try:
            # 检查是否需要检查更新
            if not force and not self._should_check_update():
                self.logger.info("距离上次检查时间未超过间隔，使用缓存的更新信息")
                return self._cached_update_info
            
            # 获取当前版本
            current_version = get_version_string()
            
            # 从GitHub获取最新版本信息
            latest_info = self._fetch_latest_release()
            
            if not latest_info:
                self.logger.warning("无法获取最新版本信息")
                return None
            
            latest_version = latest_info.get('tag_name', '').lstrip('v')
            
            # 检查是否为预发布版本
            is_prerelease = latest_info.get('prerelease', False)
            show_prerelease = UPDATE_CONFIG.get('show_prerelease', False)
            
            # 如果是预发布版本且不显示预发布版本，则跳过
            if is_prerelease and not show_prerelease:
                self.logger.info(f"跳过预发布版本: {latest_version}")
                return None
            
            # 比较版本
            has_update = is_newer_version(current_version, latest_version)
            
            # 构建更新信息
            update_info = {
                'has_update': has_update,
                'latest_version': latest_version,
                'current_version': current_version,
                'release_notes': latest_info.get('body', ''),
                'download_url': self._get_download_url(latest_info),
                'release_date': latest_info.get('published_at', ''),
                'is_prerelease': is_prerelease,
                'html_url': latest_info.get('html_url', '')
            }
            
            # 更新缓存
            self._last_check_time = datetime.now()
            self._cached_update_info = update_info
            
            if has_update:
                self.logger.info(f"发现新版本: {latest_version} (当前版本: {current_version})")
            else:
                self.logger.info(f"当前已是最新版本: {current_version}")
            
            return update_info
            
        except Exception as e:
            self.logger.error(f"检查更新时发生错误: {e}", exc_info=True)
            return None
    
    def _should_check_update(self) -> bool:
        """判断是否应该检查更新"""
        if self._last_check_time is None:
            return True
        
        elapsed = datetime.now() - self._last_check_time
        return elapsed.total_seconds() >= self._check_interval
    
    def _fetch_latest_release(self) -> Optional[Dict[str, Any]]:
        """
        从GitHub API获取最新发布信息
        
        Returns:
            发布信息字典
        """
        api_url = UPDATE_CONFIG.get('github_api')
        
        if not api_url:
            self.logger.error("未配置GitHub API地址")
            return None
        
        try:
            self.logger.info(f"正在从GitHub获取最新版本信息: {api_url}")
            
            # 创建请求
            req = request.Request(
                api_url,
                headers={
                    'User-Agent': 'Python Script Batch Executor',
                    'Accept': 'application/vnd.github.v3+json'
                }
            )
            
            # 发送请求
            with request.urlopen(req, timeout=10) as response:
                data = response.read()
                release_info = json.loads(data.decode('utf-8'))
                return release_info
                
        except HTTPError as e:
            self.logger.error(f"HTTP错误: {e.code} - {e.reason}")
            return None
        except URLError as e:
            self.logger.error(f"网络错误: {e.reason}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析错误: {e}")
            return None
        except Exception as e:
            self.logger.error(f"获取发布信息时发生未知错误: {e}", exc_info=True)
            return None
    
    def _get_download_url(self, release_info: Dict[str, Any]) -> str:
        """
        获取适合当前平台的下载地址
        
        Args:
            release_info: GitHub发布信息
        
        Returns:
            下载地址
        """
        try:
            # 获取当前平台
            system = platform.system().lower()
            
            # 获取平台信息
            platform_info = PLATFORM_INFO.get(system, PLATFORM_INFO.get('windows'))
            extension = platform_info.get('extension', 'exe')
            
            # 从assets中查找匹配的文件
            assets = release_info.get('assets', [])
            
            for asset in assets:
                name = asset.get('name', '').lower()
                
                # 检查文件名是否包含平台标识和扩展名
                if system in name and name.endswith(f'.{extension}'):
                    return asset.get('browser_download_url', '')
            
            # 如果没有找到匹配的asset，返回发布页面URL
            return release_info.get('html_url', '')
            
        except Exception as e:
            self.logger.error(f"获取下载地址时发生错误: {e}")
            return release_info.get('html_url', '')
    
    def get_current_version_info(self) -> Dict[str, str]:
        """
        获取当前版本信息
        
        Returns:
            版本信息字典
        """
        return {
            'version': get_version_string(),
            'full_version': get_full_version_string(),
            'platform': platform.system(),
            'python_version': platform.python_version()
        }
    
    def reset_check_interval(self):
        """重置检查间隔（强制下次检查）"""
        self._last_check_time = None
        self._cached_update_info = None
        self.logger.info("已重置更新检查间隔")


# 单例实例
_update_service_instance: Optional[UpdateService] = None


def get_update_service() -> UpdateService:
    """获取更新服务单例"""
    global _update_service_instance
    if _update_service_instance is None:
        _update_service_instance = UpdateService()
    return _update_service_instance


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("更新服务测试")
    print("=" * 60)
    
    service = get_update_service()
    
    # 获取当前版本信息
    print("\n当前版本信息:")
    current_info = service.get_current_version_info()
    for key, value in current_info.items():
        print(f"  {key}: {value}")
    
    # 检查更新
    print("\n检查更新...")
    update_info = service.check_for_updates(force=True)
    
    if update_info:
        print("\n更新信息:")
        for key, value in update_info.items():
            if key == 'release_notes' and len(str(value)) > 100:
                print(f"  {key}: {str(value)[:100]}...")
            else:
                print(f"  {key}: {value}")
    else:
        print("\n无法获取更新信息")