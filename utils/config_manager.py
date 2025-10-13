# utils/config_manager.py
import json
import os
from typing import Dict, Any

class ConfigManager:
    def __init__(self):
        self.config_dir = "configs"
        os.makedirs(self.config_dir, exist_ok=True)
        
    def save_llm_config(self, config: Dict[str, Any]):
        config_file = os.path.join(self.config_dir, "llm_config.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def load_llm_config(self) -> Dict[str, Any]:
        config_file = os.path.join(self.config_dir, "llm_config.json")
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_vector_config(self, config: Dict[str, Any]):
        config_file = os.path.join(self.config_dir, "vector_config.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)