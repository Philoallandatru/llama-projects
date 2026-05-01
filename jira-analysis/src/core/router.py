"""Issue Type 路由器

根据 issue type 路由到对应的分析 profile。
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProfileConfig:
    """分析 Profile 配置"""
    name: str
    description: str
    issue_types: list[str]
    prompt_template: str
    output_sections: list[str]


class Router:
    """Issue Type 路由器

    职责：
    - 加载 profiles 配置
    - 根据 issue type 路由到对应的分析 profile
    - 提供默认 profile
    """

    def __init__(self, config_path: Path):
        """初始化路由器

        Args:
            config_path: profiles/config.json 路径
        """
        self.config_path = config_path
        self.profiles: Dict[str, ProfileConfig] = {}
        self.default_profile_name: str = "general"
        self.issue_type_mapping: Dict[str, str] = {}

        self._load_config()

    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 加载 profiles
            for profile_name, profile_data in config.get("profiles", {}).items():
                profile = ProfileConfig(
                    name=profile_data["name"],
                    description=profile_data["description"],
                    issue_types=profile_data["issue_types"],
                    prompt_template=profile_data["prompt_template"],
                    output_sections=profile_data["output_sections"]
                )
                self.profiles[profile_name] = profile

                # 构建 issue type -> profile 映射
                for issue_type in profile.issue_types:
                    self.issue_type_mapping[issue_type.lower()] = profile_name

            # 设置默认 profile
            self.default_profile_name = config.get("default_profile", "general")

            logger.info(
                f"Router loaded: {len(self.profiles)} profiles, "
                f"{len(self.issue_type_mapping)} issue type mappings"
            )

        except Exception as e:
            logger.error(f"Failed to load router config: {e}")
            raise

    def route(self, issue_type: str) -> ProfileConfig:
        """根据 issue type 路由到对应的 profile

        Args:
            issue_type: Issue type 名称

        Returns:
            ProfileConfig 对象
        """
        # 标准化 issue type（转小写）
        issue_type_lower = issue_type.lower()

        # 查找匹配的 profile
        profile_name = self.issue_type_mapping.get(
            issue_type_lower,
            self.default_profile_name
        )

        profile = self.profiles.get(profile_name)

        if not profile:
            logger.warning(
                f"Profile '{profile_name}' not found, using default '{self.default_profile_name}'"
            )
            profile = self.profiles[self.default_profile_name]

        logger.info(f"Routed issue type '{issue_type}' to profile '{profile.name}'")
        return profile

    def get_profile(self, profile_name: str) -> Optional[ProfileConfig]:
        """直接获取指定的 profile

        Args:
            profile_name: Profile 名称

        Returns:
            ProfileConfig 对象或 None
        """
        return self.profiles.get(profile_name)

    def list_profiles(self) -> list[ProfileConfig]:
        """列出所有可用的 profiles

        Returns:
            ProfileConfig 列表
        """
        return list(self.profiles.values())
