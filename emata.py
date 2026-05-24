#!/usr/bin/env python3
import sys, os, traceback, subprocess, shutil, platform, datetime, argparse
from pathlib import Path

# 1. IMMEDIATE LOGGING
os.makedirs(os.path.expanduser("~/.emata"), exist_ok=True)
BOOT_LOG = os.path.expanduser("~/.emata/boot_debug.log")

def log(msg):
    try:
        with open(BOOT_LOG, "a") as f:
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            f.write(f"[{ts}] {msg}\n")
    except: pass

log("--- EMATA STARTUP v1.0.13 ---")

try:
    from config import Config
    from agent import Agent
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    console = Console()
    log("Imports successful.")
except Exception as e:
    log(f"Import error: {e}")
    print(f"\nFATAL IMPORT ERROR: {e}")
    input("Press Enter to exit...")
    sys.exit(1)

def handle_auth_setup(config):
    console.print("\n[bold cyan]Authentication Setup[/bold cyan]")
    console.print("1. API Key\n2. Google Auth (ADC)")
    
    try:
        choice = input("\nChoice (1/2): ").strip()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]Setup cancelled.[/yellow]")
        return
    log(f"User choice: {choice}")
    
    if choice == "1":
        try:
            key = input("Enter GEMINI_API_KEY: ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Cancelled.[/yellow]")
            return
        if key: config.update_env_file("GEMINI_API_KEY", key)
        config.update_env_file("EMATA_AUTH_MODE", "api_key")
    
    elif choice == "2":
        try:
            log("Starting gcloud search...")
            gcloud_abs_path = shutil.which("gcloud")
            sys_platform = platform.system()
            
            if not gcloud_abs_path and sys_platform == "Darwin":
                log("Fallback search on Mac...")
                search_paths = [
                    "/usr/local/bin/gcloud",
                    "/opt/homebrew/bin/gcloud",
                    str(Path.home() / "google-cloud-sdk/bin/gcloud")
                ]
                for p in search_paths:
                    if os.path.exists(p):
                        gcloud_abs_path = p
                        break

            if not gcloud_abs_path:
                log("GCLOUD MISSING")
                console.print("\n[bold red]Error: Google Cloud SDK not found.[/bold red]")
                
                if sys_platform == "Darwin":
                    console.print("\nHow to install on Mac:")
                    console.print("Run: brew install --cask google-cloud-sdk")
                else:
                    console.print("\nHow to install:")
                    console.print("Visit: https://cloud.google.com/sdk/docs/install")
                
                try:
                    input("\nPress Enter to return to menu...")
                except (KeyboardInterrupt, EOFError):
                    pass
                return

            try:
                adc_path = Path.home() / ".config/gcloud/application_default_credentials.json"
                if not adc_path.exists():
                    log("Handshake required.")
                    console.print("[yellow]Handshake required.[/yellow]")
                    try:
                        run_login = input("Run 'gcloud login' now? (y/N): ").lower() == "y"
                    except (KeyboardInterrupt, EOFError):
                        run_login = False
                    if run_login:
                        subprocess.run([gcloud_abs_path, "auth", "application-default", "login", "--no-browser"])
                
                if adc_path.exists():
                    config.update_env_file("EMATA_AUTH_MODE", "google_auth")
                    console.print("[green]Google Auth ready.[/green]")
                else:
                    console.print("[red]Auth failed.[/red]")
                    try:
                        input("\nPress Enter...")
                    except (KeyboardInterrupt, EOFError):
                        pass
            except Exception as e:
                log(f"ADC Error: {e}")
                try:
                    input("Press Enter...")
                except (KeyboardInterrupt, EOFError):
                    pass
        except Exception as e:
            log(f"Search Error: {e}")
            try:
                input("Press Enter...")
            except (KeyboardInterrupt, EOFError):
                pass

def parse_args():
    parser = argparse.ArgumentParser(
        description="EMATA (Enduring Multi-Agent Terminal App) - A persistent, agentic local CLI coding companion."
    )
    parser.add_argument(
        "query",
        nargs="*",
        help="Optional single-shot query string to run the agent in direct mode (exits after completion)."
    )
    parser.add_argument(
        "-f", "--file",
        action="append",
        default=[],
        help="Code or text file to include as start context (can be specified multiple times)."
    )
    parser.add_argument(
        "-d", "--dir",
        action="append",
        default=[],
        help="Directory to inspect and load its structure/file list as start context (can be specified multiple times)."
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Load active workspace git diff changes programmatically into the starting context."
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        help="Override the default Gemini model for this session."
    )
    parser.add_argument(
        "--search",
        action="store_true",
        default=None,
        help="Explicitly enable Google Search grounding for real-time information."
    )
    parser.add_argument(
        "--no-search",
        action="store_true",
        default=None,
        help="Explicitly disable Google Search grounding to save context tokens."
    )
    parser.add_argument(
        "--yolo",
        action="store_true",
        default=None,
        help="Enable YOLO Mode (remove workspace guardrails for full command/file access)."
    )
    parser.add_argument(
        "--safe",
        action="store_true",
        default=None,
        help="Enable Safe Mode (activate workspace guardrails, deny commands out of folder)."
    )
    parser.add_argument(
        "--crazy",
        action="store_true",
        default=None,
        help="Enable Crazy Mode (bypass safety confirmation prompts for risky actions)."
    )
    return parser.parse_args()

def main():
    args = parse_args()
    config = Config()
    
    # 1. Apply command-line overrides to config
    if args.model:
        config.model = args.model
    if args.search is True:
        config.search_enabled = True
    elif args.no_search is True:
        config.search_enabled = False
    if args.yolo is True:
        config.yolo_mode = True
    elif args.safe is True:
        config.yolo_mode = False
    if args.crazy is True:
        config.crazy_mode = True

    # 2. Build custom starting context
    context_parts = []
    
    # 2a. Handle standard input piping (e.g. cat file.txt | emata "explain")
    if not sys.stdin.isatty():
        try:
            piped_data = sys.stdin.read().strip()
            if piped_data:
                context_parts.append(f"=== PIPED INPUT CONTENT ===\n{piped_data}\n===========================")
        except Exception as e:
            log(f"Error reading piped stdin: {e}")
            
    # 2b. Handle explicit file context hydration (-f / --file)
    for f_path in args.file:
        try:
            target = Path(f_path).resolve()
            if target.exists() and target.is_file():
                with open(target, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                context_parts.append(f"=== FILE CONTEXT: {f_path} ===\n{content}\n===========================")
            else:
                console.print(f"[yellow]Warning: File '{f_path}' not found or is not a file.[/yellow]")
        except Exception as e:
            log(f"Error loading file context {f_path}: {e}")
            
    # 2c. Handle directory context hydration (-d / --dir)
    for d_path in args.dir:
        try:
            target = Path(d_path).resolve()
            if target.exists() and target.is_dir():
                contents = []
                for entry in os.scandir(target):
                    entry_type = "DIR" if entry.is_dir() else "FILE"
                    size_str = f" ({entry.stat().st_size} bytes)" if entry.is_file() else ""
                    contents.append(f"  [{entry_type}] {entry.name}{size_str}")
                dir_list = "\n".join(contents)
                context_parts.append(f"=== DIRECTORY CONTEXT: {d_path} ===\n{dir_list}\n===========================")
            else:
                console.print(f"[yellow]Warning: Directory '{d_path}' not found or is not a dir.[/yellow]")
        except Exception as e:
            log(f"Error loading directory context {d_path}: {e}")

    # 2d. Handle git diff awareness (--diff)
    if args.diff:
        try:
            res = subprocess.run(
                ["git", "diff"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if res.returncode == 0 and res.stdout.strip():
                context_parts.append(f"=== GIT DIFF CONTEXT (Active Changes) ===\n{res.stdout.strip()}\n===========================")
            else:
                log("Git diff returned empty or not a git repo")
        except Exception as e:
            log(f"Error reading git diff: {e}")

    joined_context = "\n\n".join(context_parts)
    if joined_context:
        config.system_instructions = (config.system_instructions or "") + "\n\n" + joined_context

    # 3. Check for authentication before starting execution
    while not config.check_auth():
        handle_auth_setup(config)
        if not config.check_auth():
            console.print("\n[yellow]Auth not configured.[/yellow]")
            try:
                choice = input("Retry? (Y/n) or 'exit': ").lower().strip()
            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]Exiting...[/yellow]")
                sys.exit(0)
            if choice == "exit" or choice == "n":
                sys.exit(0)

    # 4. Handle Single-Shot (Piping/Command Arguments) Execution Mode
    query_str = " ".join(args.query).strip()
    is_single_shot = bool(query_str) or not sys.stdin.isatty()
    
    if is_single_shot:
        if not query_str:
            query_str = "Please analyze the provided piped input content."
            
        try:
            agent = Agent(config)
            print("Working...", end="\r")
            for chunk in agent.send_message_stream(query_str):
                if "text" in chunk: console.print(chunk["text"], end="")
            console.print()
            sys.exit(0)
        except Exception as e:
            console.print(f"\n[bold red]Error executing query: {e}[/bold red]")
            sys.exit(1)

    # 5. Run Interactive Shell (TMUX detaches here)
    try:
        agent = Agent(config)
        console.print(Panel(Text("🛰️ EMATA Online", style="bold cyan"), border_style="cyan"))
        while True:
            try:
                user_input = input("\ngagent > ").strip()
            except KeyboardInterrupt:
                print()
                continue
            except EOFError:
                console.print("\n[yellow]Exiting...[/yellow]")
                break
                
            if user_input.lower() in [":exit", ":quit"]: break
            if not user_input: continue
            if user_input.lower() == ":auth":
                handle_auth_setup(config)
                agent = Agent(config)
                continue
            if user_input.lower() == ":upgrade":
                console.print("[bold cyan]🔄 Checking for updates...[/bold cyan]")
                try:
                    source_dir = os.path.dirname(os.path.abspath(__file__))
                    res = subprocess.run(
                        ["git", "pull"],
                        cwd=source_dir,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if res.returncode == 0:
                        console.print(f"[green]✓ Codebase successfully pulled from remote repository![/green]")
                        if "Already up to date." in res.stdout:
                            console.print("[dim]Already up to date.[/dim]")
                        else:
                            console.print("[yellow]Reloading EMATA...[/yellow]")
                            venv_pip = os.path.join(source_dir, ".venv", "bin", "pip")
                            if os.path.exists(venv_pip):
                                console.print("[dim]Updating virtual environment dependencies...[/dim]")
                                subprocess.run(
                                    [venv_pip, "install", "--quiet", "-r", os.path.join(source_dir, "requirements.txt")],
                                    cwd=source_dir
                                )
                                console.print("[green]✓ Virtual environment updated![/green]")
                            console.print("[bold green]✓ Upgrade complete! Please restart EMATA to load all updates.[/bold green]")
                    else:
                        console.print(f"[red]Error during upgrade pull: {res.stderr.strip()}[/red]")
                except Exception as e:
                    console.print(f"[red]Failed to execute self-upgrade: {e}[/red]")
                continue
            
            print("Working...", end="\r")
            try:
                for chunk in agent.send_message_stream(user_input):
                    if "text" in chunk: console.print(chunk["text"], end="")
                console.print()
            except KeyboardInterrupt:
                console.print("\n[yellow]Operation interrupted by user.[/yellow]")
            except Exception as e:
                console.print(f"\n[red]Error executing request: {e}[/red]")
    except Exception as e:
        log(f"Loop Error: {e}")
        traceback.print_exc()
        try:
            input("Press Enter to exit...")
        except (KeyboardInterrupt, EOFError):
            pass

if __name__ == "__main__":
    try:
        main()
    except Exception:
        err = traceback.format_exc()
        log(f"FATAL: {err}")
        print(f"\nCRITICAL FAILURE: {err}")
        try:
            input("Press Enter to exit...")
        except (KeyboardInterrupt, EOFError):
            pass
