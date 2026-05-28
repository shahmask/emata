#!/usr/bin/env python3
import sys, os, traceback, platform, datetime, argparse, warnings, re, webbrowser
from pathlib import Path

# Suppress warnings early
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*urllib3 v2 only supports OpenSSL 1.1.1+.*")

VERSION = "1.1.7"
REPO_URL = "https://github.com/shahmask/emata"

try:
    from config import get_config
    from agent import Agent
    from tools import TOOL_MAPPING
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.table import Table
    console = Console()
except Exception as e:
    print(f"\nFATAL IMPORT ERROR: {e}")
    sys.exit(1)

# 1. IMMEDIATE LOGGING
os.makedirs(os.path.expanduser("~/.emata"), exist_ok=True)
BOOT_LOG = os.path.expanduser("~/.emata/boot_debug.log")

def log(msg):
    try:
        # Prevent log from growing indefinitely (1MB limit)
        if os.path.exists(BOOT_LOG) and os.path.getsize(BOOT_LOG) > 1024 * 1024:
            with open(BOOT_LOG, "w") as f:
                f.write("[LOG ROTATED]\n")
        
        with open(BOOT_LOG, "a") as f:
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            f.write(f"[{ts}] {msg}\n")
    except: pass

def handle_key_manager(config):
    while True:
        console.print("\n[bold cyan]🔑 API Key Manager[/bold cyan]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Status", width=10)
        table.add_column("Nickname", width=20)
        table.add_column("Key (Partial)", width=30)
        for name, val in config.keys.items():
            status = "[bold green]ACTIVE[/bold green]" if name == config.active_key_name else ""
            display_key = f"{val[:6]}...{val[-4:]}" if len(val) > 10 else val
            table.add_row(status, name, display_key)
        console.print(table)
        console.print("\nOptions: [b]add[/b], [b]switch[/b], [b]delete[/b], [b]back[/b]")
        try:
            cmd = input("\nkeys > ").strip().lower()
            if cmd == "back": break
            if cmd == "add":
                nick = input("Nickname: ").strip()
                val = input("Key: ").strip()
                if nick and val: config.add_key(nick, val)
            elif cmd == "switch":
                nick = input("Nickname: ").strip()
                config.switch_key(nick)
            elif cmd == "delete":
                nick = input("Nickname: ").strip()
                config.delete_key(nick)
        except: break

def handle_model_selector(config, agent):
    console.print("\n[bold cyan]🔭 Fetching available Gemini models...[/bold cyan]")
    try:
        models = [m.name.replace("models/", "") for m in agent.client.models.list() if "gemini" in m.name.lower()]
        if not models:
            console.print("[yellow]No Gemini models found.[/yellow]")
            return False
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("#", width=4)
        table.add_column("Model Name", width=40)
        table.add_column("Status", width=10)
        for i, m_name in enumerate(models, 1):
            status = "[bold green]ACTIVE[/bold green]" if m_name == config.model else ""
            table.add_row(str(i), m_name, status)
        console.print(table)
        choice = input("\nSelect model number (or 'back'): ").strip().lower()
        if choice != "back" and choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                new_model = models[idx]
                config.update_setting("GEMINI_MODEL", new_model)
                console.print(f"[green]Switched to model: {new_model}[/green]")
                return True 
    except Exception as e:
        console.print(f"[red]Failed to list models: {e}[/red]")
    return False

def handle_report_issue(config):
    console.print("\n[bold red]🐞 Report an Issue[/bold red]")
    console.print("This will open the Emata GitHub issues page and provide diagnostic info.")
    
    # Collect diagnostics
    diag = (
        f"EMATA Version: {VERSION}\n"
        f"Python Version: {platform.python_version()}\n"
        f"OS: {platform.system()} {platform.release()}\n"
        f"Model: {config.model}\n"
    )
    
    console.print("\n[bold cyan]Diagnostic Info (Copy this for your report):[/bold cyan]")
    console.print(Panel(diag, border_style="dim"))
    
    try:
        if input("\nOpen GitHub issues page? (y/n): ").lower() == "y":
            webbrowser.open(f"{REPO_URL}/issues/new")
            console.print("[green]Opening browser...[/green]")
    except:
        console.print(f"\nPlease visit: {REPO_URL}/issues")

def display_help():
    console.print("\n[bold cyan]📖 Runtime Commands[/bold cyan]")
    console.print("  [b]:help[/b]      - Show this guide")
    console.print("  [b]:keys[/b]      - Manage API keys")
    console.print("  [b]:model[/b]     - Switch Gemini models")
    console.print("  [b]:clear[/b]     - Reset session history")
    console.print("  [b]:report[/b]    - Report a bug or issue")
    console.print("  [b]:yolo[/b]      - Toggle YOLO mode")
    console.print("  [b]:crazy[/b]     - Toggle tool confirmation")
    console.print("  [b]:session[/b]   - Show current details")
    console.print("  [b]:exit[/b]      - Exit Emata")

def print_header(config):
    active_tag = f"[bold green]{config.active_key_name}[/bold green]"
    active_model = f"[bold cyan]{config.model}[/bold cyan]"
    c_status = "[bold magenta]On[/bold magenta]" if config.crazy_mode else "[dim]Off[/dim]"
    y_status = "[bold red]On[/bold red]" if config.yolo_mode else "[dim]Off[/dim]"
    header_text = Text.from_markup(
        f"[bold yellow]EMATA Online[/bold yellow] ({active_tag})\n"
        f"───────────────────────────────────────────────────\n"
        f"Model: {active_model}\n"
        f"Crazy: {c_status} | YOLO: {y_status}"
    )
    console.print(Panel(header_text, style="bold cyan", border_style="cyan", padding=(0, 1)))

def is_tool_safe(name, args):
    if name in ["list_dir", "read_file", "search_grep"]: return True
    if name == "run_command":
        cmd = args.get("command", "").lower().strip()
        safe_prefixes = ["ls ", "cat ", "curl ", "grep ", "pwd", "whoami", "date", "which ", "echo "]
        return any(cmd.startswith(p) or cmd == p.strip() for p in safe_prefixes)
    return False

def handle_session_manager(config, agent):
    console.print("\n[bold cyan]🛰️ Session Manager[/bold cyan]")
    
    if os.environ.get("TMUX"):
        console.print("\n[bold]Active TMUX Sessions for this directory:[/bold]")
        try:
            current_session = os.environ.get("TMUX_SESSION_NAME")
            current_dir = os.getcwd()
            res = subprocess.run(
                ["tmux", "list-sessions", "-F", "#{session_name} #{session_attached} #{@emata_pwd}"],
                capture_output=True, text=True
            )
            if res.returncode == 0:
                found = False
                for line in res.stdout.strip().split("\n"):
                    parts = line.split(" ", 2)
                    if len(parts) >= 3 and parts[2].strip() == current_dir:
                        name, attached = parts[0], parts[1]
                        status = "[bold green]● CURRENT[/bold green]" if name == current_session else ("[blue]Attached[/blue]" if attached == "1" else "[dim]Detached[/dim]")
                        console.print(f"  {status} [magenta]{name}[/magenta]")
                        found = True
                if not found: console.print("  [dim]No other sessions found.[/dim]")
        except: console.print("  [dim]Could not query TMUX.[/dim]")
    
    console.print("\n[bold]Recent History Files (~/.emata/sessions):[/bold]")
    try:
        files = sorted(Path(agent.session_dir).glob("*.json"), key=os.path.getmtime, reverse=True)
        if files:
            for f in files[:5]:
                dt = datetime.datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                console.print(f"  [dim]{dt}[/dim] [cyan]{f.name}[/cyan] ({f.stat().st_size} bytes)")
        else: console.print("  [dim]No history files found.[/dim]")
    except: console.print("  [dim]Error listing history.[/dim]")
    
    console.print("\n[dim]Tip: To switch to an active session, open a new terminal and use the startup menu.[/dim]")

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("query", nargs="*")
    parser.add_argument("-m", "--model")
    parser.add_argument("-k", "--key")
    parser.add_argument("-f", "--file", action="append", default=[])
    parser.add_argument("-d", "--dir", action="append", default=[])
    parser.add_argument("--diff", action="store_true")
    parser.add_argument("--yolo", action="store_true")
    parser.add_argument("--crazy", action="store_true")
    args = parser.parse_args()
    
    config = get_config()
    if args.key: config.switch_key(args.key)
    if args.model: config.update_setting("GEMINI_MODEL", args.model)
    if args.yolo: config.update_setting("EMATA_YOLO_MODE", True)
    if args.crazy: config.update_setting("EMATA_CRAZY_MODE", True)

    log(f"--- EMATA STARTUP v{VERSION} ---")
    console.print(f"[dim]EMATA v{VERSION} (Python {platform.python_version()})[/dim]")

    if not config.check_auth():
        from emata import handle_auth_setup # type: ignore
        handle_auth_setup(config)

    try:
        agent = Agent(config)
        
        # Hydrate context
        context_parts = []
        if not sys.stdin.isatty():
            piped = sys.stdin.read().strip()
            if piped: context_parts.append(f"=== PIPED INPUT ===\n{piped}\n===================")
        for f in args.file:
            if os.path.isfile(f):
                with open(f, "r", encoding="utf-8", errors="replace") as file:
                    context_parts.append(f"=== FILE: {f} ===\n{file.read()}\n===================")
        for d in args.dir:
            if os.path.isdir(d):
                ls = "\n".join([f"  {'[DIR]' if os.path.isdir(os.path.join(d,e)) else '[FILE]'} {e}" for e in os.listdir(d)])
                context_parts.append(f"=== DIR: {d} ===\n{ls}\n===================")
        if args.diff:
            try:
                res = subprocess.run(["git", "diff"], capture_output=True, text=True)
                if res.returncode == 0 and res.stdout.strip():
                    context_parts.append(f"=== GIT DIFF ===\n{res.stdout.strip()}\n===================")
            except: pass
        if context_parts:
            config.system_instructions += "\n\n" + "\n\n".join(context_parts)
            agent = Agent(config)

        print_header(config)
        display_help()
        
        B_MAGENTA = "\033[1;35m"
        PURPLE = "\033[95m"
        RESET = "\033[0m"

        while True:
            try:
                user_input = input(f"\n{B_MAGENTA}EMATA >{RESET} {PURPLE}").strip()
                print(RESET, end="") 
            except (KeyboardInterrupt, EOFError):
                print(RESET)
                break
            
            if not user_input: continue
            if user_input.lower() in [":exit", ":quit"]:
                console.print("[cyan]Exiting Emata. Session persisted in background.[/cyan]")
                break
            if user_input.lower() == ":help":
                display_help()
                continue
            if user_input.lower() == ":clear":
                agent.clear_history()
                console.print("[green]Session history cleared.[/green]")
                continue
            if user_input.lower() == ":report" or user_input.lower() == ":bug":
                handle_report_issue(config)
                continue
            if user_input.lower() == ":yolo":
                if input(f"Turn YOLO {'OFF' if config.yolo_mode else 'ON'}? (y/n): ").lower() == "y":
                    config.update_setting("EMATA_YOLO_MODE", not config.yolo_mode)
                    console.print(f"YOLO: {'ENABLED' if config.yolo_mode else 'DISABLED'}")
                continue
            if user_input.lower() == ":crazy":
                if input(f"Turn CRAZY {'OFF' if config.crazy_mode else 'ON'}? (y/n): ").lower() == "y":
                    config.update_setting("EMATA_CRAZY_MODE", not config.crazy_mode)
                    console.print(f"CRAZY: {'ENABLED' if config.crazy_mode else 'DISABLED'}")
                continue
            if user_input.lower() == ":model":
                if handle_model_selector(config, agent): agent = Agent(config)
                continue
            if user_input.lower() == ":keys":
                handle_key_manager(config)
                agent = Agent(config)
                continue
            if user_input.lower() == ":session":
                handle_session_manager(config, agent)
                continue
            
            query = user_input
            while query is not None:
                tool_results = {}
                awaiting_calls = None
                for chunk in agent.send_message_stream(query):
                    c_type = chunk.get("type")
                    if c_type == "thought": console.print(f"[dim italic]{chunk.get('content')}[/dim italic]", end="")
                    elif c_type == "text": console.print(chunk.get("content"), end="")
                    elif c_type == "tool_call":
                        console.print(f"\n[bold cyan]🔧 Tool: {chunk.get('name')}({chunk.get('args')})[/bold cyan]")
                    elif c_type == "awaiting_execution": awaiting_calls = chunk.get("calls")
                    elif c_type == "error": console.print(f"\n[bold red]Error: {chunk.get('content')}[/bold red]")
                
                query = None 
                if awaiting_calls:
                    exec_list = []
                    for call in awaiting_calls:
                        if config.crazy_mode or is_tool_safe(call.name, call.args):
                            exec_list.append(call)
                        else:
                            if input(f"\n[bold yellow]Allow {call.name}? [y/N]: [/bold yellow]").lower() == "y":
                                exec_list.append(call)
                            else:
                                tool_results[call.name] = "Error: Permission denied."
                    
                    for call in exec_list:
                        console.print(f"[dim]Executing {call.name}...[/dim]")
                        try:
                            res = TOOL_MAPPING[call.name](**call.args)
                        except Exception as e: res = f"Error: {e}"
                        tool_results[call.name] = res
                    
                    agent.inject_tool_results(tool_results)
                    query = ""
            console.print()
    except Exception as e: traceback.print_exc()

if __name__ == "__main__":
    main()
