# agent_designer/ui/agent_settings/vlm/config.py
"""
VLM (Vision Language Model) 設定
SAIL-VL2-2B を使用した画像認識・質問応答エージェント
"""

from typing import Dict, Any


class VLMConfig:
    """VLM設定の統合管理クラス"""
    
    # UI表示情報
    UI_INFO = {
        'name': 'VLM',
        'description': 'Vision Language Model - 画像認識・質問応答エージェント',
        'color': {
            # シアン系（マルチモーダル・AI）
            'fill': (60, 180, 200, 200),
            'border': (90, 210, 230),
            'text': (255, 255, 255)
        }
    }
    
    # デフォルト設定値
    DEFAULT_VALUES = {
        # 生成パラメータ
        'temperature': 0.7,
        'top_p': 0.8,
        'top_k': 20,
        'max_new_tokens': 512,
        
        # ログ設定
        'logging_level': 'VERBOSE',
        
        # モデルパス（固定）
        'model_path': './vlm/SAIL-VL2-2B'
    }
    
    # 設定項目スキーマ
    SETTINGS_SCHEMA = {
        'temperature': {
            'type': 'float',
            'label': 'Temperature',
            'description': '生成のランダム性 (高いほど多様、低いほど確実)',
            'min_value': 0.0,
            'max_value': 2.0,
            'step': 0.1,
            'width': 150
        },
        'top_p': {
            'type': 'float',
            'label': 'Top-p (Nucleus Sampling)',
            'description': '累積確率による選択範囲',
            'min_value': 0.0,
            'max_value': 1.0,
            'step': 0.05,
            'width': 150
        },
        'top_k': {
            'type': 'int',
            'label': 'Top-k',
            'description': '上位k個の候補から選択',
            'min_value': 1,
            'max_value': 100,
            'width': 150
        },
        'max_new_tokens': {
            'type': 'int',
            'label': '最大トークン数',
            'description': '生成する最大トークン数',
            'min_value': 50,
            'max_value': 2048,
            'width': 150
        },
        'logging_level': {
            'type': 'combo',
            'label': 'ログレベル',
            'options': [
                ('VERBOSE', '詳細 (VERBOSE)'),
                ('MINIMAL', '最小限 (MINIMAL)')
            ],
            'description': 'ログ出力の詳細度'
        }
    }
    
    @classmethod
    def get_default_config(cls):
        """デフォルト設定を返却"""
        return cls.DEFAULT_VALUES.copy()
    
    @classmethod
    def get_execution_thresholds(cls, config_values):
        """実行用のthresholds形式に変換"""
        thresholds = {}
        
        for key, value in config_values.items():
            if key in ['log_level', 'logging_level']:
                continue
            
            if isinstance(value, dict) and "value" in value:
                thresholds[key] = value
            else:
                thresholds[key] = {"value": value}
        
        return thresholds
    
    @classmethod
    def validate_config(cls, config_values):
        """設定値のバリデーション"""
        errors = []
        warnings = []
        
        # Temperature範囲チェック
        temp = config_values.get('temperature', 0.7)
        if not (0.0 <= temp <= 2.0):
            errors.append("Temperatureは0.0～2.0の範囲である必要があります")
        
        # Top-p範囲チェック
        top_p = config_values.get('top_p', 0.8)
        if not (0.0 <= top_p <= 1.0):
            errors.append("Top-pは0.0～1.0の範囲である必要があります")
        
        # Top-k範囲チェック
        top_k = config_values.get('top_k', 20)
        if not (1 <= top_k <= 100):
            errors.append("Top-kは1～100の範囲である必要があります")
        
        # Max tokens範囲チェック
        max_tokens = config_values.get('max_new_tokens', 512)
        if not (50 <= max_tokens <= 2048):
            errors.append("最大トークン数は50～2048の範囲である必要があります")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @classmethod
    def get_ui_info(cls):
        """UI表示用の情報を返却"""
        return cls.UI_INFO.copy()
    
    @classmethod
    def get_settings_schema(cls):
        """設定項目のスキーマを返却"""
        return cls.SETTINGS_SCHEMA.copy()
    
    @classmethod
    def get_ui_fields(cls):
        """UI設定フィールドのリストを返却"""
        return list(cls.SETTINGS_SCHEMA.keys())
