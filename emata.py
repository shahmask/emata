#!/usr/bin/env python3
import sys
import argparse
import subprocess
import os
from pathlib import Path
try:
    import readline
except ImportError:
    pass
from config import Config
from agent import Agent
from logging_config import setup_logging
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
import webbrowser
import urllib.parse
import platform
import shutil
import datetime
import traceback

console = Console()
config_instance = None
DEBUG_LOG = os.path.expanduser("~/.emata/debug_auth.log")

def log_debug(msg):
    try:
        os.makedirs(os.path.dirname(DEBUG_LOG), exist_ok=True)
        with open(DEBUG_LOG, "a") as f:
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass

def parse_args():
    parser = argparse.ArgumentParser(
        description="EMATA - Enduring Multi-Agent Terminal App."
    )
    parser.add_argument("-m", "--model", type=str)
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()

def show_welcome_banner(config: Config, debug: bool = False):
    banner_text = Text()
    banner_text.append("🚀 EMATA Online\n", style="bold cyan")
    banner_text.append(f"Model: {config.model}", style="green")
    console.print(Panel(banner_text, border_style="cyan"))

def get_tmux_mouse_state():
    if not os.environ.get("TMUX"): return None
    try:
        res = subprocess.run(["tmux", "show-options", "-g", "mouse"], capture_output=True, text=True)
        return "on" if "mouse on" in res.stdout else "off"
    except Exception: return None

def set_tmux_mouse(state: str):
    if not os.environ.get("TMUX"): return
    try: subprocess.run(["tmux", "set", "-g", "mouse", state], capture_output=True)
    except Exception: pass

def handle_auth_setup(config: Config):
    log_debug("--- Starting handle_auth_setup ---")
    try:
        console.print("\n[bold cyan]🔐 Authentication Setup:[/bold cyan]")
        console.print(f"  Current Mode: [yellow]{config.auth_mode}[/yellow]")
        console.print("-" * 30)
        console.print("  1. [bold]API Key[/bold]")
        console.print("  2. [bold]Google Auth (ADC)[/bold]")
        
        choice = input("\nSelect auth mode (1/2 or Enter to cancel): ").strip()
        log_debug(f"Choice: {choice}")

        if choice == "1":
            key = input("Enter GEMINI_API_KEY: ").strip()
            if key: config.update_env_file("GEMINI_API_KEY", key)
            config.update_env_file("EMATA_AUTH_MODE", "api_key")
        elif choice == "2":
            log_debug("Checking gcloud...")
            has_gcloud = shutil.which("gcloud") is not None
            if not has_gcloud:
                console.print("[red]gcloud not found.[/red]")
                input("Press Enter...")
                return
            
            adc_path = Path.home() / ".config/gcloud/application_default_credentials.json"
            if not adc_path.exists():
                console.print("[yellow]Handshake required![/yellow]")
                run_it = input("Run gcloud login now? (y/N): ").lower()
                if run_it == "y":
                    log_debug("Running gcloud...")
                    scopes = "https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/userinfo.email,openid"
                    subprocess.run(["gcloud", "auth", "application-default", "login", "--no-browser", f"--scopes={scopes}"])
                    if adc_path.exists():
                        config.update_env_file("EMATA_AUTH_MODE", "google_auth")
            else:
                config.update_env_file("EMATA_AUTH_MODE", "google_auth")
    except Exception as e:
        log_debug(f"Error in auth setup: {e}\n{traceback.format_exc()}")
        console.print(f"[red]Error: {e}[/red]")
        input("Press Enter to continue...")

def handle_report_issue(config: Config):
    emata_version = "v1.0.11"
    issue_body = f"Version: {emata_version}\nOS: {platform.system()}\nModel: {config.model}"
    url = f"https://github.com/shahmask/emata/issues/new?body={urllib.parse.quote(issue_body)}"
    console.print(f"\n[cyan]Issue URL: {url}[/cyan]")
    if input("Open browser? (y/N): ").lower() == "y": webbrowser.open(url)

def main():
    try:
        args = parse_args()
        config = Config()
        if args.model: config.model = args.model
        
        if not config.check_auth():
            handle_auth_setup(config)
            if not config.check_auth():
                console.print("[red]Auth required.[/red]")
                input("Press Enter to exit...")
                sys.exit(1)
        
        agent = Agent(config)
        show_welcome_banner(config)
        
        while True:
            try:
                user_input = input("gagent > ").strip()
                if user_input.lower() in [":exit", ":quit"]: break
                if user_input.lower() == ":auth":
                    handle_auth_setup(config)
                    agent = Agent(config)
                    continue
                if user_input.lower() == ":report":
                    handle_report_issue(config)
                    continue
                
                # Streaming message logic
                for chunk in agent.send_message_stream(user_input):
                    if "text" in chunk: console.print(chunk["text"], end="")
                console.print()
            except KeyboardInterrupt:
                console.print("\n[yellow]Use :exit to quit.[/yellow]")
            except Exception as e:
                console.print(f"[red]Loop Error: {e}[/red]")
                input("Press Enter...")
    except Exception as e:
        log_debug(f"Main Error: {e}\n{traceback.format_exc()}")
        console.print(f"[bold red]Startup Error: {e}[/bold red]")
        console.print(traceback.format_exc())
        input("\nFATAL. Press Enter to exit...")

if __name__ == "__main__":
    main()
