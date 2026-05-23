import os
import re
import subprocess
from pathlib import Path
from typing import Optional

def list_dir(path: str = ".") -> str:
    """Lists the contents of a directory.

    Args:
        path: The directory path to list (defaults to the current working directory).
    """
    try:
        target = Path(path).resolve()
        # Ensure we stay safe and handle errors
        if not target.exists():
            return f"Error: Directory '{path}' does not exist."
        if not target.is_dir():
            return f"Error: '{path}' is not a directory."

        contents = []
        for entry in os.scandir(target):
            entry_type = "DIR " if entry.is_dir() else "FILE"
            size_str = f" {entry.stat().st_size} bytes" if entry.is_file() else ""
            contents.append(f"[{entry_type}] {entry.name}{size_str}")

        if not contents:
            return f"Directory '{path}' is empty."
        
        return "\n".join(contents)
    except Exception as e:
        return f"Error listing directory '{path}': {e}"

def read_file(path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
    """Reads the contents of a file. Optionally, a range of lines can be read (1-indexed, inclusive).

    Args:
        path: The file path to read (relative or absolute).
        start_line: Optional start line number to read (1-indexed).
        end_line: Optional end line number to read (1-indexed, inclusive).
    """
    try:
        target = Path(path).resolve()
        if not target.exists():
            return f"Error: File '{path}' does not exist."
        if not target.is_file():
            return f"Error: '{path}' is not a file."

        with open(target, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        if start_line is not None or end_line is not None:
            # Handle defaults if one is specified but not the other
            start = (start_line - 1) if start_line is not None else 0
            end = end_line if end_line is not None else len(lines)
            
            # Bound checks
            start = max(0, min(start, len(lines)))
            end = max(0, min(end, len(lines)))
            
            slice_lines = lines[start:end]
            formatted_lines = [f"{i + start + 1}: {line}" for i, line in enumerate(slice_lines)]
            return "".join(formatted_lines)
        else:
            return "".join(lines)
    except Exception as e:
        return f"Error reading file '{path}': {e}"

def write_file(path: str, content: str, overwrite: bool = True) -> str:
    """Creates a new file or overwrites/modifies an existing file with the provided content.
    Automatically creates any missing parent directories.

    Args:
        path: The file path to write to.
        content: The text content to write into the file.
        overwrite: Set to True to overwrite existing files, False to fail if the file already exists.
    """
    try:
        target = Path(path).resolve()
        if target.exists() and not overwrite:
            return f"Error: File '{path}' already exists and overwrite is disabled."
        
        # Ensure parent directories exist
        target.parent.mkdir(parents=True, exist_ok=True)
        
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
            
        action = "Overwritten" if target.exists() else "Created"
        return f"Successfully {action.lower()} file '{path}' with {len(content)} characters."
    except Exception as e:
        return f"Error writing to file '{path}': {e}"

def delete_file(path: str) -> str:
    """Deletes a file.

    Args:
        path: The file path to delete.
    """
    try:
        target = Path(path).resolve()
        if not target.exists():
            return f"Error: File '{path}' does not exist."
        if not target.is_file():
            return f"Error: '{path}' is not a file (directories cannot be deleted with this tool)."

        target.unlink()
        return f"Successfully deleted file '{path}'."
    except Exception as e:
        return f"Error deleting file '{path}': {e}"

def run_command(command: str) -> str:
    """Runs a shell command in the current directory and returns the console output (stdout and stderr).

    Args:
        command: The shell command line string to run.
    """
    try:
        # Run command in the current working directory, capture stdout and stderr, timeout in 60s
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            timeout=60,
            cwd=os.getcwd()
        )
        
        output = []
        if result.stdout:
            output.append(result.stdout)
        if result.stderr:
            output.append(f"Stderr:\n{result.stderr}")
            
        combined = "".join(output).strip()
        if not combined:
            return f"Command executed successfully with exit code {result.returncode} (no output)."
            
        return f"Exit Code: {result.returncode}\n\n{combined}"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 60 seconds."
    except Exception as e:
        return f"Error executing command: {e}"

def search_grep(pattern: str, path: str = ".", recursive: bool = True) -> str:
    """Recursively searches for a regular expression pattern in files.

    Args:
        pattern: The regular expression pattern to search for (case-insensitive by default).
        path: The directory or file path to start the search from (defaults to '.').
        recursive: Whether to search subdirectories recursively.
    """
    try:
        base_path = Path(path).resolve()
        if not base_path.exists():
            return f"Error: Path '{path}' does not exist."
            
        results = []
        pattern_re = re.compile(pattern, re.IGNORECASE)
        
        # Find files to search
        files_to_search = []
        if base_path.is_file():
            files_to_search.append(base_path)
        else:
            glob_pattern = "**/*" if recursive else "*"
            for p in base_path.glob(glob_pattern):
                if p.is_file():
                    # Skip common build, git, and environment dirs
                    if any(ignored in p.parts for ignored in [".git", "__pycache__", ".venv", "node_modules", "venv", "build", "dist"]):
                        continue
                    files_to_search.append(p)
                    
        for file_path in files_to_search:
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern_re.search(line):
                            relative_path = file_path.relative_to(Path.cwd()) if file_path.is_relative_to(Path.cwd()) else file_path
                            results.append(f"{relative_path}:{line_num}: {line.strip()}")
            except Exception:
                continue
                
        if not results:
            return f"No matches found for pattern: '{pattern}'"
            
        limited_results = results[:100]
        output = "\n".join(limited_results)
        if len(results) > 100:
            output += f"\n\n... (truncated {len(results) - 100} more matches)"
            
        return output
    except Exception as e:
        return f"Error running search_grep: {e}"

def replace_text_in_file(path: str, search_text: str, replace_text: str, count: int = 1) -> str:
    """Finds and replaces a block of text in a file. Very useful for editing specific parts of large files.

    Args:
        path: The file path to modify.
        search_text: The exact block of text or string to search for in the file.
        replace_text: The replacement text.
        count: The maximum number of occurrences to replace (defaults to 1).
    """
    try:
        target = Path(path).resolve()
        if not target.exists():
            return f"Error: File '{path}' does not exist."
        if not target.is_file():
            return f"Error: '{path}' is not a file."
            
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
            
        if search_text not in content:
            return f"Error: Search text block not found in file '{path}'."
            
        new_content = content.replace(search_text, replace_text, count)
        
        with open(target, "w", encoding="utf-8") as f:
            f.write(new_content)
            
        return f"Successfully replaced {count} occurrence(s) in file '{path}'."
    except Exception as e:
        return f"Error replacing text in file '{path}': {e}"

# Expose tools as a dictionary for easy execution lookup
TOOL_MAPPING = {
    "list_dir": list_dir,
    "read_file": read_file,
    "write_file": write_file,
    "delete_file": delete_file,
    "run_command": run_command,
    "search_grep": search_grep,
    "replace_text_in_file": replace_text_in_file,
}

# Get tool list for API registration
ALL_TOOLS = list(TOOL_MAPPING.values())
