import os
from pathlib import Path
from dotenv import load_dotenv

# Default model if not specified in environment
DEFAULT_MODEL = "gemini-2.5-flash"

class Config:
    def __init__(self):
        # Load default/global configurations from the codebase directory first
        codebase_dir = Path(__file__).resolve().parent
        load_dotenv(codebase_dir / ".env")
        
        # Load environment variables from current working directory (takes precedence)
        cwd = Path.cwd()
        load_dotenv(cwd / ".env", override=True)
        
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
        self.auth_mode = os.getenv("EMATA_AUTH_MODE", "api_key")
        self.safe_mode = os.getenv("EMATA_SAFE_MODE", "true").lower() == "true"
        
        # Load thinking budget and level
        self.thinking_level = os.getenv("GEMINI_THINKING_LEVEL")
        
        budget_str = os.getenv("GEMINI_THINKING_BUDGET")
        self.thinking_budget = None
        if budget_str is not None:
            try:
                self.thinking_budget = int(budget_str)
            except ValueError:
                pass
        
        # Load gemini.md (primary) or .gemini rules file from current working directory if it exists
        self.system_instructions = ""
        gemini_file = cwd / "gemini.md"
        if not gemini_file.exists():
            gemini_file = cwd / ".gemini"
            
        if gemini_file.exists() and gemini_file.is_file():
            try:
                with open(gemini_file, "r", encoding="utf-8") as f:
                    self.system_instructions = f.read().strip()
            except Exception as e:
                self.system_instructions = f"Error reading local gemini file: {e}"

    def check_auth(self) -> bool:
        """Returns True if auth is configured based on current mode."""
        if self.auth_mode == "google_auth":
            return True # Assume ADC is handled by SDK
        return bool(self.api_key)

    def update_env_file(self, key: str, value: str):
        """Updates or adds a key-value pair in the codebase .env file."""
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
        
        # Also update current instance
        if key == "GEMINI_MODEL":
            self.model = value
        elif key == "EMATA_AUTH_MODE":
            self.auth_mode = value
        elif key == "EMATA_SAFE_MODE":
            self.safe_mode = value.lower() == "true"
        elif key == "GEMINI_API_KEY":
            self.api_key = value
