# test2.json実行フロー完全図解（実装完全版）

## ✅ 全ファイル実装確認済み

すべてのコンポーネントの実装が確認できました！

---

## 📝 test2.json実行フロー（完全版）

### 【Phase 1】UIからボタンクリックまで

```
user_tab.py (PySide6 GUI - メインスレッド)
│
├─ PromptInputWidget
│   ├─ デザインファイル選択: test2.json を読み込み
│   │   └─ design_data = json.load(file)  # 辞書として読み込み
│   │
│   ├─ プロンプト入力: "冷蔵庫のモデルを作って"
│   │
│   └─ 送信ボタンクリック
│       ↓
│   emit send_requested.signal(
│       prompt="冷蔵庫のモデルを作って",
│       design_data={...test2.jsonの全内容...},
│       design_name="test2.json"
│   )
│
└─ UserTab.execute_workflow() シグナル受信
    ├─ self.prompt_widget.set_enabled(False)  # UI無効化
    ├─ self.log_widget.add_section_header("ワークフロー実行開始")
    ├─ self.log_widget.add_log(f"使用設計ファイル: test2.json")
    ├─ self.log_widget.add_log(f"プロンプト: 冷蔵庫のモデルを作って")
    │
    └─ WorkflowManager生成・起動
        ├─ self.workflow_manager = WorkflowManager(design_data, prompt, design_name)
        ├─ log_signal → log_widget.add_log_without_timestamp() 接続
        ├─ result_signal → handle_workflow_result() 接続
        ├─ finished → on_workflow_finished() 接続
        └─ self.workflow_manager.start()  # 別スレッド起動
```

**重要ポイント**:
- `design_data`は`test2.json`の完全な辞書オブジェクト
- WorkflowManagerは**QThread**なので`.start()`で**別スレッド実行**

---

### 【Phase 2】WorkflowManager.run()（別スレッド）

```python
# tabs/managers/workflow_manager.py (実装確認済み)

class WorkflowManager(QThread):
    log_signal = Signal(str)
    result_signal = Signal(dict)
    
    def __init__(self, design_data, prompt, design_name):
        super().__init__()
        self.design_data = design_data  # test2.json全体
        self.prompt = prompt            # "冷蔵庫のモデルを作って"
        self.design_name = design_name  # "test2.json"
    
    def run(self):
        """QThreadのrun()メソッド（別スレッドで自動実行）"""
        try:
            # ========== Step 2-1: モジュールインポート ==========
            from utils.workflow_factory import WorkflowFactory
            from utils.llm_manager import LLMManager  
            from utils.vector_manager import VectorManager
            
            self.emit_log("--- デバッグ: インポート開始 ---")
            
            # ========== Step 2-2: マネージャー初期化 ==========
            llm_manager = LLMManager()        # configs/llm_config.json 読み込み
            vector_manager = VectorManager()  # configs/vector_config.json 読み込み
            
            # ========== Step 2-3: ワークフローエンジン構築 ==========
            workflow = WorkflowFactory.create_workflow_engine(
                config_dict=self.design_data,  # test2.jsonの全内容
                llm_manager=llm_manager,
                vector_manager=vector_manager
            )
            
            # ========== Step 2-4: GUIコールバック設定 ==========
            workflow.log_manager.set_gui_callback(
                lambda msg: self.log_signal.emit(msg)
            )
            
            self.emit_log("LangGraphワークフロー実行開始")
            
            # ========== Step 2-5: ワークフロー実行 ==========
            results = workflow.execute(self.prompt)
            
            # ========== Step 2-6: 結果をメインスレッドに返却 ==========
            self.result_signal.emit(results)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.emit_log(f"ワークフロー実行エラー: {str(e)}")
            self.emit_log(f"エラー詳細:\n{error_details}")
            
            error_results = {
                'final_result': None,
                'error': str(e),
                'error_details': error_details
            }
            self.result_signal.emit(error_results)
    
    def emit_log(self, message: str):
        """リアルタイムログ出力"""
        self.log_signal.emit(message)
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()  # GUI更新を強制
```

**重要ポイント**:
- 別スレッドで実行されるため、メインスレッド（GUI）がブロックされない
- `log_signal`でリアルタイムログをGUIに送信
- `result_signal`で結果をGUIに送信

---

### 【Phase 3】WorkflowFactory.create_workflow_engine()

```python
# utils/workflow_factory.py (実装確認済み)

@staticmethod
def create_workflow_engine(config_dict, llm_manager, vector_manager):
    """test2.jsonから実行可能なワークフローを構築"""
    
    # ========== Step 3-1: 管理インスタンス生成 ==========
    log_manager = LogManager(config_dict)
    # ↓ config_dict["logging"]を読み込み
    # {
    #   "default_level": "VERBOSE",
    #   "node_specific_levels": {"1": "VERBOSE", "2": "VERBOSE", ...}
    # }
    
    threshold_manager = NodeThresholdManager(config_dict)
    # ↓ config_dict["node_thresholds"]を読み込み
    # + デフォルト値を自動適用（agent_settings/*/config.py から）
    # {
    #   "1": {"analysis_depth": {"value": "comprehensive"}, ...},
    #   "2": {"search_k": {"value": 6}, "use_reranker": {"value": true}, ...},
    #   ...
    # }
    
    # ========== Step 3-2: 全エージェントのインスタンス生成 ==========
    agent_instances = {}
    
    for node in config_dict["nodes"]:
        node_id = str(node["id"])
        node_type = node["type"]
        
        # エージェントクラス取得
        AgentClass = SUPPORTED_NODE_TYPES[node_type]
        # {
        #   "analyzer": AnalyzerExecutor,
        #   "retriever": RetrieverExecutor,
        #   "domain_expert": DomainExpertExecutor,
        #   "validator": ValidatorExecutor,
        #   "refiner": RefinerExecutor,
        #   "router": RouterExecutor
        # }
        
        # エージェント初期化
        if node_type == "retriever":
            agent = AgentClass(log_manager, threshold_manager, vector_manager)
        else:
            agent = AgentClass(log_manager, threshold_manager, llm_manager)
        
        # ノード固有設定を適用
        agent.set_node_config(node.get("config", {}), node_id)
        
        # 辞書に登録
        agent_key = f"{node_type}_{node_id}"
        agent_instances[agent_key] = agent
    
    # ========== Step 3-3: LangGraphワークフローエンジン構築 ==========
    return LangGraphWorkflowEngine(
        agents=agent_instances,
        log_manager=log_manager,
        threshold_manager=threshold_manager,
        config_dict=config_dict
    )
```

**test2.jsonから生成される8個のエージェント**:
```python
{
    "analyzer_1": AnalyzerExecutor(log_manager, threshold_manager, llm_manager),
    "retriever_2": RetrieverExecutor(log_manager, threshold_manager, vector_manager),
    "retriever_3": RetrieverExecutor(log_manager, threshold_manager, vector_manager),
    "domain_expert_4": DomainExpertExecutor(log_manager, threshold_manager, llm_manager),
    "domain_expert_5": DomainExpertExecutor(log_manager, threshold_manager, llm_manager),
    "validator_6": ValidatorExecutor(log_manager, threshold_manager, llm_manager),
    "refiner_7": RefinerExecutor(log_manager, threshold_manager, llm_manager),
    "router_9": RouterExecutor(log_manager, threshold_manager, llm_manager)
}
```

---

### 【Phase 4】LangGraphWorkflowEngine初期化

```python
# utils/langgraph_workflow_engine.py (実装確認済み)

class LangGraphWorkflowEngine:
    def __init__(self, agents, log_manager, threshold_manager, config_dict):
        self.agents = agents  # 上記8個のエージェント
        self.log_manager = log_manager
        self.threshold_manager = threshold_manager
        self.nodes = {node["id"]: node for node in config_dict["nodes"]}
        self.connections = config_dict["connections"]
        
        # ========== LangGraph StateGraphを構築 ==========
        self.workflow = self._build_workflow()
    
    def _build_workflow(self):
        """test2.jsonからLangGraphグラフを構築"""
        workflow = StateGraph(WorkflowState)
        
        # ========== 全8ノードをLangGraphに登録 ==========
        for node_id in [1, 2, 3, 4, 5, 6, 7, 9]:
            node_type = self.nodes[node_id]["type"]
            agent_key = f"{node_type}_{node_id}"
            
            # ノード実行関数を生成
            node_func = self._create_node_function(agent_key, str(node_id))
            workflow.add_node(f"node_{node_id}", node_func)
        
        # ========== test2.jsonのconnectionsからエッジを構築 ==========
        
        # 1. START → Analyzer(1)
        workflow.add_edge(START, "node_1")
        
        # 2. Analyzer(1) → [Retriever(2), Retriever(3)] 並列分岐
        workflow.add_edge("node_1", "node_2")
        workflow.add_edge("node_1", "node_3")
        
        # 3. [Retriever(2), Retriever(3)] → [DomainExpert(4), DomainExpert(5)] 並列継続
        workflow.add_edge("node_2", "node_4")
        workflow.add_edge("node_3", "node_5")
        
        # 4. [DomainExpert(4), DomainExpert(5)] → Validator(6) 並列合流
        workflow.add_edge("node_4", "node_6")
        workflow.add_edge("node_5", "node_6")
        
        # 5. Validator(6) → Router(9)
        workflow.add_edge("node_6", "node_9")
        
        # 6. Router(9) → 条件分岐
        workflow.add_conditional_edges(
            "node_9",
            self._create_router_condition("9"),
            {
                "condition_1": "node_1",            # 信頼度低→Analyzerへループバック
                "default": "node_7",                 # 成功→Refiner
                "max_iterations_exceeded": "node_7"  # 上限→Refiner
            }
        )
        
        # 7. Refiner(7) → END
        workflow.add_edge("node_7", END)
        
        return workflow.compile()  # LangGraph実行可能状態に
```

**LangGraphグラフ構造（test2.json）**:
```
START
  ↓
Analyzer(1)
  ├→ Retriever(2) → DomainExpert(4) ┐
  └→ Retriever(3) → DomainExpert(5) ┤
                                     ├→ Validator(6) → Router(9) ┐
                                     │                             │
                                     │  ┌──────────────────────────┘
                                     │  │ [condition_1: 信頼度低]
                                     │  └→ Analyzer(1) へループバック
                                     │
                                     │  [default / max_iterations_exceeded]
                                     └→ Refiner(7) → END
```

---

### 【Phase 5】workflow_engine.execute(prompt)

```python
# utils/langgraph_workflow_engine.py

def execute(self, user_input: str) -> Dict[str, Any]:
    """ワークフロー実行"""
    
    # ========== Step 5-1: 初期状態を生成 ==========
    self.log_manager.log(
        "langgraph_workflow_engine",
        LogLevel.MINIMAL,
        f"ワークフロー新規実行開始 - 既存状態をクリア: {user_input[:50]}..."
    )
    
    initial_state = WorkflowState(
        user_input="冷蔵庫のモデルを作って",
        current_data={},        # 完全に空の状態で開始
        execution_log=[],
        node_results={},
        iteration_count=1,
        error=None,
        parallel_results=[],
        node_history=[],
        last_key=""
    )
    
    # ========== Step 5-2: LangGraphワークフローを起動 ==========
    final_state = self.workflow.invoke(initial_state)
    #             ↑ ここでLangGraphが全ノードを実行
    
    # ========== Step 5-3: 結果をフォーマットして返却 ==========
    return self._format_result(final_state)
```

---

### 【Phase 6】LangGraph自動実行シーケンス

```
=== LangGraph内部実行フロー（test2.json完全版）===

1. START → node_1 (analyzer_1)
   └─ AnalyzerExecutor.execute(current_data={}, node_id="1")
       ├─ プロンプト生成: LLM用のプロンプトを構築
       ├─ LLM呼び出し: llm_manager.generate(prompt)
       │   ↓ LLM応答
       │   {
       │     "intent": "冷蔵庫のModelicaモデルを作成する",
       │     "complexity": "中",
       │     "optimized_query": "冷蔵庫の熱・流体・電気統合モデル構築...",
       │     "sources": ["Modelica.Thermal", "Modelica.Fluid", ...],
       │     "confidence": 0.9
       │   }
       │
       └─ 結果返却: {
           "intent_1": "...",
           "complexity_1": "中",
           "optimized_query_1": "...",
           "sources_1": [...],
           "confidence_1": 0.9
       }
   
   ↓ current_data更新: {intent_1: "...", optimized_query_1: "...", ...}


2. node_1 → [node_2, node_3] (並列実行)
   
   ├─ node_2 (retriever_2):
   │   └─ RetrieverExecutor.execute(current_data={...}, node_id="2")
   │       ├─ optimized_query_1を取得
   │       ├─ ベクトル検索: vector_manager.search(
   │       │       query=optimized_query_1,
   │       │       collection="rag_documents_ast",
   │       │       k=50
   │       │   )
   │       ├─ 再ランク: reranker.rank(results, k=6)
   │       └─ 結果返却: {
   │           "search_results_2": [...6件のAST結果...],
   │           "search_query_2": "...",
   │           "confidence_2": -1.95
   │       }
   │
   └─ node_3 (retriever_3):
       └─ RetrieverExecutor.execute(current_data={...}, node_id="3")
           ├─ optimized_query_1を取得
           ├─ ベクトル検索: vector_manager.search(
           │       query=optimized_query_1,
           │       collection="rag_documents_pdf",
           │       k=50
           │   )
           ├─ 再ランク: reranker.rank(results, k=6)
           └─ 結果返却: {
               "search_results_3": [...6件のPDF結果...],
               "search_query_3": "...",
               "confidence_3": -1.90
           }
   
   ※ 並列実行のため、current_dataは merge_dict()で自動マージ
   
   ↓ current_data更新: {
       intent_1: "...",
       optimized_query_1: "...",
       search_results_2: [...],
       search_results_3: [...],
       confidence_2: -1.95,
       confidence_3: -1.90
   }


3. [node_2, node_3] → [node_4, node_5] (並列実行)
   
   ├─ node_4 (domain_expert_4):
   │   └─ DomainExpertExecutor.execute(current_data={...}, node_id="4")
   │       ├─ search_results_2を取得（AST検索結果）
   │       ├─ プロンプト生成: 専門家プロンプトを構築
   │       ├─ LLM呼び出し: llm_manager.generate(prompt)
   │       │   ↓ LLM応答
   │       │   {
   │       │     "answer": "Modelicaライブラリによる冷蔵庫モデル構築...",
   │       │     "facts": [{"statement": "...", "cite_ids": ["chunk:ast:123"]}, ...],
   │       │     "insights": ["洞察1", "洞察2", ...],
   │       │     "recommendations": ["推奨1", "推奨2", ...],
   │       │     "gaps": ["ギャップ1", ...],
   │       │     "citations": ["chunk:ast:123", ...],
   │       │     "confidence": 0.85
   │       │   }
   │       │
   │       └─ 結果返却: {
   │           "analysis_4": "...",
   │           "facts_4": [...],
   │           "insights_4": [...],
   │           "recommendations_4": [...],
   │           "confidence_4": 0.85
   │       }
   │
   └─ node_5 (domain_expert_5):
       └─ DomainExpertExecutor.execute(current_data={...}, node_id="5")
           ├─ search_results_3を取得（PDF検索結果）
           ├─ プロンプト生成: 専門家プロンプトを構築
           ├─ LLM呼び出し: llm_manager.generate(prompt)
           └─ 結果返却: {
               "analysis_5": "...",
               "facts_5": [...],
               "insights_5": [...],
               "recommendations_5": [...],
               "confidence_5": 0.80
           }
   
   ↓ current_data更新: 上記すべてをマージ


4. [node_4, node_5] → node_6 (合流)
   └─ ValidatorExecutor.execute(current_data={...}, node_id="6")
       ├─ 前段階の信頼度を取得:
       │   confidence_2 = -1.95
       │   confidence_3 = -1.90
       │   confidence_4 = 0.85
       │   confidence_5 = 0.80
       │
       ├─ facts, insightsを取得
       ├─ プロンプト生成: 検証プロンプトを構築
       ├─ LLM呼び出し: llm_manager.generate(prompt)
       │   ↓ LLM応答
       │   {
       │     "issues": ["途中で途切れている式がある", ...],
       │     "confidence": 0.65,
       │     "evidence_assessment": "中程度の証拠",
       │     "improvement_suggestions": ["...", ...]
       │   }
       │
       ├─ 信頼度計算:
       │   retriever_avg = (confidence_2 + confidence_3) / 2 = -1.925
       │   expert_avg = (confidence_4 + confidence_5) / 2 = 0.825
       │   llm_confidence = 0.65
       │   rule_score = 0.54
       │   
       │   final_confidence = 
       │       (retriever_avg × 0.15) +
       │       (expert_avg × 0.5) +
       │       (llm_confidence × 0.25) +
       │       (rule_score × 0.1)
       │     = (-1.925 × 0.15) + (0.825 × 0.5) + (0.65 × 0.25) + (0.54 × 0.1)
       │     = -0.289 + 0.413 + 0.163 + 0.054
       │     = 0.341
       │
       └─ 結果返却: {
           "validation_confidence_6": 0.341,  # 閾値0.8未満
           "validation_result_6": {...},
           "validation_issues_6": [...]
       }
   
   ↓ current_data更新


5. node_6 → node_9 (router_9)
   └─ RouterExecutor.execute(current_data={...}, node_id="9")
       ├─ 現在の実行回数を取得: execution_count = 1
       ├─ 条件評価:
       │   [1] validation_confidence_6 < 0.6
       │       → 0.341 < 0.6  →  True
       │   
       │   [2] confidence_2 < 0.8
       │       → -1.95 < 0.8  →  True
       │   
       │   [3] confidence_3 < 0.8
       │       → -1.90 < 0.8  →  True
       │   
       │   custom_expression: "[1] or ( [2] and [3] )"
       │       → True or (True and True)
       │       → True
       │
       ├─ 条件一致: "condition_1"
       ├─ target_node: 1
       │
       └─ 結果返却: {
           "router_decision_9": "condition_1",
           "target_node_9": 1,
           "execution_count": 1
       }


6. node_9 → node_1 (条件分岐でループバック)
   ※ iteration_count = 2 に増加
   
   [Analyzer → Retriever → DomainExpert → Validator → Router を再実行]
   
   ※ 2回目の実行では履歴情報を活用して改善


7. node_9 → node_7 (max_iterations_exceeded)
   ※ max_iterations = 1 なので、2回目は強制的に Refiner へ
   
   └─ RefinerExecutor.execute(current_data={...}, node_id="7")
       ├─ 全DomainExpertの結果を収集:
       │   analysis_4, facts_4, insights_4, recommendations_4
       │   analysis_5, facts_5, insights_5, recommendations_5
       │
       ├─ プロンプト生成: 統合プロンプトを構築
       │   セクション構成:
       │     - 概要 (2%)
       │     - 完全動作Modelicaコード (98%)
       │
       ├─ LLM呼び出し: llm_manager.generate(
       │       prompt=integrated_prompt,
       │       max_tokens=4000
       │   )
       │   ↓ LLM応答（10,000文字以上の詳細回答）
       │   "# 概要\n\n冷蔵庫のModelicaモデルは...\n\n# 完全動作Modelicaコード\n\nmodel Refrigerator\n..."
       │
       └─ 結果返却: {
           "refined_answer": "...",
           "refined_answer_node_7": "..."
       }


8. node_7 → END
   └─ LangGraphワークフロー終了
```

---

### 【Phase 7】結果の返却とUI表示

```python
# utils/langgraph_workflow_engine.py

def _format_result(self, final_state: WorkflowState) -> Dict:
    """最終結果をフォーマット"""
    
    final_answer = self._extract_final_answer(final_state["current_data"])
    # ↓ refined_answer または refined_answer_node_7 を取得
    
    return {
        "refined_answer": final_answer,  # Refinerが生成した最終回答
        "execution_summary": {
            "total_iterations": final_state["iteration_count"],  # 2
            "nodes_executed": list(final_state["node_results"].keys()),
            "processing_status": "completed"
        },
        "current_data": final_state["current_data"]  # 全ての中間結果
    }
```

```python
# tabs/managers/workflow_manager.py

def run(self):
    # ...
    results = workflow.execute(self.prompt)
    
    # メインスレッドに結果を返却
    self.result_signal.emit(results)
```

```python
# tabs/user_tab.py

def handle_workflow_result(self, results):
    """WorkflowManagerから結果を受信（メインスレッド）"""
    
    if "error" in results:
        self.result_widget.display_error(results["error"])
        return
    
    # ResultFormatterで整形してUI表示
    self.result_widget.display_results(results)
    # ↓
    # refined_answer → Markdown表示
    # execution_summary → ログ表示
    
    self.log_widget.add_log("結果表示完了")

def on_workflow_finished(self):
    """ワークフロー完了後の処理（メインスレッド）"""
    self.prompt_widget.set_enabled(True)
    self.log_widget.add_section_header("ワークフロー実行完了")
```

---

## 🎯 完全フロー総括

### データフロー全体像

```
test2.json (ファイル)
  ↓ PromptInputWidget.load()
design_data (辞書)
  ↓ UserTab.execute_workflow()
WorkflowManager.__init__(design_data, prompt, design_name)
  ↓ QThread.start() → 別スレッド
WorkflowManager.run()
  ↓ WorkflowFactory.create_workflow_engine(design_data, ...)
8個のエージェントインスタンス生成
  ↓ LangGraphWorkflowEngine.__init__(agents, ...)
LangGraphグラフ構築 (StateGraph)
  ↓ workflow.compile()
実行可能なLangGraphワークフロー
  ↓ workflow_engine.execute(prompt)
LangGraph自動実行
  ├→ Analyzer → [Retriever×2] → [DomainExpert×2] → Validator → Router
  │                                                                ↓
  │   [条件: 信頼度低] ───────────────────────────────────────→ Analyzer (ループバック)
  │
  └→ [条件: 成功 or 上限] ─→ Refiner → END
  
final_state (WorkflowState)
  ↓ _format_result()
results (辞書)
  ↓ result_signal.emit(results)
UserTab.handle_workflow_result(results) (メインスレッド)
  ↓ ResultDisplayWidget.display_results()
UI表示完了
```

---

## 📌 重要なポイント

### 1. **スレッド分離**
- **メインスレッド**: GUI操作（PySide6）
- **ワーカースレッド**: ワークフロー実行（QThread）
- **通信**: Signalで結果を送信

### 2. **test2.jsonの役割**
- ワークフローの**設計図**（コードではない）
- JSON → Python辞書 → エージェント生成 → LangGraphグラフ
- **実行時に動的に変換される**

### 3. **LangGraphの自動制御**
- 並列実行: `merge_dict()`, `merge_list()`で競合解決
- 条件分岐: Router結果に基づいて自動ルーティング
- ループ制御: `iteration_count`と`max_iterations`で管理

### 4. **状態管理（current_data）**
- すべてのエージェント出力が蓄積される辞書
- 後続エージェントが前段階の結果を参照
- LangGraphが自動的にマージ・更新

### 5. **キー命名規則**
- `{キー名}_{ノードID}`: 例: `intent_1`, `confidence_2`
- KeyRegistryで一元管理
- 重複を防ぎ、並列実行を可能にする

---

## 🔍 test2.json実行時の実際のログ（推定）

```
[16:52:57] 使用設計ファイル: test2.json
[16:52:57] プロンプト: 冷蔵庫のモデルを作って
--- デバッグ: インポート開始 ---
LangGraphワークフロー実行開始
[langgraph_workflow_engine] ワークフロー新規実行開始 - 既存状態をクリア
[langgraph_workflow_engine] 初期状態設定完了 - current_data: {}
[analyzer_1] 分析開始: 冷蔵庫のモデルを作って
[analyzer_1] 分析深度: comprehensive
[analyzer_1] LLM応答サイズ: 344 文字
[analyzer_1] 分析完了: 深度=comprehensive, 信頼度=0.90
[retriever_2] 検索開始: 冷蔵庫の設計モデルを作成してください...
[retriever_3] 検索開始: 冷蔵庫の設計モデルを作成してください...
[retriever_2] Dense検索モデル初期化中
[retriever_3] Dense検索モデル初期化中
[retriever_2] 再ランクモデル初期化中: BAAI/bge-reranker-large
[retriever_3] 再ランクモデル初期化中: BAAI/bge-reranker-large
[retriever_2] rag_documents_ast: 6件取得
[retriever_3] rag_documents_pdf: 6件取得
[retriever_2] 再ランク検索完了: 6件, 信頼度=-1.95
[retriever_3] 再ランク検索完了: 6件, 信頼度=-1.90
[domain_expert_4] 専門分析開始: Modelicaライブラリ
[domain_expert_5] 専門分析開始: ModelicaStandardLibrary
[domain_expert_4] 検索結果数: 6
[domain_expert_5] 検索結果数: 6
[domain_expert_4] LLM応答サイズ: 3134 文字
[domain_expert_5] LLM応答サイズ: 2924 文字
[domain_expert_4] 専門分析完了: 信頼度=0.85
[domain_expert_5] 専門分析完了: 信頼度=0.80
[validator_6] 段階間連携検証開始
[validator_6] 前段階信頼度: Retriever=-1.925, Expert=0.825
[validator_6] 信頼度計算詳細:
[validator_6]   Retriever影響: -1.925 × 0.15 = -0.289
[validator_6]   Expert影響: 0.825 × 0.50 = 0.413
[validator_6]   LLM検証: 0.650 × 0.25 = 0.163
[validator_6]   ルールスコア: 0.540 × 0.10 = 0.054
[validator_6]   最終信頼度: 0.341 (閾値: 0.80)
[validator_6] ✗ 検証不合格: 信頼度 0.341 < 閾値 0.80 (不足: 0.459)
[validator_6]   不合格要因: Retriever影響低 (-0.289)
[validator_6]   改善提案: 検索品質向上が必要
[router_9] Router分岐判定開始
[router_9] 条件評価: [1]=True or ([2]=True and [3]=True) → True
[router_9] ルート決定: condition_1 → Node 1 (ループバック)
[analyzer_1] 分析開始: 冷蔵庫のモデルを作って (2回目)
[analyzer_1] 利用可能累積情報: 検索結果: 2件, 専門分析: 2件
... (2回目の実行)
[router_9] max_iterations超過: 1/1 → max_iterations_exceeded → Node 7
[refiner_7] 統合回答生成開始
[refiner_7] 収集した専門家数: 2
[refiner_7] 生成プロンプト長: 3982 文字
[refiner_7] LLM応答サイズ: 10250 文字
[refiner_7] 統合生成完了
[langgraph_workflow_engine] ワークフロー実行完了
[16:54:05] 結果表示完了
=== ワークフロー実行完了 ===
```

---

## 🚀 次のステップ: Phase別実装

これで**完全なフロー**が理解できました！

次は、以下のPhase別実装を進めましょう：

### Phase 1: 基盤整備（35分）
1. `utils/exceptions.py` 作成
2. `NodeThresholdManager` リファクタリング
   - 旧形式検出→即エラー
   - デフォルト値自動適用

### Phase 2: エージェント統一化（10分）
1. `BaseAgentExecutor._get_threshold()` フォールバック削除

### Phase 3: デフォルト値追加（10分）
1. `domain_expert/config.py` に不足キー追加
   - `min_facts_count`: 3
   - `min_insights_count`: 2

### Phase 4: バグ修正（5分）
1. `RefinerExecutor` LLMManager呼び出し修正
   - `generate_response()` → `generate()`

### Phase 5: 簡略化（15分）
1. `ConfigTransformer._extract_node_thresholds()` 簡略化

---

## 実装開始の選択肢

以下のどれかを選択してください：

**A. Phase 1から順番に実装**（推奨）
- 1つずつ確実に進める
- 各Phaseで動作確認

**B. 全Phaseのコードを一度に生成**
- 5つのファイル修正を一括提供
- まとめて適用後、動作確認

**C. 最優先のみ実装（Phase 3, 4）**
- test2.jsonのエラーを即座に解消
- 他のPhaseは後回し

どれにしますか？