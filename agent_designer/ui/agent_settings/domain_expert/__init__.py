# agent_designer/ui/agent_settings/domain_expert/__init__.py
"""
Domain Expert設定統合パッケージ
完全なDomain Expert設定管理機能を提供
"""

from .config import DomainExpertConfig
from .settings_ui import DomainExpertSettingsUI

__all__ = ['DomainExpertConfig', 'DomainExpertSettingsUI']

# パッケージ情報
AGENT_TYPE = 'Domain Expert'
PACKAGE_VERSION = '1.0.0'