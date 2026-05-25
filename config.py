import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Default model if not specified in environment
DEFAULT_MODEL = "gemini-3-flash-preview"

class Config:
    def __init__(self):
        # 1. Global System Config (~/.config/emata/config.yaml)
        self.global_config_dir = Path.home() / ".config" / "emata"
        self.global_config_path = self.global_config_dir / "config.yaml"
        self.config_data = self._load_global_config()

        # 2. Codebase-level .env (for internal state/defaults)
        codebase_dir = Path(__file__).resolve().parent
        load_dotenv(codebase_dir / ".env")
        
        # 3. Project-level .env (current working directory)
        cwd = Path.cwd()
        load_dotenv(cwd / ".env", override=True)
        
        # Multi-Key Support
        self.keys = self.config_data.get("keys", {})  # { "nickname": "key_value" }
        self.active_key_name = self.config_data.get("active_key_name")
        
        # Resolution Priority: Env Var > Active Config Key > First Available Key
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key and self.active_key_name:
            self.api_key = self.keys.get(self.active_key_name)
        if not self.api_key and self.keys:
            self.active_key_name = next(iter(self.keys))
            self.api_key = self.keys[self.active_key_name]

        self.model = os.getenv("GEMINI_MODEL") or self.config_data.get("model", DEFAULT_MODEL)
        
        # Mode settings
        self.crazy_mode = self._get_bool("EMATA_CRAZY_MODE", "crazy_mode", False)
        self.yolo_mode = self._get_bool("EMATA_YOLO_MODE", "yolo_mode", True)
        self.search_enabled = self._get_bool("EMATA_SEARCH_ENABLED", "search_enabled", True)
        
        # Thinking settings
        self.thinking_level = os.getenv("GEMINI_THINKING_LEVEL") or self.config_data.get("thinking_level")
        self.thinking_budget = self._get_int("GEMINI_THINKING_BUDGET", "thinking_budget")
        
        self.system_instructions = ""

    def _get_bool(self, env_key, config_key, default):
        env_val = os.getenv(env_key)
        if env_val is not None:
            return env_val.lower() == "true"
        return self.config_data.get(config_key, default)

    def _get_int(self, env_key, config_key):
        env_val = os.getenv(env_key)
        if env_val is not None:
            try: return int(env_val)
            except: pass
        return self.config_data.get(config_key)

    def _load_global_config(self):
        if self.global_config_path.exists():
            try:
                with open(self.global_config_path, "r") as f:
                    return yaml.safe_load(f) or {}
            except: return {}
        return {}

    def _save_global_config(self):
        self.global_config_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.global_config_path, "w") as f:
                yaml.safe_dump(self.config_data, f)
        except: pass

    def check_auth(self) -> bool:
        return bool(self.api_key)

    def add_key(self, nickname: str, key_value: str):
        self.keys[nickname] = key_value
        self.active_key_name = nickname
        self.api_key = key_value
        self.config_data["keys"] = self.keys
        self.config_data["active_key_name"] = nickname
        self._save_global_config()

    def switch_key(self, nickname: str) -> bool:
        if nickname in self.keys:
            self.active_key_name = nickname
            self.api_key = self.keys[nickname]
            self.config_data["active_key_name"] = nickname
            self._save_global_config()
            return True
        return False

    def delete_key(self, nickname: str):
        if nickname in self.keys:
            del self.keys[nickname]
            if self.active_key_name == nickname:
                self.active_key_name = next(iter(self.keys)) if self.keys else None
                self.api_key = self.keys[self.active_key_name] if self.active_key_name else None
            self.config_data["keys"] = self.keys
            self.config_data["active_key_name"] = self.active_key_name
            self._save_global_config()

    def update_setting(self, key: str, value):
        key_map = {
            "GEMINI_MODEL": "model",
            "EMATA_CRAZY_MODE": "crazy_mode",
            "EMATA_YOLO_MODE": "yolo_mode",
            "EMATA_SEARCH_ENABLED": "search_enabled"
        }
        config_key = key_map.get(key)
        if config_key:
            self.config_data[config_key] = value
            self._save_global_config()
            # Update instance
            if config_key == "model": self.model = value
            elif config_key == "crazy_mode": self.crazy_mode = value
            elif config_key == "yolo_mode": self.yolo_mode = value
            elif config_key == "search_enabled": self.search_enabled = value

# Singleton instance for tools to access
config_instance = None

def get_config():
    global config_instance
    if config_instance is None:
        config_instance = Config()
    return config_instance
