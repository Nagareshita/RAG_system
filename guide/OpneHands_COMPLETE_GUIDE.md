# OpenHands Azure CLI認証 - 完全ガイド（初心者向け）

このガイドに従えば、初めてでもAzure CLI認証でOpenHandsを使えます。

---

## 📋 準備

### 必要なもの
- Azure OpenAIのリソース（作成済み）
- リソース名（例: `mycompany-openai`）
- デプロイ名（例: `gpt-4o`）

### Azure Portalで確認
1. https://portal.azure.com を開く
2. Azure OpenAIリソースを開く
3. 「キーとエンドポイント」→ エンドポイントをメモ
   - 例: `https://mycompany-openai.openai.azure.com/`
4. 「モデルのデプロイ」→ デプロイ名をメモ
   - 例: `gpt-4o`

---

## 🚀 セットアップ（5ステップ）

### ステップ1: インストール
```bash
pip install openhands-ai azure-identity
```

### ステップ2: Azure CLIログイン
```bash
az login
```
ブラウザが開くのでログイン

### ステップ3: コード修正（3ファイル）

#### ファイル1: `llm.py`

場所を確認：
```bash
find ~/miniforge3/envs -name "llm.py" | grep openhands/llm/llm.py | head -1
```

出力例：
```
/home/nagareshita/miniforge3/envs/openhands/lib/python3.12/site-packages/openhands/llm/llm.py
```

このファイルを編集：
```bash
nano /home/nagareshita/miniforge3/envs/openhands/lib/python3.12/site-packages/openhands/llm/llm.py
```

**ファイルの先頭（7行目あたり、`import httpx`の後）に以下を追加：**

```python
# Azure CLI authentication support
_azure_token_provider = None
try:
    if os.environ.get('USE_AZURE_CLI_AUTH') == 'true':
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider
        _azure_credential = DefaultAzureCredential()
        _azure_token_provider = get_bearer_token_provider(
            _azure_credential,
            "https://cognitiveservices.azure.com/.default"
        )
        print("✅ Azure CLI authentication loaded!")
    else:
        _azure_token_provider = None
except Exception as e:
    print(f"⚠️ Azure auth failed: {e}")
    _azure_token_provider = None
```

**`self._completion = partial(` の部分（200行目あたり）を探して、以下に置き換え：**

置き換え前：
```python
        self._completion = partial(
            litellm_completion,
            model=self.config.model,
            api_key=self.config.api_key.get_secret_value()
            if self.config.api_key
            else None,
            base_url=self.config.base_url,
            api_version=self.config.api_version,
            custom_llm_provider=self.config.custom_llm_provider,
            timeout=self.config.timeout,
            drop_params=self.config.drop_params,
            seed=self.config.seed,
            **kwargs,
        )
```

置き換え後：
```python
        # Determine if we should use Azure CLI authentication
        use_azure_cli_auth = (
            self.config.model.startswith('azure/') and 
            _azure_token_provider is not None
        )
        
        if use_azure_cli_auth:
            # Use Azure CLI authentication instead of API key
            self._completion = partial(
                litellm_completion,
                model=self.config.model,
                azure_ad_token_provider=_azure_token_provider,
                base_url=self.config.base_url,
                api_version=self.config.api_version,
                custom_llm_provider=self.config.custom_llm_provider,
                timeout=self.config.timeout,
                drop_params=self.config.drop_params,
                seed=self.config.seed,
                **kwargs,
            )
            logger.debug(f'Using Azure CLI authentication for model: {self.config.model}')
        else:
            # Use regular API key authentication
            self._completion = partial(
                litellm_completion,
                model=self.config.model,
                api_key=self.config.api_key.get_secret_value()
                if self.config.api_key
                else None,
                base_url=self.config.base_url,
                api_version=self.config.api_version,
                custom_llm_provider=self.config.custom_llm_provider,
                timeout=self.config.timeout,
                drop_params=self.config.drop_params,
                seed=self.config.seed,
                **kwargs,
            )
```

保存して終了（nano: `Ctrl+O` → `Enter` → `Ctrl+X`）

---

#### ファイル2: `async_llm.py`

場所を確認：
```bash
find ~/miniforge3/envs -name "async_llm.py" | grep openhands/llm/async_llm.py | head -1
```

このファイルを編集：
```bash
nano /home/nagareshita/miniforge3/envs/openhands/lib/python3.12/site-packages/openhands/llm/async_llm.py
```

**importセクション（11行目あたり）を修正：**

置き換え前：
```python
from openhands.llm.llm import (
    LLM,
    LLM_RETRY_EXCEPTIONS,
)
```

置き換え後：
```python
from openhands.llm.llm import (
    LLM,
    LLM_RETRY_EXCEPTIONS,
    _azure_token_provider,
)
```

**`def __init__` の中の `self._async_completion = partial(` の部分（23行目あたり）を探して、以下に置き換え：**

置き換え前：
```python
        self._async_completion = partial(
            self._call_acompletion,
            model=self.config.model,
            api_key=self.config.api_key.get_secret_value()
            if self.config.api_key
            else None,
            base_url=self.config.base_url,
            api_version=self.config.api_version,
            custom_llm_provider=self.config.custom_llm_provider,
            max_tokens=self.config.max_output_tokens,
            timeout=self.config.timeout,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            drop_params=self.config.drop_params,
            seed=self.config.seed,
        )
```

置き換え後：
```python
        # Determine if we should use Azure CLI authentication
        use_azure_cli_auth = (
            self.config.model.startswith('azure/') and 
            _azure_token_provider is not None
        )

        if use_azure_cli_auth:
            self._async_completion = partial(
                self._call_acompletion,
                model=self.config.model,
                azure_ad_token_provider=_azure_token_provider,
                base_url=self.config.base_url,
                api_version=self.config.api_version,
                custom_llm_provider=self.config.custom_llm_provider,
                max_tokens=self.config.max_output_tokens,
                timeout=self.config.timeout,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                drop_params=self.config.drop_params,
                seed=self.config.seed,
            )
            logger.debug(f'Using Azure CLI authentication for async model: {self.config.model}')
        else:
            self._async_completion = partial(
                self._call_acompletion,
                model=self.config.model,
                api_key=self.config.api_key.get_secret_value()
                if self.config.api_key
                else None,
                base_url=self.config.base_url,
                api_version=self.config.api_version,
                custom_llm_provider=self.config.custom_llm_provider,
                max_tokens=self.config.max_output_tokens,
                timeout=self.config.timeout,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                drop_params=self.config.drop_params,
                seed=self.config.seed,
            )
```

保存して終了

---

#### ファイル3: `streaming_llm.py`

場所を確認：
```bash
find ~/miniforge3/envs -name "streaming_llm.py" | grep openhands/llm/streaming_llm.py | head -1
```

このファイルを編集：
```bash
nano /home/nagareshita/miniforge3/envs/openhands/lib/python3.12/site-packages/openhands/llm/streaming_llm.py
```

**importセクション（7行目あたり）を修正：**

置き換え前：
```python
from openhands.llm.async_llm import LLM_RETRY_EXCEPTIONS, AsyncLLM
from openhands.llm.model_features import get_features
```

置き換え後：
```python
from openhands.llm.async_llm import LLM_RETRY_EXCEPTIONS, AsyncLLM
from openhands.llm.llm import _azure_token_provider
from openhands.llm.model_features import get_features
```

**`def __init__` の中の `self._async_streaming_completion = partial(` の部分（17行目あたり）を探して、以下に置き換え：**

置き換え前：
```python
        self._async_streaming_completion = partial(
            self._call_acompletion,
            model=self.config.model,
            api_key=self.config.api_key.get_secret_value()
            if self.config.api_key
            else None,
            base_url=self.config.base_url,
            api_version=self.config.api_version,
            custom_llm_provider=self.config.custom_llm_provider,
            max_tokens=self.config.max_output_tokens,
            timeout=self.config.timeout,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            drop_params=self.config.drop_params,
            stream=True,
        )
```

置き換え後：
```python
        # Determine if we should use Azure CLI authentication
        use_azure_cli_auth = (
            self.config.model.startswith('azure/') and 
            _azure_token_provider is not None
        )

        if use_azure_cli_auth:
            self._async_streaming_completion = partial(
                self._call_acompletion,
                model=self.config.model,
                azure_ad_token_provider=_azure_token_provider,
                base_url=self.config.base_url,
                api_version=self.config.api_version,
                custom_llm_provider=self.config.custom_llm_provider,
                max_tokens=self.config.max_output_tokens,
                timeout=self.config.timeout,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                drop_params=self.config.drop_params,
                stream=True,
            )
            logger.debug(f'Using Azure CLI authentication for streaming model: {self.config.model}')
        else:
            self._async_streaming_completion = partial(
                self._call_acompletion,
                model=self.config.model,
                api_key=self.config.api_key.get_secret_value()
                if self.config.api_key
                else None,
                base_url=self.config.base_url,
                api_version=self.config.api_version,
                custom_llm_provider=self.config.custom_llm_provider,
                max_tokens=self.config.max_output_tokens,
                timeout=self.config.timeout,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                drop_params=self.config.drop_params,
                stream=True,
            )
```

保存して終了

---

### ステップ4: 環境変数設定
```bash
echo 'export USE_AZURE_CLI_AUTH=true' >> ~/.bashrc
source ~/.bashrc
```

確認：
```bash
echo $USE_AZURE_CLI_AUTH
# 出力: true
```

---

### ステップ5: 初回起動
```bash
openhands
```

対話式セットアップで入力：
```
Provider: azure
Model: gpt-4o (または自分のデプロイ名)
API Key: dummy
Search API: No
Shell aliases: No
Trust folder: Yes
```

---

## ✅ 完了

2回目以降は `openhands` だけで起動できます。

---

## ⚠️ トラブルシューティング

### エラー: Azure auth failed
```bash
az login
```

### エラー: ファイルが見つからない
Pythonバージョンが違う可能性があります：
```bash
find ~/miniforge3/envs -name "llm.py" | grep openhands/llm/llm.py
```
表示されたパスを使用してください。

### エラー: 環境変数が設定されていない
```bash
export USE_AZURE_CLI_AUTH=true
```

---

## 📋 チェックリスト

- [ ] `pip install openhands-ai azure-identity`
- [ ] `az login`
- [ ] `llm.py` を修正
- [ ] `async_llm.py` を修正
- [ ] `streaming_llm.py` を修正
- [ ] 環境変数設定 `USE_AZURE_CLI_AUTH=true`
- [ ] `openhands` 起動
- [ ] 対話式セットアップで `dummy` と入力

すべてチェックできたら完了です！
