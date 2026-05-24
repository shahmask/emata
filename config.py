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
        
        # Priority: Env Var > Global Config > Default
        self.api_key = os.getenv("GEMINI_API_KEY") or self.config_data.get("api_key")
        self.model = os.getenv("GEMINI_MODEL") or self.config_data.get("model", DEFAULT_MODEL)
        self.auth_mode = os.getenv("EMATA_AUTH_MODE") or self.config_data.get("auth_mode", "api_key")
        
        # Crazy Mode (True = No prompts)
        crazy_env = os.getenv("EMATA_CRAZY_MODE")
        if crazy_env is not None:
            self.crazy_mode = crazy_env.lower() == "true"
        else:
            self.crazy_mode = self.config_data.get("crazy_mode", False)

        # YOLO Mode (True = Full system access)
        yolo_env = os.getenv("EMATA_YOLO_MODE")
        if yolo_env is not None:
            self.yolo_mode = yolo_env.lower() == "true"
        else:
            self.yolo_mode = self.config_data.get("yolo_mode", True)

        search_env = os.getenv("EMATA_SEARCH_ENABLED")
        if search_env is not None:
            self.search_enabled = search_env.lower() == "true"
        else:
            self.search_enabled = self.config_data.get("search_enabled", True)
        
        # Load thinking budget and level
        self.thinking_level = os.getenv("GEMINI_THINKING_LEVEL") or self.config_data.get("thinking_level")
        
        budget_str = os.getenv("GEMINI_THINKING_BUDGET")
        if budget_str is not None:
            try:
                self.thinking_budget = int(budget_str)
            except ValueError:
                self.thinking_budget = self.config_data.get("thinking_budget")
        else:
            self.thinking_budget = self.config_data.get("thinking_budget")
        
        # Load gemini.md (primary) or .gemini rules file from current working directory if it exists
        self.system_instructions = ""

    def _load_global_config(self):
        """Loads the global YAML config file."""
        if self.global_config_path.exists():
            try:
                with open(self.global_config_path, "r") as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                return {}
        return {}

    def _save_global_config(self):
        """Saves the current config state to the global YAML file."""
        self.global_config_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.global_config_path, "w") as f:
                yaml.safe_dump(self.config_data, f)
        except Exception:
            pass

    def check_auth(self) -> bool:
        """Returns True if auth is configured based on current mode."""
        if self.auth_mode == "google_auth":
            return True # Assume ADC is handled by SDK
        return bool(self.api_key)

    def update_env_file(self, key: str, value: str):
        """Updates the key in global config (primary) and syncs to codebase .env (legacy)."""
        # Update internal config data
        config_key_map = {
            "GEMINI_MODEL": "model",
            "EMATA_AUTH_MODE": "auth_mode",
            "EMATA_CRAZY_MODE": "crazy_mode",
            "EMATA_YOLO_MODE": "yolo_mode",
            "EMATA_SEARCH_ENABLED": "search_enabled",
            "GEMINI_API_KEY": "api_key"
        }
        
        config_key = config_key_map.get(key)
        if config_key:
            # Convert string booleans to actual booleans for YAML
            if value.lower() == "true":
                self.config_data[config_key] = True
            elif value.lower() == "false":
                self.config_data[config_key] = False
            else:
                self.config_data[config_key] = value
            self._save_global_config()

        # Legacy Support: Update codebase .env file
        codebase_dir = Path(__file__).resolve().parent
        env_path = codebase_dir / ".env"
        
        lines = []
        found = False
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        
        new_lines = []
        for line in lines:
            if line.strip().startswith(f"{key}="):
                new_lines.append(f'{key}="{value}"\n')
                found = True
            else:
                new_lines.append(line)
        
        if not found:
            new_lines.append(f'{key}="{value}"\n')
            
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        
        # Update current instance attributes
        if key == "GEMINI_MODEL":
            self.model = value
        elif key == "EMATA_AUTH_MODE":
            self.auth_mode = value
        elif key == "EMATA_CRAZY_MODE":
            self.crazy_mode = value.lower() == "true"
        elif key == "EMATA_YOLO_MODE":
            self.yolo_mode = value.lower() == "true"
        elif key == "EMATA_SEARCH_ENABLED":
            self.search_enabled = value.lower() == "true"
        elif key == "GEMINI_API_KEY":
            self.api_key = value
