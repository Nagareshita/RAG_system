# tabs/managers/workflow_manager.py
from PySide6.QtCore import QThread, Signal
from typing import Dict, Any


class WorkflowManager(QThread):
    """ワークフロー実行管理クラス"""
    log_signal = Signal(str)
    result_signal = Signal(dict)
    
    def __init__(self, design_data: Dict[str, Any], prompt: str, design_name: str, image_path: str = ""):
        super().__init__()
        self.design_data = design_data
        self.prompt = prompt
        self.design_name = design_name
        self.image_path = image_path
    
    def run(self):
        """ワークフロー実行のメインロジック"""
        try:
            from utils.workflow_factory import WorkflowFactory
            from utils.llm_manager import LLMManager  
            from utils.vector_manager import VectorManager
            
            self.emit_log("--- デバッグ: インポート開始 ---")
            
            # マネージャー初期化（シングルトンインスタンス取得）
            llm_manager = LLMManager()
            vector_manager = VectorManager()  # 同じインスタンスが返される
            
            # ワークフロー構築
            workflow = WorkflowFactory.create_workflow_engine(
                config_dict=self.design_data,
                llm_manager=llm_manager,
                vector_manager=vector_manager
            )
            
            # ログマネージャーにGUIコールバック設定
            workflow.log_manager.set_gui_callback(lambda msg: self.log_signal.emit(msg))
            
            self.emit_log("LangGraphワークフロー実行開始")
            
            # 画像パスがある場合は初期状態に追加
            initial_state = {}
            if self.image_path:
                from utils.key_registry import KeyRegistry
                initial_state[KeyRegistry.IMAGE_PATH] = self.image_path
                self.emit_log(f"画像パスを設定: {self.image_path}")
            
            results = workflow.execute(self.prompt, initial_state=initial_state)
            self.result_signal.emit(results)
            
            # 🔥 重要: 実行完了後のメモリクリーンアップは既にworkflow.execute内で実行済み
            # （LangGraphWorkflowEngine._cleanup_after_execution()がfinally句で自動実行）
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.emit_log(f"ワークフロー実行エラー: {str(e)}")
            self.emit_log(f"エラー詳細:\n{error_details}")
            error_results = {'final_result': None, 'error': str(e), 'error_details': error_details}
            self.result_signal.emit(error_results)

    def emit_log(self, message: str):
        """リアルタイムログメッセージを表示"""
        self.log_signal.emit(message)
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()

    def _emit_analyzer_details(self):
        """Analyzer詳細情報の出力"""
        try:
            # 閾値設定情報の表示
            thresholds = self.design_data.get('thresholds', {}).get('analyzer', {})
            if thresholds:
                self.log_signal.emit("=== 設定閾値一覧 ===")
                for key, config in thresholds.items():
                    value = config.get('value', '未設定')
                    self.log_signal.emit(f"{key}: {value}")
        except Exception:
            pass

    def _emit_llm_response_details(self):
        """LLM応答詳細情報の出力"""
        try:
            # WorkflowEngineから最新のcurrent_dataを取得
            if hasattr(self, '_last_current_data'):
                data = self._last_current_data
                
                # LLM応答詳細
                response_length = data.get('llm_response_length', 0)
                if response_length > 0:
                    self.log_signal.emit("=== LLM応答詳細 ===")
                    self.log_signal.emit(f"応答サイズ: {response_length} 文字")
                
                # パース済みパラメータ詳細
                params_count = data.get('parsed_fields_count', 0)
                if params_count > 0:
                    self.log_signal.emit("=== パース済みパラメータ ===")
                    self.log_signal.emit(f"パラメータ総数: {params_count} 個")
                    
                    # 主要パラメータの表示
                    key_params = ['intent', 'complexity', 'analyzer_confidence', 'optimized_search_query']
                    for param in key_params:
                        if param in data:
                            value = data[param]
                            if isinstance(value, float):
                                display_value = f"{value:.2f}"
                            elif isinstance(value, str) and len(value) > 80:
                                display_value = f"{value[:80]}..."
                            else:
                                display_value = str(value)
                            self.log_signal.emit(f"{param}: {display_value}")
        except Exception:
            pass