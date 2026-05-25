import os
import re
import subprocess
from pathlib import Path
from typing import Optional

import shutil
import logging

logger = logging.getLogger("emata.tools")

def get_config_instance():
    from config import get_config
    return get_config()

def is_safe_path(path: str) -> bool:
    try:
        target = Path(path).resolve()
        cwd = Path.cwd().resolve()
        return target == cwd or cwd in target.parents
    except Exception:
        return False

def backup_file(path: Path):
    if path.exists() and path.is_file():
        try:
            bak_path = path.with_suffix(path.suffix + ".bak")
            shutil.copy2(path, bak_path)
        except: pass

def clean_output(text: str, max_chars: int = 5000) -> str:
    """Cleans terminal noise, strips ANSI codes, and truncates output."""
    if not text: return ""
    # Strip ANSI escape sequences (colors, etc.)
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    text = ansi_escape.sub('', text)
    
    # Cap total output size to prevent token flooding
    if len(text) > max_chars:
        return text[:max_chars] + f"\n... [Truncated! Total output was {len(text)} chars]"
    return text

def list_dir(path: str = ".") -> str:
    config = get_config_instance()
    if config and not config.yolo_mode and not is_safe_path(path):
        return f"Error: YOLO Mode is OFF. Access to '{path}' denied."
    try:
        target = Path(path).resolve()
        if not target.exists(): return f"Error: '{path}' does not exist."
        contents = []
        for entry in os.scandir(target):
            entry_type = "DIR " if entry.is_dir() else "FILE"
            size = f" {entry.stat().st_size} bytes" if entry.is_file() else ""
            contents.append(f"[{entry_type}] {entry.name}{size}")
        return clean_output("\n".join(contents)) if contents else f"Directory '{path}' is empty."
    except Exception as e: return f"Error: {e}"

def read_file(path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
    config = get_config_instance()
    if config and not config.yolo_mode and not is_safe_path(path):
        return f"Error: YOLO Mode is OFF. Access denied."
    try:
        target = Path(path).resolve()
        if not target.exists(): return f"Error: File not found."
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        start = (start_line - 1) if start_line is not None else 0
        end = end_line if end_line is not None else len(lines)
        return clean_output("".join(lines[start:end]), max_chars=10000)
    except Exception as e: return f"Error: {e}"

def write_file(path: str, content: str, overwrite: bool = True) -> str:
    config = get_config_instance()
    if config and not config.yolo_mode and not is_safe_path(path):
        return f"Error: YOLO Mode is OFF. Access denied."
    try:
        target = Path(path).resolve()
        backup_file(target)
        if target.exists() and not overwrite: return f"Error: File exists."
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote '{path}'."
    except Exception as e: return f"Error: {e}"

def run_command(command: str) -> str:
    config = get_config_instance()
    if config and not config.yolo_mode:
        blocked = [r"\.\./", r"/\.\.", r"~/", r"/etc", r"/var", r"/root", r"/usr"]
        if any(re.search(p, command) for p in blocked):
            return "Error: YOLO Mode is OFF. Unsafe path reference."
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True, timeout=120)
        output = f"Exit Code: {result.returncode}\n\n{result.stdout}\n{result.stderr}".strip()
        return clean_output(output, max_chars=5000)
    except Exception as e: return f"Error: {e}"

def search_grep(pattern: str, path: str = ".", recursive: bool = True) -> str:
    config = get_config_instance()
    if config and not config.yolo_mode and not is_safe_path(path):
        return "Error: YOLO Mode is OFF. Access denied."
    try:
        base = Path(path).resolve()
        results = []
        regex = re.compile(pattern, re.IGNORECASE)
        glob_p = "**/*" if recursive else "*"
        for p in base.glob(glob_p):
            if p.is_file() and not any(i in p.parts for i in [".git", "__pycache__", ".venv", "node_modules", "dist", ".next"]):
                try:
                    with open(p, "r", encoding="utf-8", errors="replace") as f:
                        for i, line in enumerate(f, 1):
                            if regex.search(line):
                                rel = p.relative_to(Path.cwd()) if p.is_relative_to(Path.cwd()) else p
                                display_line = line.strip()
                                if len(display_line) > 500:
                                    display_line = display_line[:500] + "... [truncated line]"
                                results.append(f"{rel}:{i}: {display_line}")
                                if len(results) > 100: break
                except: continue
            if len(results) > 100: break
        output = "\n".join(results) if results else "No matches found."
        return clean_output(output, max_chars=8000)
    except Exception as e: return f"Error: {e}"

def replace_text_in_file(path: str, search_text: str, replace_text: str, count: int = 1) -> str:
    config = get_config_instance()
    if config and not config.yolo_mode and not is_safe_path(path):
        return "Error: YOLO Mode is OFF. Access denied."
    try:
        target = Path(path).resolve()
        backup_file(target)
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        if search_text not in content: return "Error: Search text not found."
        with open(target, "w", encoding="utf-8") as f:
            f.write(content.replace(search_text, replace_text, count))
        return f"Successfully replaced {count} occurrences in '{path}'."
    except Exception as e: return f"Error: {e}"

TOOL_MAPPING = {
    "list_dir": list_dir,
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command,
    "search_grep": search_grep,
    "replace_text_in_file": replace_text_in_file,
}

ALL_TOOLS = list(TOOL_MAPPING.values())
