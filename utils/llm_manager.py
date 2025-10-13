# utils/llm_manager.py
from typing import Dict, Any, Optional
import json

class LLMManager:
    def __init__(self):
        self.providers = {}
        
    def register_provider(self, name: str, config: Dict[str, Any]):
        """LLMプロバイダーを登録"""
        self.providers[name] = config
        
    def get_response(self, prompt: str, provider_config: Dict[str, Any] = None, 
                    max_tokens: Optional[int] = None) -> str:
        """LLMから応答を取得（完全動的版）"""
        
        if provider_config is None:
            from utils.config_manager import ConfigManager
            config_manager = ConfigManager()
            provider_config = config_manager.load_llm_config()
        
        if not provider_config:
            return "エラー: LLMプロバイダーの設定が見つかりません。"
        
        # max_tokensが明示的に渡されない場合は制限なし（プロバイダー側のデフォルトに委ねる）
        provider = provider_config.get('provider', '')
        
        try:
            if provider == "ChatGPT API":
                return self._get_openai_response(prompt, provider_config, max_tokens)
            elif provider == "Claude API":
                return self._get_claude_response(prompt, provider_config, max_tokens)
            elif provider == "Azure OpenAI API":
                return self._get_azure_api_response(prompt, provider_config, max_tokens)
            elif provider == "Azure OpenAI CLI":
                return self._get_azure_cli_response(prompt, provider_config, max_tokens)
            elif provider == "AWS Bedrock":
                return self._get_bedrock_response(prompt, provider_config, max_tokens)
            else:
                return f"エラー: 未対応のプロバイダー '{provider}'"
        except Exception as e:
            return f"エラー: LLM呼び出し中にエラーが発生しました: {str(e)}"

    def _get_openai_response(self, prompt: str, config: Dict[str, Any], max_tokens: Optional[int] = None) -> str:
        """OpenAI API応答取得（制限なし版）"""
        try:
            import openai
        except ImportError:
            return "エラー: openai ライブラリがインストールされていません"
        
        api_key = config.get('api_key', '')
        base_url = config.get('base_url', '') or None
        model = config.get('model', 'gpt-3.5-turbo')
        
        if not api_key:
            return "エラー: OpenAI API Keyが設定されていません"
        
        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        
        create_params = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        
        if max_tokens is not None:
            create_params["max_tokens"] = max_tokens
        
        response = client.chat.completions.create(**create_params)
        return response.choices[0].message.content.strip()

    def _get_claude_response(self, prompt: str, config: Dict[str, Any], max_tokens: Optional[int] = None) -> str:
        """Claude API応答取得（制限なし版）"""
        try:
            import anthropic
        except ImportError:
            return "エラー: anthropic ライブラリがインストールされていません"
        
        api_key = config.get('api_key', '')
        model = config.get('model', 'claude-3-haiku-20240307')
        
        if not api_key:
            return "エラー: Claude API Keyが設定されていません"
        
        client = anthropic.Anthropic(api_key=api_key)
        
        create_params = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if max_tokens is not None:
            create_params["max_tokens"] = max_tokens
        
        response = client.messages.create(**create_params)
        return response.content[0].text.strip()

    def _get_azure_api_response(self, prompt: str, config: Dict[str, Any], max_tokens: Optional[int] = None) -> str:
        """Azure OpenAI API応答取得（制限なし版）"""
        try:
            import openai
        except ImportError:
            return "エラー: openai ライブラリがインストールされていません"
        
        api_key = config.get('api_key', '')
        endpoint = config.get('endpoint', '')
        api_version = config.get('api_version', '2024-02-15-preview')
        deployment_name = config.get('deployment_name', '')
        
        if not all([api_key, endpoint, deployment_name]):
            return "エラー: Azure OpenAI の設定が不完全です"
        
        client = openai.AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint
        )
        
        create_params = {
            "model": deployment_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        
        if max_tokens is not None:
            create_params["max_tokens"] = max_tokens
        
        response = client.chat.completions.create(**create_params)
        return response.choices[0].message.content.strip()

    def _get_azure_cli_response(self, prompt: str, config: Dict[str, Any], max_tokens: Optional[int] = None) -> str:
        """Azure OpenAI CLI認証応答取得（制限なし版）"""
        try:
            import openai
            from azure.identity import DefaultAzureCredential, get_bearer_token_provider
        except ImportError:
            return "エラー: openai または azure-identity ライブラリがインストールされていません"
        
        endpoint = config.get('endpoint', '')
        api_version = config.get('api_version', '2024-02-15-preview')
        deployment_name = config.get('deployment_name', '')
        
        if not all([endpoint, deployment_name]):
            return "エラー: Azure CLI設定が不完全です"
        
        try:
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(), 
                "https://cognitiveservices.azure.com/.default"
            )
        except Exception as e:
            return f"エラー: Azure CLI認証に失敗しました: {str(e)}"
        
        client = openai.AzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            azure_ad_token_provider=token_provider,
        )
        
        create_params = {
            "model": deployment_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        
        if max_tokens is not None:
            create_params["max_tokens"] = max_tokens
        
        response = client.chat.completions.create(**create_params)
        return response.choices[0].message.content.strip()

    def _get_bedrock_response(self, prompt: str, config: Dict[str, Any], max_tokens: Optional[int] = None) -> str:
        """AWS Bedrock応答取得（制限なし版）"""
        try:
            import boto3
            import json
        except ImportError:
            return "エラー: boto3 ライブラリがインストールされていません"
        
        aws_access_key_id = config.get('aws_access_key_id', '')
        aws_secret_access_key = config.get('aws_secret_access_key', '')
        aws_region = config.get('aws_region', 'us-east-1')
        model_id = config.get('model_id', 'anthropic.claude-3-haiku-20240307-v1:0')
        
        if not all([aws_access_key_id, aws_secret_access_key]):
            return "エラー: AWS認証情報が設定されていません"
        
        client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )
        
        # モデル別のリクエスト構築
        if 'anthropic.claude' in model_id:
            body_data = {
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
            
            if max_tokens is not None:
                body_data["max_tokens"] = max_tokens
                
            body = json.dumps(body_data)
            
        elif 'amazon.titan' in model_id:
            text_gen_config = {"temperature": 0.7}
            
            if max_tokens is not None:
                text_gen_config["maxTokenCount"] = max_tokens
                
            body = json.dumps({
                "inputText": prompt,
                "textGenerationConfig": text_gen_config
            })
        else:
            return f"エラー: 未対応のBedrockモデル: {model_id}"
        
        response = client.invoke_model(
            body=body,
            modelId=model_id,
            accept='application/json',
            contentType='application/json'
        )
        
        response_body = json.loads(response.get('body').read())
        
        # モデル別のレスポンス解析
        if 'anthropic.claude' in model_id:
            return response_body['content'][0]['text'].strip()
        elif 'amazon.titan' in model_id:
            return response_body['results'][0]['outputText'].strip()
        else:
            return str(response_body)
    
    def test_connection(self, provider_config: Dict[str, Any]) -> bool:
        """各プロバイダーの実際の接続テスト"""
        provider = provider_config.get('provider', '')
        
        try:
            if provider == "ChatGPT API":
                return self._test_openai_connection(provider_config)
            elif provider == "Claude API":
                return self._test_claude_connection(provider_config)
            elif provider == "Azure OpenAI API":
                return self._test_azure_api_connection(provider_config)
            elif provider == "Azure OpenAI CLI":
                return self._test_azure_cli_connection(provider_config)
            elif provider == "AWS Bedrock":
                return self._test_bedrock_connection(provider_config)
            else:
                return False
        except Exception as e:
            print(f"Connection test error: {e}")
            raise e

    def _test_openai_connection(self, config: Dict[str, Any]) -> bool:
        """OpenAI API接続テスト"""
        try:
            import openai
        except ImportError:
            raise Exception("openai ライブラリがインストールされていません")
            
        api_key = config.get('api_key', '')
        base_url = config.get('base_url', '') or None
        model = config.get('model', 'gpt-3.5-turbo')
        
        if not api_key:
            raise Exception("API Keyが設定されていません")
        
        client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # 簡単なテストメッセージ送信
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        
        return len(response.choices) > 0

    def _test_claude_connection(self, config: Dict[str, Any]) -> bool:
        """Claude API接続テスト"""
        try:
            import anthropic
        except ImportError:
            raise Exception("anthropic ライブラリがインストールされていません")
            
        api_key = config.get('api_key', '')
        model = config.get('model', 'claude-3-haiku-20240307')
        
        if not api_key:
            raise Exception("API Keyが設定されていません")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # 簡単なテストメッセージ送信
        response = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        return len(response.content) > 0

    def _test_azure_api_connection(self, config: Dict[str, Any]) -> bool:
        """Azure OpenAI API接続テスト"""
        try:
            import openai
        except ImportError:
            raise Exception("openai ライブラリがインストールされていません")
            
        api_key = config.get('api_key', '')
        endpoint = config.get('endpoint', '')
        api_version = config.get('api_version', '2024-02-15-preview')
        deployment_name = config.get('deployment_name', '')
        
        if not all([api_key, endpoint, deployment_name]):
            raise Exception("API Key、エンドポイント、デプロイメント名が必要です")
        
        client = openai.AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint
        )
        
        # 簡単なテストメッセージ送信
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        
        return len(response.choices) > 0

    def _test_azure_cli_connection(self, config: Dict[str, Any]) -> bool:
        """Azure OpenAI CLI認証接続テスト"""
        try:
            import openai
            from azure.identity import DefaultAzureCredential, get_bearer_token_provider
        except ImportError:
            raise Exception("openai または azure-identity ライブラリがインストールされていません")
            
        endpoint = config.get('endpoint', '')
        api_version = config.get('api_version', '2024-02-15-preview')
        deployment_name = config.get('deployment_name', '')
        
        if not all([endpoint, deployment_name]):
            raise Exception("エンドポイントとデプロイメント名が必要です")
        
        # Azure CLI認証を使用
        try:
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
            )
        except Exception as e:
            raise Exception(f"Azure CLI認証に失敗しました: {str(e)}")
        
        client = openai.AzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            azure_ad_token_provider=token_provider,
        )
        
        # 簡単なテストメッセージ送信
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        
        return len(response.choices) > 0

    def _test_bedrock_connection(self, config: Dict[str, Any]) -> bool:
        """AWS Bedrock接続テスト"""
        try:
            import boto3
        except ImportError:
            raise Exception("boto3 ライブラリがインストールされていません")
            
        aws_access_key_id = config.get('aws_access_key_id', '')
        aws_secret_access_key = config.get('aws_secret_access_key', '')
        aws_region = config.get('aws_region', 'us-east-1')
        model_id = config.get('model_id', 'anthropic.claude-3-haiku-20240307-v1:0')
        
        if not all([aws_access_key_id, aws_secret_access_key]):
            raise Exception("AWS認証情報が必要です")
        
        client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )
        
        # モデルに応じたテスト実行
        if 'anthropic.claude' in model_id:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hello"}]
            })
        elif 'amazon.titan' in model_id:
            body = json.dumps({
                "inputText": "Hello",
                "textGenerationConfig": {"maxTokenCount": 10}
            })
        else:
            raise Exception(f"未対応のモデル: {model_id}")
        
        response = client.invoke_model(
            body=body,
            modelId=model_id,
            accept='application/json',
            contentType='application/json'
        )
        
        return response['ResponseMetadata']['HTTPStatusCode'] == 200