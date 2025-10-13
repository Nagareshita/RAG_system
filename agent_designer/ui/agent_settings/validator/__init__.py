# agent_designer/ui/agent_settings/validator/__init__.py
"""
Validator設定統合パッケージ
完全なValidator設定管理機能を提供
"""

from .config import ValidatorConfig
from .settings_ui import ValidatorSettingsUI

__all__ = ['ValidatorConfig', 'ValidatorSettingsUI']

# パッケージ情報
AGENT_TYPE = 'Validator'
PACKAGE_VERSION = '1.0.0'