from typing import Any, Optional

from llama_index.core.llms import (
    CustomLLM,
    CompletionResponse,
    CompletionResponseGen,
    LLMMetadata,
)

# 注意: 追加プロバイダ（OpenAI など）の依存は必要時にのみ import し、
# 最小依存での利用を可能にする。


class LocalHFLLM(CustomLLM):
    """ローカルの HuggingFace CausalLM を LlamaIndex から利用するための薄い実装。"""

    context_window: int = 8192
    num_output: int = 2048
    model_name: str = "local-hf"

    def __init__(self, pretrained_model_path: str, max_new_tokens: int = 800, temperature: float = 0.3):
        super().__init__()
        from transformers import AutoTokenizer, AutoModelForCausalLM  # 遅延 import
        import torch

        self._tokenizer = AutoTokenizer.from_pretrained(pretrained_model_path, trust_remote_code=True)
        self._model = AutoModelForCausalLM.from_pretrained(
            pretrained_model_path,
            trust_remote_code=True,
            device_map="auto",
            torch_dtype=torch.float16,
        )
        self._max_new_tokens = max_new_tokens
        self._temperature = temperature
        self.model_name = pretrained_model_path

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=self.context_window,
            num_output=self.num_output,
            model_name=self.model_name,
        )

    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        inputs = self._tokenizer(prompt, return_tensors="pt")
        input_ids = inputs["input_ids"].to("cuda")
        attention_mask = inputs.get("attention_mask")
        if attention_mask is not None:
            attention_mask = attention_mask.to("cuda")

        max_length = int(input_ids.shape[1]) + int(self._max_new_tokens)
        outputs = self._model.generate(
            input_ids,
            max_length=max_length,
            temperature=float(self._temperature),
            do_sample=True,
            top_k=10,
            attention_mask=attention_mask,
            pad_token_id=self._tokenizer.eos_token_id,
        )
        text = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
        return CompletionResponse(text=text)

    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        # ストリーミング未対応の簡易フォールバック
        resp = self.complete(prompt, **kwargs)
        yield CompletionResponse(text=resp.text, delta=resp.text)


def create_llm(provider: str,
               model: Optional[str] = None,
               model_path: Optional[str] = None,
               temperature: float = 0.3,
               max_new_tokens: int = 800,
               openai_api_base: Optional[str] = None,
               openai_api_key: Optional[str] = None,
               openai_api_version: Optional[str] = None,
               openai_deployment: Optional[str] = None,
               apim_subscription_key_header: Optional[str] = None,
               apim_subscription_key: Optional[str] = None) -> CustomLLM:
    """LlamaIndex 互換の LLM インスタンスを作成するファクトリ。

    provider: local_hf | openai | azure_openai
    - local_hf: transformers ベースのローカル推論（GPU/CPU 資源が必要）
    - openai: LlamaIndex の OpenAI 連携（任意依存パッケージが必要）
    - azure_openai: 上記の Azure 版（API Base/Version/Deployment 等を指定）
    """

    if provider == "local_hf":
        if not model_path:
            raise ValueError("local_hf requires model_path to be set")
        return LocalHFLLM(model_path, max_new_tokens=max_new_tokens, temperature=temperature)

    if provider in ("openai", "azure_openai"):
        # LlamaIndex の OpenAI 連携を利用（未インストール時は明示エラー）。
        try:
            # Note: in LlamaIndex 0.11+, OpenAI integration lives in a separate package.
            from llama_index.llms.openai import OpenAI as LlamaIndexOpenAI  # type: ignore
        except Exception as e:
            raise ImportError(
                "OpenAI/Azure OpenAI を選択しましたが、llama-index-llms-openai が未インストールです。\n"
                "インストール例: pip install llama-index-llms-openai"
            ) from e

        kwargs = {}
        if openai_api_base:
            kwargs["api_base"] = openai_api_base
        if openai_api_key:
            kwargs["api_key"] = openai_api_key
        if openai_api_version:
            kwargs["api_version"] = openai_api_version
        if provider == "azure_openai":
            # In Azure OpenAI, model is often the deployment name
            if openai_deployment:
                kwargs["model"] = openai_deployment
            # Pass-through APIM subscription key via headers if provided
            if apim_subscription_key_header and apim_subscription_key:
                kwargs["default_headers"] = {apim_subscription_key_header: apim_subscription_key}
        else:
            if model:
                kwargs["model"] = model

        # 温度やトークン上限は呼び出し側で渡すのが基本だが、利用可能な範囲で既定を合わせる。
        return LlamaIndexOpenAI(**kwargs)

    raise ValueError(f"未対応の LLM プロバイダです: {provider}")
