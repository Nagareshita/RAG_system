"""
SAIL-VL2-2B モデル管理モジュール（改善版）
RAGシステムとの統合を考慮し、柔軟なパラメータ設定に対応
"""

import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModel, AutoProcessor
from huggingface_hub import snapshot_download
import json
import shutil
from typing import Optional, Dict, Any
from PIL import Image


class ModelManager:
    """SAIL-VL2モデルの管理クラス（改善版）"""
    
    # デフォルトパラメータ（Qwen3-1.7B推奨値に準拠）
    DEFAULT_GENERATION_CONFIG = {
        # Sampling / search
        "do_sample": True,
        "temperature": 0.7,
        "top_p": 0.8,
        "top_k": 20,
        "num_beams": 1,
        "length_penalty": 1.0,
        "no_repeat_ngram_size": 0,
        "repetition_penalty": 1.0,
        "diversity_penalty": 0.0,
        "early_stopping": False,

        # Length control
        "min_new_tokens": 1,
        "max_new_tokens": 512,
    }
    
    # タスク別プリセット
    # 注意: use_cacheはmodeling_sailvl.pyで強制的にTrueが設定されるため、
    #       ここでは設定しない（二重設定エラー回避）
    TASK_PRESETS = {
        # 既存互換（シンプル）
        "accurate": {  # 正確性重視/OCR寄り
            "do_sample": False,
            "num_beams": 4,
            "length_penalty": 1.05,
            "min_new_tokens": 64,
            "max_new_tokens": 1024,
            "no_repeat_ngram_size": 3,
            "repetition_penalty": 1.08,
            "temperature": 0.1,
            "top_p": 0.5,
            "top_k": 10,
        },
        "balanced": {  # 画像説明・バランス型
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 20,
            "min_new_tokens": 32,
            "max_new_tokens": 512,
            "repetition_penalty": 1.0,
        },

        # 提案プリセット（リクエスト準拠）
        "ocr": {
            "do_sample": False, "num_beams": 5,
            "length_penalty": 1.1,
            "min_new_tokens": 120, "max_new_tokens": 2048,
            "no_repeat_ngram_size": 4, "repetition_penalty": 1.05
        },
        "qa": {
            "do_sample": False, "num_beams": 4,
            "min_new_tokens": 64, "max_new_tokens": 1024,
            "no_repeat_ngram_size": 4, "repetition_penalty": 1.05
        },
        "code": {
            "do_sample": False, "num_beams": 4,
            "length_penalty": 0.98, "min_new_tokens": 128, "max_new_tokens": 2048,
            "no_repeat_ngram_size": 6, "repetition_penalty": 1.08
        },
        "creative": {
            "do_sample": True, "temperature": 0.9, "top_p": 0.92,
            "min_new_tokens": 80, "max_new_tokens": 1024,
            "repetition_penalty": 1.02
        },
        "summary": {
            "do_sample": False, "num_beams": 3,
            "length_penalty": 0.95, "min_new_tokens": 80, "max_new_tokens": 800,
            "no_repeat_ngram_size": 4
        },
        "json": {
            "do_sample": False, "num_beams": 6,
            "min_new_tokens": 80, "max_new_tokens": 1600,
            "no_repeat_ngram_size": 4, "repetition_penalty": 1.05
        },
    }
    
    def __init__(self, model_path: str = "./SAIL-VL2-2B"):
        self.model_path = Path(model_path)
        self.model = None
        self.tokenizer = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    def setup_model(self, progress_callback=None) -> bool:
        """モデルのセットアップ（ダウンロード、設定修正、読み込み）"""
        try:
            # ステップ1: ダウンロード
            if progress_callback:
                progress_callback("モデルの確認中...")
            self._download_model_if_needed()
            
            # ステップ2: 設定修正
            if progress_callback:
                progress_callback("設定ファイルの修正中...")
            self._fix_config()
            self._patch_modeling_qwen3()
            self._clear_cache()
            
            # ステップ3: モデル読み込み
            if progress_callback:
                progress_callback("トークナイザーを読み込み中...")
            self._load_tokenizer()
            
            if progress_callback:
                progress_callback("プロセッサーを読み込み中...")
            self._load_processor()
            
            if progress_callback:
                progress_callback("モデルを読み込み中（数分かかります）...")
            self._load_model()
            
            if progress_callback:
                progress_callback("完了")
            
            return True
            
        except Exception as e:
            print(f"モデルセットアップエラー: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _download_model_if_needed(self):
        """必要に応じてモデルをダウンロード"""
        required_files = ["config.json", "model.safetensors.index.json", "tokenizer.json"]
        
        is_downloaded = self.model_path.exists() and all(
            (self.model_path / f).exists() for f in required_files
        )
        
        if not is_downloaded:
            print("モデルをダウンロードしています...")
            snapshot_download(
                repo_id="BytedanceDouyinContent/SAIL-VL2-2B",
                repo_type="model",
                local_dir=str(self.model_path),
                local_dir_use_symlinks=False
            )
    
    def _fix_config(self):
        """config.jsonのFlash Attention設定を修正"""
        config_path = self.model_path / "config.json"
        
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        modified = False
        
        if config.get("_attn_implementation") == "flash_attention_2":
            config["_attn_implementation"] = "sdpa"
            modified = True
        
        if "llm_config" in config and config["llm_config"].get("attn_implementation") == "flash_attention_2":
            config["llm_config"]["attn_implementation"] = "sdpa"
            modified = True
        
        if modified:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
    
    def _patch_modeling_qwen3(self):
        """modeling_qwen3.pyをNVIDIA GPU対応に修正"""
        modeling_file = self.model_path / "modeling_qwen3.py"
        
        if not modeling_file.exists():
            return
        
        with open(modeling_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        if "torch_npu.npu_fusion_attention(" in content and "hasattr(torch, 'npu')" not in content:
            old_code = """    head_num = query.shape[1]
    attn_output = torch_npu.npu_fusion_attention(
                    query, key, value, head_num, input_layout="BNSD", 
                    pse=None,
                    atten_mask=atten_mask_npu,
                    scale=1.0 / math.sqrt(query.shape[-1]),
                    pre_tockens=2147483647,
                    next_tockens=2147483647,
                    keep_prob=1
                )[0]

    attn_output = attn_output.transpose(1, 2).contiguous()"""
            
            new_code = """    head_num = query.shape[1]
    
    # NVIDIA GPU の場合は標準 SDPA を使用
    if not hasattr(torch, 'npu') or not torch.npu.is_available():
        attn_output = torch.nn.functional.scaled_dot_product_attention(
            query,
            key,
            value,
            attn_mask=causal_mask,
            dropout_p=dropout,
            scale=scaling if scaling else 1.0 / math.sqrt(query.shape[-1]),
            is_causal=is_causal,
        )
    else:
        # Huawei NPU の場合
        attn_output = torch_npu.npu_fusion_attention(
                        query, key, value, head_num, input_layout="BNSD", 
                        pse=None,
                        atten_mask=atten_mask_npu,
                        scale=1.0 / math.sqrt(query.shape[-1]),
                        pre_tockens=2147483647,
                        next_tockens=2147483647,
                        keep_prob=1
                    )[0]

    attn_output = attn_output.transpose(1, 2).contiguous()"""
            
            content = content.replace(old_code, new_code)
            
            with open(modeling_file, "w", encoding="utf-8") as f:
                f.write(content)
    
    def _clear_cache(self):
        """transformersキャッシュをクリア"""
        cache_dir = Path.home() / ".cache/huggingface/modules/transformers_modules/SAIL-VL2-2B"
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
    
    def _load_tokenizer(self):
        """トークナイザーを読み込み"""
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(self.model_path),
            local_files_only=True,
            trust_remote_code=True,
        )
    
    def _load_processor(self):
        """プロセッサーを読み込み"""
        self.processor = AutoProcessor.from_pretrained(
            str(self.model_path),
            local_files_only=True,
            trust_remote_code=True,
        )
    
    def _load_model(self):
        """モデルを読み込み"""
        self.model = AutoModel.from_pretrained(
            str(self.model_path),
            local_files_only=True,
            trust_remote_code=True,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            low_cpu_mem_usage=True,
        )
        self.model.eval()
    
    def generate_response(
        self,
        text: str,
        image: Optional[Image.Image] = None,
        max_new_tokens: Optional[int] = None,
        min_new_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        do_sample: Optional[bool] = None,
        num_beams: Optional[int] = None,
        length_penalty: Optional[float] = None,
        no_repeat_ngram_size: Optional[int] = None,
        diversity_penalty: Optional[float] = None,
        early_stopping: Optional[bool] = None,
        repetition_penalty: Optional[float] = None,
        preset: Optional[str] = None,
    ) -> str:
        """
        テキスト・画像から応答を生成（メモリ最適化版）
        
        Args:
            text: 入力テキスト
            image: 入力画像（オプション）
            max_new_tokens: 生成する最大トークン数
            min_new_tokens: 生成する最小トークン数
            temperature: サンプリング温度（0.0-1.0）
            top_p: 核サンプリング確率
            top_k: 上位K個のトークンを考慮
            do_sample: サンプリングの有効/無効
            num_beams: ビーム探索のビーム数
            length_penalty: シーケンス長ペナルティ
            no_repeat_ngram_size: n-gramの繰り返し抑制サイズ
            diversity_penalty: 多様性ペナルティ（ビーム分岐向け）
            early_stopping: 早期停止フラグ
            repetition_penalty: 繰り返しペナルティ
            preset: タスク別プリセット ("accurate", "balanced", "creative")
        
        Returns:
            生成されたテキスト
        """
        if self.model is None or self.processor is None:
            raise RuntimeError("モデルが初期化されていません")
        
        # 変数を事前定義（finally句で確実にクリーンアップするため）
        inputs = None
        outputs = None
        response = None
        
        try:
            # パラメータ設定（優先順位: デフォルト < preset < 個別指定）
            gen_config = self.DEFAULT_GENERATION_CONFIG.copy()
            
            # プリセット適用
            if preset and preset in self.TASK_PRESETS:
                gen_config.update(self.TASK_PRESETS[preset])
            
            # 個別指定パラメータで上書き
            if max_new_tokens is not None:
                gen_config["max_new_tokens"] = max_new_tokens
            if min_new_tokens is not None:
                gen_config["min_new_tokens"] = min_new_tokens
            if temperature is not None:
                gen_config["temperature"] = temperature
            if top_p is not None:
                gen_config["top_p"] = top_p
            if top_k is not None:
                gen_config["top_k"] = top_k
            if do_sample is not None:
                gen_config["do_sample"] = do_sample
            if num_beams is not None:
                gen_config["num_beams"] = num_beams
            if length_penalty is not None:
                gen_config["length_penalty"] = length_penalty
            if no_repeat_ngram_size is not None:
                gen_config["no_repeat_ngram_size"] = no_repeat_ngram_size
            if diversity_penalty is not None:
                gen_config["diversity_penalty"] = diversity_penalty
            if early_stopping is not None:
                gen_config["early_stopping"] = early_stopping
            if repetition_penalty is not None:
                gen_config["repetition_penalty"] = repetition_penalty
            
            # 🔥 重要: use_cacheはmodeling_sailvl.pyで強制的にTrueが設定されるため、
            #         ここでは設定しない（二重設定による"got multiple values"エラー回避）
            # 参考: vlm/SAIL-VL2-2B/modeling_sailvl.py:345 で use_cache=True がハードコード
            
            # メッセージ構築
            content = []
            if image is not None:
                content.append({"type": "image"})
            content.append({"type": "text", "text": text})
            
            messages = [{"role": "user", "content": content}]
            
            # 入力を準備
            text_prompt = self.processor.apply_chat_template(
                messages, add_generation_prompt=True, tokenize=False
            )
            inputs = self.processor(images=image, text=text_prompt, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items() if isinstance(v, torch.Tensor)}
            
            # 推論
            with torch.no_grad():
                outputs = self.model.generate(**inputs, **gen_config)
            
            # デコード
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # プロンプト部分を除去
            if "<|im_start|>assistant" in response:
                response = response.split("<|im_start|>assistant")[-1].strip()
            
            return response
        
        finally:
            # 🔥 重要: メモリクリーンアップを確実に実行
            self._cleanup_after_generation(inputs, outputs)
    
    def _cleanup_after_generation(self, inputs: Optional[Dict] = None, outputs: Optional[torch.Tensor] = None):
        """
        生成後のメモリクリーンアップ（OSダウン防止の最重要処理）
        """
        import gc
        
        # 入力テンソルの削除
        if inputs is not None:
            for key in list(inputs.keys()):
                if isinstance(inputs[key], torch.Tensor):
                    del inputs[key]
            del inputs
        
        # 出力テンソルの削除
        if outputs is not None:
            del outputs
        
        # モデルのキャッシュクリア（past_key_valuesなどの累積防止）
        if self.model is not None:
            # KVキャッシュが存在する場合はクリア
            if hasattr(self.model, 'past_key_values'):
                self.model.past_key_values = None
        
        # Python GC実行
        gc.collect()
        
        # CUDA メモリキャッシュクリア（重要！）
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()  # GPU処理の完全同期
    
    def cleanup_model(self):
        """
        モデルの完全クリーンアップ（ワークフロー終了時用）
        """
        import gc
        
        print("VLMモデルのクリーンアップ開始...")
        
        # モデルをCPUに移動してからメモリ解放
        if self.model is not None:
            try:
                self.model.cpu()
            except:
                pass
            del self.model
            self.model = None
        
        # トークナイザー削除
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
        
        # プロセッサー削除
        if self.processor is not None:
            del self.processor
            self.processor = None
        
        # Python GC強制実行
        gc.collect()
        
        # CUDA完全クリーンアップ
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            torch.cuda.ipc_collect()  # プロセス間共有メモリもクリア
        
        print("VLMモデルのクリーンアップ完了")
    
    def get_device_info(self) -> Dict[str, Any]:
        """デバイス情報を取得"""
        info = {
            "device": self.device,
            "cuda_available": torch.cuda.is_available(),
        }
        
        if torch.cuda.is_available():
            info["gpu_name"] = torch.cuda.get_device_name(0)
            info["gpu_memory_total"] = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            info["gpu_memory_allocated"] = torch.cuda.memory_allocated() / (1024**3)
        
        return info
    
    def get_preset_names(self):
        """利用可能なプリセット名のリストを取得"""
        return list(self.TASK_PRESETS.keys())
    
    def get_preset_config(self, preset_name: str) -> Optional[Dict]:
        """指定プリセットの設定を取得"""
        return self.TASK_PRESETS.get(preset_name)
