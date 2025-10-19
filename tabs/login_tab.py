# tabs/login_tab.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                               QLineEdit, QLabel, QPushButton, QComboBox, 
                               QTextEdit, QCheckBox)
from utils.config_manager import ConfigManager
import json
import subprocess

class LoginTab(QWidget):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # LLMプロバイダー選択
        provider_group = QGroupBox("LLMプロバイダー設定")
        provider_layout = QVBoxLayout()
        
        self.provider_combo = QComboBox()
        self.provider_combo.addItems([
            "ChatGPT API", "Claude API", "Azure OpenAI API", 
            "Azure OpenAI CLI", "AWS Bedrock"
        ])
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        provider_layout.addWidget(QLabel("プロバイダー:"))
        provider_layout.addWidget(self.provider_combo)
        
        # 動的設定エリア
        self.config_area = QWidget()
        self.config_layout = QVBoxLayout(self.config_area)
        provider_layout.addWidget(self.config_area)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.test_button = QPushButton("接続テスト")
        self.save_button = QPushButton("設定保存")
        self.load_button = QPushButton("設定読込")
        
        self.test_button.clicked.connect(self.test_connection)
        self.save_button.clicked.connect(self.save_config)
        self.load_button.clicked.connect(self.load_config)
        
        button_layout.addWidget(self.test_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.load_button)
        
        provider_layout.addLayout(button_layout)
        provider_group.setLayout(provider_layout)
        
        # ログ表示
        log_group = QGroupBox("ログ")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        
        layout.addWidget(provider_group)
        layout.addWidget(log_group)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # 初期設定UI作成
        self.on_provider_changed()
        self.load_config()

    def on_provider_changed(self):
        # 既存のウィジェットをクリア
        for i in reversed(range(self.config_layout.count())):
            child = self.config_layout.itemAt(i)
            if child.widget():
                child.widget().setParent(None)
            elif child.layout():
                # レイアウトの場合は中身も削除
                layout = child.layout()
                for j in reversed(range(layout.count())):
                    layout.itemAt(j).widget().setParent(None)
                self.config_layout.removeItem(child)
        
        provider = self.provider_combo.currentText()
        self.config_widgets = {}
        
        # Azure CLI専用の属性もクリア
        if hasattr(self, 'check_auth_button'):
            delattr(self, 'check_auth_button')
        if hasattr(self, 'login_button'):
            delattr(self, 'login_button')
        if hasattr(self, 'logout_button'):
            delattr(self, 'logout_button')
        if hasattr(self, 'auth_status_label'):
            delattr(self, 'auth_status_label')
        
        if provider == "ChatGPT API":
            self.create_openai_config()
        elif provider == "Claude API":
            self.create_claude_config()
        elif provider == "Azure OpenAI API":
            self.create_azure_api_config()
        elif provider == "Azure OpenAI CLI":
            self.create_azure_cli_config()
        elif provider == "AWS Bedrock":
            self.create_bedrock_config()
            
    def create_openai_config(self):
        # API Key
        self.config_widgets['api_key'] = QLineEdit()
        self.config_widgets['api_key'].setEchoMode(QLineEdit.Password)
        self.config_layout.addWidget(QLabel("API Key:"))
        self.config_layout.addWidget(self.config_widgets['api_key'])
        
        # Model
        self.config_widgets['model'] = QComboBox()
        self.config_widgets['model'].addItems(['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'])
        self.config_widgets['model'].setEditable(True)
        self.config_layout.addWidget(QLabel("モデル:"))
        self.config_layout.addWidget(self.config_widgets['model'])
        
        # Base URL (Optional)
        self.config_widgets['base_url'] = QLineEdit()
        self.config_widgets['base_url'].setPlaceholderText("https://api.openai.com/v1 (デフォルト)")
        self.config_layout.addWidget(QLabel("Base URL (オプション):"))
        self.config_layout.addWidget(self.config_widgets['base_url'])

    def create_claude_config(self):
        # API Key
        self.config_widgets['api_key'] = QLineEdit()
        self.config_widgets['api_key'].setEchoMode(QLineEdit.Password)
        self.config_layout.addWidget(QLabel("API Key:"))
        self.config_layout.addWidget(self.config_widgets['api_key'])
        
        # Model
        self.config_widgets['model'] = QComboBox()
        self.config_widgets['model'].addItems(['claude-3-5-sonnet-20241022', 'claude-3-haiku-20240307', 'claude-3-opus-20240229'])
        self.config_widgets['model'].setEditable(True)
        self.config_layout.addWidget(QLabel("モデル:"))
        self.config_layout.addWidget(self.config_widgets['model'])

    def create_azure_api_config(self):
        # API Key
        self.config_widgets['api_key'] = QLineEdit()
        self.config_widgets['api_key'].setEchoMode(QLineEdit.Password)
        self.config_layout.addWidget(QLabel("API Key:"))
        self.config_layout.addWidget(self.config_widgets['api_key'])
        
        # Endpoint
        self.config_widgets['endpoint'] = QLineEdit()
        self.config_widgets['endpoint'].setPlaceholderText("https://your-resource.openai.azure.com/")
        self.config_layout.addWidget(QLabel("Azure エンドポイント:"))
        self.config_layout.addWidget(self.config_widgets['endpoint'])
        
        # API Version
        self.config_widgets['api_version'] = QComboBox()
        self.config_widgets['api_version'].addItems(['2024-02-15-preview', '2023-12-01-preview', '2023-09-15-preview'])
        self.config_widgets['api_version'].setEditable(True)
        self.config_layout.addWidget(QLabel("API Version:"))
        self.config_layout.addWidget(self.config_widgets['api_version'])
        
        # Deployment Name
        self.config_widgets['deployment_name'] = QLineEdit()
        self.config_layout.addWidget(QLabel("デプロイメント名:"))
        self.config_layout.addWidget(self.config_widgets['deployment_name'])

    def create_azure_cli_config(self):
        # CLI認証の説明
        info_label = QLabel("Azure CLI認証を使用します。")
        info_label.setStyleSheet("color: blue; font-style: italic;")
        self.config_layout.addWidget(info_label)
        
        # 認証状態確認・ログインボタン
        auth_layout = QHBoxLayout()
        self.check_auth_button = QPushButton("認証状態確認")
        self.login_button = QPushButton("Azureにログイン")
        self.logout_button = QPushButton("ログアウト")
        
        self.check_auth_button.clicked.connect(self.check_azure_auth)
        self.login_button.clicked.connect(self.azure_login)
        self.logout_button.clicked.connect(self.azure_logout)
        
        auth_layout.addWidget(self.check_auth_button)
        auth_layout.addWidget(self.login_button)
        auth_layout.addWidget(self.logout_button)
        self.config_layout.addLayout(auth_layout)
        
        # 認証状態表示
        self.auth_status_label = QLabel("認証状態: 未確認")
        self.config_layout.addWidget(self.auth_status_label)
        
        # Endpoint
        self.config_widgets['endpoint'] = QLineEdit()
        self.config_widgets['endpoint'].setPlaceholderText("https://your-resource.openai.azure.com/")
        self.config_layout.addWidget(QLabel("Azure エンドポイント:"))
        self.config_layout.addWidget(self.config_widgets['endpoint'])
        
        # API Version
        self.config_widgets['api_version'] = QComboBox()
        self.config_widgets['api_version'].addItems(['2024-02-15-preview', '2023-12-01-preview'])
        self.config_widgets['api_version'].setEditable(True)
        self.config_layout.addWidget(QLabel("API Version:"))
        self.config_layout.addWidget(self.config_widgets['api_version'])
        
        # Deployment Name
        self.config_widgets['deployment_name'] = QLineEdit()
        self.config_layout.addWidget(QLabel("デプロイメント名:"))
        self.config_layout.addWidget(self.config_widgets['deployment_name'])
        
        # 初回認証状態確認
        self.check_azure_auth()

    def check_azure_auth(self):
        """Azure CLI認証状態を確認"""
        try:
            # Windowsではshell=Trueを使用してコマンドを実行
            # encoding='cp932'で日本語Windowsの文字コードを正しく処理
            result = subprocess.run(['az', 'account', 'show'], 
                                capture_output=True, text=True, encoding='cp932', 
                                errors='replace', timeout=10, shell=True)
            
            if result.returncode == 0 and result.stdout and result.stdout.strip():
                try:
                    account_info = json.loads(result.stdout)
                    user_name = account_info.get('user', {}).get('name', 'Unknown')
                    subscription_name = account_info.get('name', 'Unknown')
                    
                    self.auth_status_label.setText(
                        f"認証状態: ログイン済み\nユーザー: {user_name}\nサブスクリプション: {subscription_name}"
                    )
                    self.auth_status_label.setStyleSheet("color: green;")
                    self.log_text.append(f"✅ Azure認証確認: {user_name} ({subscription_name})")
                    return True
                except json.JSONDecodeError:
                    self.auth_status_label.setText("認証状態: 情報取得エラー")
                    self.auth_status_label.setStyleSheet("color: orange;")
                    self.log_text.append("⚠️ Azure認証情報のパースに失敗しました")
                    return False
            else:
                self.auth_status_label.setText("認証状態: ログインが必要")
                self.auth_status_label.setStyleSheet("color: red;")
                if result.stderr:
                    self.log_text.append(f"❌ Azure認証が必要です: {result.stderr}")
                else:
                    self.log_text.append("❌ Azure認証が必要です")
                return False
                
        except subprocess.TimeoutExpired:
            self.auth_status_label.setText("認証状態: タイムアウト")
            self.auth_status_label.setStyleSheet("color: orange;")
            self.log_text.append("⚠️ Azure CLI認証確認がタイムアウトしました")
            return False
        except FileNotFoundError:
            self.auth_status_label.setText("認証状態: Azure CLI未インストール")
            self.auth_status_label.setStyleSheet("color: red;")
            self.log_text.append("❌ Azure CLIがインストールされていません")
            self.log_text.append("https://docs.microsoft.com/cli/azure/install-azure-cli からインストールしてください")
            return False
        except Exception as e:
            self.auth_status_label.setText(f"認証状態: エラー")
            self.auth_status_label.setStyleSheet("color: red;")
            self.log_text.append(f"❌ Azure認証確認エラー: {str(e)}")
            return False

    def azure_login(self):
        """Azure CLIログイン（ブラウザ認証）"""
        try:
            self.log_text.append("🌐 ブラウザでAzure認証を開始します...")
            
            # Windowsではshell=Trueを使用してコマンドを実行
            # encoding='cp932'で日本語Windowsの文字コードを正しく処理
            result = subprocess.run(['az', 'login'], 
                                capture_output=True, text=True, encoding='cp932',
                                errors='replace', timeout=120, shell=True)
            
            if result.returncode == 0:
                self.log_text.append("✅ Azure認証が完了しました")
                self.check_azure_auth()  # 認証状態を更新
            else:
                self.log_text.append(f"❌ Azure認証に失敗: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            self.log_text.append("⚠️ Azure認証がタイムアウトしました（120秒）")
        except FileNotFoundError:
            self.log_text.append("❌ Azure CLIがインストールされていません")
            self.log_text.append("https://docs.microsoft.com/cli/azure/install-azure-cli からインストールしてください")
        except Exception as e:
            self.log_text.append(f"❌ Azure認証エラー: {str(e)}")

    def azure_logout(self):
        """Azure CLIログアウト"""
        try:
            # Windowsではshell=Trueを使用してコマンドを実行
            # encoding='cp932'で日本語Windowsの文字コードを正しく処理
            result = subprocess.run(['az', 'logout'], 
                                capture_output=True, text=True, encoding='cp932',
                                errors='replace', timeout=30, shell=True)
            
            if result.returncode == 0:
                self.log_text.append("✅ Azureからログアウトしました")
                self.check_azure_auth()  # 認証状態を更新
            else:
                self.log_text.append(f"❌ ログアウトに失敗: {result.stderr}")
                
        except Exception as e:
            self.log_text.append(f"❌ ログアウトエラー: {str(e)}")

    def create_bedrock_config(self):
        # AWS Access Key ID
        self.config_widgets['aws_access_key_id'] = QLineEdit()
        self.config_widgets['aws_access_key_id'].setEchoMode(QLineEdit.Password)
        self.config_layout.addWidget(QLabel("AWS Access Key ID:"))
        self.config_layout.addWidget(self.config_widgets['aws_access_key_id'])
        
        # AWS Secret Access Key
        self.config_widgets['aws_secret_access_key'] = QLineEdit()
        self.config_widgets['aws_secret_access_key'].setEchoMode(QLineEdit.Password)
        self.config_layout.addWidget(QLabel("AWS Secret Access Key:"))
        self.config_layout.addWidget(self.config_widgets['aws_secret_access_key'])
        
        # AWS Region
        self.config_widgets['aws_region'] = QComboBox()
        self.config_widgets['aws_region'].addItems(['us-east-1', 'us-west-2', 'ap-northeast-1', 'eu-west-1'])
        self.config_widgets['aws_region'].setEditable(True)
        self.config_layout.addWidget(QLabel("AWS Region:"))
        self.config_layout.addWidget(self.config_widgets['aws_region'])
        
        # Model ID
        self.config_widgets['model_id'] = QComboBox()
        self.config_widgets['model_id'].addItems([
            'anthropic.claude-3-sonnet-20240229-v1:0',
            'anthropic.claude-3-haiku-20240307-v1:0',
            'amazon.titan-text-express-v1'
        ])
        self.config_widgets['model_id'].setEditable(True)
        self.config_layout.addWidget(QLabel("Model ID:"))
        self.config_layout.addWidget(self.config_widgets['model_id'])

    def test_connection(self):
        self.log_text.append("接続テスト開始...")
        
        try:
            config = self.get_current_config()
            from utils.llm_manager import LLMManager
            llm_manager = LLMManager()
            
            if llm_manager.test_connection(config):
                self.log_text.append("✅ 接続テスト成功")
            else:
                self.log_text.append("❌ 接続テスト失敗")
        except Exception as e:
            self.log_text.append(f"❌ 接続テストエラー: {str(e)}")

    def save_config(self):
        try:
            config = self.get_current_config()
            self.config_manager.save_llm_config(config)
            self.log_text.append("✅ 設定を保存しました")
        except Exception as e:
            self.log_text.append(f"❌ 設定保存エラー: {str(e)}")

    def load_config(self):
        try:
            config = self.config_manager.load_llm_config()
            if config:
                # プロバイダー選択
                provider = config.get('provider', '')
                index = self.provider_combo.findText(provider)
                if index >= 0:
                    self.provider_combo.setCurrentIndex(index)
                
                # 各設定値を復元
                for key, widget in self.config_widgets.items():
                    value = config.get(key, '')
                    if isinstance(widget, QLineEdit):
                        widget.setText(value)
                    elif isinstance(widget, QComboBox):
                        widget.setCurrentText(value)
                
                self.log_text.append("✅ 設定を読み込みました")
        except Exception as e:
            self.log_text.append(f"❌ 設定読込エラー: {str(e)}")

    def get_current_config(self):
        config = {'provider': self.provider_combo.currentText()}
        
        for key, widget in self.config_widgets.items():
            if isinstance(widget, QLineEdit):
                config[key] = widget.text()
            elif isinstance(widget, QComboBox):
                config[key] = widget.currentText()
        
        return config