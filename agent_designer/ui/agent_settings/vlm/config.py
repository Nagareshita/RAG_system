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
        # プリセット設定
        'preset': None,  # None = プリセット未使用
        
        # 基本生成パラメータ
        'temperature': 0.7,
        'top_p': 0.8,
        'top_k': 20,
        'do_sample': True,
        
        # トークン数制御
        'max_new_tokens': 512,
        'min_new_tokens': 1,
        
        # 繰り返し制御
        'repetition_penalty': 1.0,
        'no_repeat_ngram_size': 0,
        
        # ビームサーチ設定
        'num_beams': 1,
        'length_penalty': 1.0,
        'diversity_penalty': 0.0,
        'early_stopping': False,
        
        # ログ設定
        'logging_level': 'VERBOSE',
        
        # モデルパス（固定）
        'model_path': './vlm/SAIL-VL2-2B'
    }
    
    # プリセット定義（model_managerと一致）
    PRESETS = {
        'accurate': '正確性重視/OCR寄り',
        'balanced': 'バランス型',
        'ocr': 'OCR特化',
        'qa': '質問応答',
        'code': 'コード生成',
        'creative': '創造的生成',
        'summary': '要約',
        'json': 'JSON出力'
    }
    
    # 設定項目スキーマ
    SETTINGS_SCHEMA = {
        'preset': {
            'type': 'combo',
            'label': 'プリセット',
            'options': [
                (None, 'なし（カスタム設定）'),
                ('accurate', '正確性重視/OCR寄り'),
                ('balanced', 'バランス型'),
                ('ocr', 'OCR特化'),
                ('qa', '質問応答'),
                ('code', 'コード生成'),
                ('creative', '創造的生成'),
                ('summary', '要約'),
                ('json', 'JSON出力')
            ],
            'description': 'タスク別の推奨設定（選択するとパラメータが自動設定されます）',
            'width': 250
        },
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
        'do_sample': {
            'type': 'bool',
            'label': 'サンプリング有効化',
            'description': 'Trueでサンプリング、Falseで貪欲/ビーム探索',
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
        'min_new_tokens': {
            'type': 'int',
            'label': '最小トークン数',
            'description': '生成する最小トークン数',
            'min_value': 1,
            'max_value': 1024,
            'width': 150
        },
        'repetition_penalty': {
            'type': 'float',
            'label': 'Repetition Penalty',
            'description': '繰り返しペナルティ (1.0=ペナルティなし)',
            'min_value': 1.0,
            'max_value': 2.0,
            'step': 0.05,
            'width': 150
        },
        'no_repeat_ngram_size': {
            'type': 'int',
            'label': 'No-Repeat N-gram Size',
            'description': 'N-gramの繰り返し抑制 (0=抑制なし)',
            'min_value': 0,
            'max_value': 10,
            'width': 150
        },
        'num_beams': {
            'type': 'int',
            'label': 'ビーム数 (Beam Search)',
            'description': 'ビーム探索のビーム数 (1=貪欲探索)',
            'min_value': 1,
            'max_value': 10,
            'width': 150
        },
        'length_penalty': {
            'type': 'float',
            'label': 'Length Penalty',
            'description': 'シーケンス長ペナルティ (1.0=ペナルティなし)',
            'min_value': 0.5,
            'max_value': 2.0,
            'step': 0.05,
            'width': 150
        },
        'diversity_penalty': {
            'type': 'float',
            'label': 'Diversity Penalty',
            'description': 'ビーム間の多様性ペナルティ (0.0=なし)',
            'min_value': 0.0,
            'max_value': 2.0,
            'step': 0.1,
            'width': 150
        },
        'early_stopping': {
            'type': 'bool',
            'label': '早期停止',
            'description': 'ビーム探索の早期停止を有効化',
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
        
        # Min tokens範囲チェック
        min_tokens = config_values.get('min_new_tokens', 1)
        if not (1 <= min_tokens <= 1024):
            errors.append("最小トークン数は1～1024の範囲である必要があります")
        
        # Min/Max tokens 整合性チェック
        if min_tokens > max_tokens:
            errors.append("最小トークン数は最大トークン数以下である必要があります")
        
        # Repetition penalty範囲チェック
        rep_penalty = config_values.get('repetition_penalty', 1.0)
        if not (1.0 <= rep_penalty <= 2.0):
            errors.append("Repetition Penaltyは1.0～2.0の範囲である必要があります")
        
        # Length penalty範囲チェック
        length_penalty = config_values.get('length_penalty', 1.0)
        if not (0.5 <= length_penalty <= 2.0):
            errors.append("Length Penaltyは0.5～2.0の範囲である必要があります")
        
        # Diversity penalty範囲チェック
        diversity_penalty = config_values.get('diversity_penalty', 0.0)
        if not (0.0 <= diversity_penalty <= 2.0):
            errors.append("Diversity Penaltyは0.0～2.0の範囲である必要があります")
        
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
