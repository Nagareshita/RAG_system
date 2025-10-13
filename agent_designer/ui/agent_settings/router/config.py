# agent_designer/ui/agent_settings/router/config.py
"""
Router設定の完全統合（Analyzerパターン準拠）
- UI表示情報（色、説明）
- デフォルト設定値
- 設定項目スキーマ定義
- 実行用thresholds形式
- 設定検証ルール
"""

from typing import Dict, List, Any

class RouterConfig:
    """Router設定の統合管理クラス（Analyzerパターン準拠）"""
    
    # UI表示情報
    UI_INFO = {
        'name': 'Router',
        'description': '条件分岐・ルーティングエージェント',
        'color': {
            # 紫系: 分岐を示す（視認性強化）
            'fill': (140, 80, 180, 200),
            'border': (180, 120, 210),
            'text': (255, 255, 255)
        }
    }
    
    # デフォルト設定値
    DEFAULT_VALUES = {
        'max_iterations': 1,
        'logging_level': 'VERBOSE',
        'routing_rules': {
            'conditions': {},
            'default': {
                'target': '',
                'decision': 'proceed_to_target',
                'description': 'デフォルトルート'
            },
            'max_iterations_exceeded': {
                'target': '',
                'decision': 'max_iterations_exceeded',
                'description': '最大繰り返し回数超過ルート'
            }
        }
    }
    
    # 設定項目の定義（UI生成とバリデーション用）
    SETTINGS_SCHEMA = {
        'max_iterations': {
            'type': 'int',
            'label': '最大繰り返し回数',
            'description': 'Router実行の最大繰り返し回数',
            'width': 100
        },
        'logging_level': {
            'type': 'combo',
            'label': 'ログ出力レベル',
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
    def get_ui_info(cls):
        """UI表示用の情報を返却"""
        return cls.UI_INFO.copy()
    
    @classmethod
    def get_settings_schema(cls):
        """設定項目のスキーマを返却"""
        return cls.SETTINGS_SCHEMA.copy()
    
    @classmethod
    def get_execution_thresholds(cls, config_values: Dict[str, Any]):
        """実行用閾値形式に変換"""
        return {
            "max_iterations": {"value": int(config_values.get('max_iterations', cls.DEFAULT_VALUES['max_iterations']))},
            "logging_level": {"value": config_values.get('logging_level', cls.DEFAULT_VALUES['logging_level'])},
            "routing_rules": {"value": config_values.get('routing_rules', cls.DEFAULT_VALUES['routing_rules'])}
        }
    
    @classmethod
    def validate_config(cls, config_values: Dict[str, Any]) -> Dict[str, Any]:
        """設定値のバリデーション"""
        errors = []
        warnings = []
        
        # max_iterations validation
        max_iterations = config_values.get('max_iterations', cls.DEFAULT_VALUES['max_iterations'])
        try:
            max_iterations_int = int(max_iterations)
            if max_iterations_int < 1:
                errors.append("最大繰り返し回数は1以上である必要があります")
            elif max_iterations_int > 10:
                warnings.append("最大繰り返し回数が10を超えています。パフォーマンスに影響する可能性があります")
        except (ValueError, TypeError):
            errors.append("最大繰り返し回数は数値である必要があります")
        
        # logging_level validation
        logging_level = config_values.get('logging_level', cls.DEFAULT_VALUES['logging_level'])
        valid_levels = ['VERBOSE', 'MINIMAL']
        if logging_level not in valid_levels:
            errors.append(f"ログレベルは {valid_levels} のいずれかである必要があります")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @classmethod
    def get_reference_values(cls):
        """参照値（編集不可）を返却"""
        return {
            'default_max_iterations': cls.DEFAULT_VALUES['max_iterations'],
            'supported_log_levels': ['VERBOSE', 'MINIMAL']
        }
    
    # ===== 統合アクセスメソッド（agent_types廃止後の互換） =====
    
    @classmethod
    def get_default_node_config(cls):
        """
        デフォルトノード設定を返却（agent_types.defaults互換）
        GUI内部で使用される形式
        """
        return cls.DEFAULT_VALUES.copy()
    
    @classmethod
    def get_gui_metadata(cls):
        """
        GUI表示用メタデータを返却（agent_types互換）
        色情報、名前、説明を含む
        """
        return {
            'name': cls.UI_INFO['name'],
            'description': cls.UI_INFO['description'],
            'color': cls.UI_INFO['color'].copy()
        }


# 条件管理用のヘルパークラス
class RouterCondition:
    """単一の条件を表現するクラス"""
    
    def __init__(self, key: str = "", operator: str = ">=", value: float = 0.0):
        self.key = key
        self.operator = operator
        self.value = value
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'key': self.key,
            'operator': self.operator,
            'value': self.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RouterCondition':
        """辞書から作成"""
        return cls(
            key=data.get('key', ''),
            operator=data.get('operator', '>='),
            value=data.get('value', 0.0)
        )


class RouterConditionGroup:
    """条件グループを表現するクラス"""
    
    def __init__(self, name: str, conditions: List[RouterCondition] = None, logic: str = "AND"):
        self.name = name
        self.conditions = conditions or []
        self.logic = logic  # "AND" or "OR"
        self.target = ""
        self.description = ""
    
    def add_condition(self, condition: RouterCondition):
        """条件を追加"""
        self.conditions.append(condition)
    
    def remove_condition(self, index: int):
        """条件を削除"""
        if 0 <= index < len(self.conditions):
            self.conditions.pop(index)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'conditions': [c.to_dict() for c in self.conditions],
            'logic': self.logic,
            'target': self.target,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> 'RouterConditionGroup':
        """辞書から作成"""
        conditions = [RouterCondition.from_dict(c) for c in data.get('conditions', [])]
        group = cls(name, conditions, data.get('logic', 'AND'))
        group.target = data.get('target', '')
        group.description = data.get('description', '')
        return group


# 利用可能なフィールドオプション
AVAILABLE_FIELDS = {
    'validator_confidence': 'Validator信頼度',
    'retriever_confidence': 'Retriever信頼度', 
    'expert_confidence': 'Expert信頼度',
    'facts_count': 'Facts数',
    'insights_count': 'Insights数',
    'recommendations_count': 'Recommendations数'
}

COMPARISON_OPERATORS = {
    '>=': '以上',
    '<=': '以下',
    '>': 'より大きい',
    '<': 'より小さい',
    '==': '等しい',
    '!=': '等しくない'
}