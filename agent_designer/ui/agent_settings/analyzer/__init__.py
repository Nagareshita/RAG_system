# agent_designer/ui/agent_settings/analyzer/__init__.py
"""
Analyzer設定統合パッケージ
完全なAnalyzer設定管理機能を提供
"""

from .config import AnalyzerConfig
from .settings_ui import AnalyzerSettingsUI

__all__ = ['AnalyzerConfig', 'AnalyzerSettingsUI']

# パッケージ情報
AGENT_TYPE = 'Analyzer'
PACKAGE_VERSION = '1.0.0'