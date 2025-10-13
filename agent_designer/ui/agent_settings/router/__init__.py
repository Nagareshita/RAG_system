# agent_designer/ui/agent_settings/router/__init__.py
"""
Router設定統合パッケージ
完全なRouter設定管理機能を提供
"""

from .config import RouterConfig
from .settings_ui import RouterSettingsUI

__all__ = ['RouterConfig', 'RouterSettingsUI']

# パッケージ情報
AGENT_TYPE = 'Router'
PACKAGE_VERSION = '1.0.0'