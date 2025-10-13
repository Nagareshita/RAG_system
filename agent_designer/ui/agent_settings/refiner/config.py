# agent_designer/ui/agent_settings/refiner/config_new.py
"""
Refiner設定の完全統合（Analyzerパターン準拠 + Section動的管理）
- UI表示情報（色、説明）
- デフォルト設定値 
- SETTINGS_SCHEMA（Section以外）
- Section専用データ管理
- 実行用thresholds形式
- 設定検証ルール
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field, asdict


@dataclass
class RefinerSection:
    """Refinerセクション定義（既存の構造を維持）"""
    id: str
    title: str
    content_type: str = "summary"
    target_length_ratio: int = 10
    includes: List[str] = field(default_factory=lambda: ["key_points"])
    tone: str = "professional_concise"
    data_focus: str = "unified_analysis"
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RefinerSection':
        """辞書から作成"""
        return cls(**data)


class RefinerConfig:
    """Refiner設定の統合管理クラス（Analyzerパターン準拠）"""
    
    # UI表示情報
    UI_INFO = {
        'name': 'Refiner',
        'description': '文書生成・整形エージェント',
        'color': {
            # ティール系（緑青）: 文書整形を示す
            'fill': (60, 160, 140, 200),
            'border': (90, 200, 170),
            'text': (255, 255, 255)
        }
    }
    
    # デフォルト設定値
    DEFAULT_VALUES = {
        # 基本設定
        'min_answer_length': 10000,
        'max_answer_length': 15000,
        'enable_regeneration': False,
        'logging_level': 'VERBOSE',
        'llm_max_tokens': 16000,  # LLM最大トークン数
        
        # フォーマット設定
        'use_code_blocks': True,
        'include_citations': True,
        'structure_with_headers': True,
        'technical_terminology': 'preserve',
        'expert_attribution': True,
        'response_format': 'technical_documentation',
        
        # 出力構造設定（注意: sectionsはここには含めない）
        'output_structure': {
            'response_format': 'technical_documentation',
            'formatting_rules': {
                'use_code_blocks': True,
                'include_citations': True,
                'structure_with_headers': True,
                'technical_terminology': 'preserve',
                'expert_attribution': True
            }
        },
        
        # LLMプロンプト設定（新形式：5つのプロンプト）
        'llm_prompts': {
            'generation_instruction': '以下の構成で{min_answer_length}文字以上{max_answer_length}文字以下の包括的な技術文書を生成してください。Modelicaライブラリ専門家と熱流体専門家の両方の分析結果を統合し、ASTデータとPDF文献の両方を活用した高品質な実装ガイドを提供してください。',
            'section_instruction': '各セクションは指定された比率と内容focusに従って構成してください。専門家の具体的な分析内容（facts, insights, recommendations）を活用し、引用情報を適切に含めてください。',
            'output_format': '指定されたセクション構成に従い、技術的正確性を最優先として実装者が即座に活用できる詳細で構造化された説明を提供してください。',
            'integration_focus': '2つの専門分野の知見を効果的に統合し、Routerによる品質管理の結果を適切に表現してください。',
            'code_generation_focus': 'コードの生成に重点を置き、retrieved_documentsの内容を必ずコードに含めてください。よくわからない内容がある場合はコードを生成せず、わからないと回答してください。'
        }
    }
    
    # 設定項目スキーマ（Section以外の通常設定）
    SETTINGS_SCHEMA = {
        'min_answer_length': {
            'type': 'int',
            'label': '最小回答長',
            'description': '生成する文書の最小文字数',
            'min_value': 100,
            'max_value': 50000,
            'width': 120
        },
        'max_answer_length': {
            'type': 'int',
            'label': '最大回答長',
            'description': '生成する文書の最大文字数',
            'min_value': 1000,
            'max_value': 100000,
            'width': 120
        },
        'enable_regeneration': {
            'type': 'checkbox',
            'label': '再生成有効化',
            'description': '品質が低い場合の自動再生成機能'
        },
        'logging_level': {
            'type': 'combo',
            'label': 'ログレベル',
            'options': [
                ('VERBOSE', '詳細 (VERBOSE)'),
                ('MINIMAL', '最小限 (MINIMAL)')
            ],
            'description': 'ログ出力の詳細度'
        },
        'use_code_blocks': {
            'type': 'checkbox',
            'label': 'コードブロック使用',
            'description': 'コードや例示にコードブロックを使用'
        },
        'include_citations': {
            'type': 'checkbox',
            'label': '引用包含',
            'description': '参考資料の引用を含める'
        },
        'structure_with_headers': {
            'type': 'checkbox',
            'label': 'ヘッダー構造化',
            'description': 'ヘッダーによる構造化を行う'
        },
        'technical_terminology': {
            'type': 'combo',
            'label': '専門用語処理',
            'options': [
                ('preserve', '保持'),
                ('simplify', '簡素化'),
                ('explain', '説明付き')
            ],
            'description': '専門用語の処理方法'
        },
        'expert_attribution': {
            'type': 'checkbox',
            'label': '専門家帰属',
            'description': '専門家による検証を明示'
        },
        'response_format': {
            'type': 'combo',
            'label': 'レスポンス形式',
            'options': [
                ('technical_documentation', '技術文書'),
                ('academic_paper', '学術論文'),
                ('user_manual', 'ユーザーマニュアル'),
                ('report', 'レポート')
            ],
            'description': '出力文書の形式'
        }
    }
    
    # Section管理用のプロパティ
    @classmethod
    def get_default_sections(cls) -> List[RefinerSection]:
        """デフォルトセクション構成を取得"""
        return [
            RefinerSection(
                id="introduction",
                title="概要",
                content_type="summary",
                target_length_ratio=15,
                includes=["background", "objectives"],
                tone="professional_concise",
                data_focus="problem_definition"
            ),
            RefinerSection(
                id="analysis",
                title="詳細分析",
                content_type="analysis",
                target_length_ratio=50,
                includes=["technical_details", "implementation"],
                tone="technical_detailed",
                data_focus="technical_solution"
            ),
            RefinerSection(
                id="conclusion",
                title="結論",
                content_type="conclusion",
                target_length_ratio=20,
                includes=["summary", "recommendations"],
                tone="professional_conclusive",
                data_focus="actionable_results"
            )
        ]
    
    @classmethod
    def get_default_config(cls):
        """GUIで使用するデフォルト設定を返却"""
        config = cls.DEFAULT_VALUES.copy()
        # Sectionsを辞書リストとして追加
        config['sections'] = [section.to_dict() for section in cls.get_default_sections()]
        return config
    
    @classmethod
    def get_execution_thresholds(cls, config_values):
        """実行用のthresholds形式に変換"""
        thresholds = {}
        
        # 基本設定をthresholds形式に変換
        for key, value in config_values.items():
            if key == 'sections':
                # Sectionsは特別処理
                sections_data = []
                for section_dict in value:
                    if isinstance(section_dict, dict):
                        sections_data.append(section_dict)
                    else:
                        sections_data.append(section_dict.to_dict())
                
                thresholds['output_structure'] = {
                    'value': {
                        'response_format': config_values.get('response_format', 'technical_documentation'),
                        'sections': sections_data,
                        'formatting_rules': {
                            'use_code_blocks': config_values.get('use_code_blocks', True),
                            'include_citations': config_values.get('include_citations', True),
                            'structure_with_headers': config_values.get('structure_with_headers', True),
                            'technical_terminology': config_values.get('technical_terminology', 'preserve'),
                            'expert_attribution': config_values.get('expert_attribution', True)
                        }
                    }
                }
            elif key in ['use_code_blocks', 'include_citations', 'structure_with_headers', 
                        'technical_terminology', 'expert_attribution', 'response_format']:
                # フォーマット設定はoutput_structureに含まれるのでスキップ
                continue
            else:
                thresholds[key] = {"value": value}
        
        return thresholds
    
    @classmethod
    def validate_config(cls, config_values):
        """設定値のバリデーション"""
        errors = []
        warnings = []
        
        # 基本設定チェック
        min_len = config_values.get('min_answer_length', 0)
        max_len = config_values.get('max_answer_length', 0)
        
        if min_len <= 0:
            errors.append("最小回答長は1以上である必要があります")
        
        if max_len <= min_len:
            errors.append("最大回答長は最小回答長より大きい必要があります")
        
        # Section設定チェック
        sections = config_values.get('sections', [])
        if not sections:
            warnings.append("セクションが定義されていません")
        else:
            total_ratio = sum(s.get('target_length_ratio', 0) for s in sections)
            if total_ratio <= 0:
                errors.append("セクションの総文字数比率が0以下です")
            
            # セクションID重複チェック
            section_ids = [s.get('id', '') for s in sections]
            if len(section_ids) != len(set(section_ids)):
                errors.append("重複するセクションIDがあります")
        
        # LLMプロンプトチェック
        llm_prompts = config_values.get('llm_prompts', {})
        required_prompts = ['document_generation', 'content_refinement']
        for prompt_key in required_prompts:
            if prompt_key not in llm_prompts or not llm_prompts[prompt_key].strip():
                warnings.append(f"推奨プロンプト'{prompt_key}'が設定されていません")
        
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
    
    @classmethod
    def sections_from_config(cls, config_values) -> List[RefinerSection]:
        """設定値からSectionリストを作成"""
        sections_data = config_values.get('sections', [])
        sections = []
        for section_dict in sections_data:
            if isinstance(section_dict, dict):
                sections.append(RefinerSection.from_dict(section_dict))
            else:
                sections.append(section_dict)
        return sections
    
    @classmethod
    def sections_to_config(cls, sections: List[RefinerSection]) -> List[Dict[str, Any]]:
        """SectionリストからConfigデータに変換"""
        return [section.to_dict() for section in sections]