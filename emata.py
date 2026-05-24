#!/usr/bin/env python3
import sys, os, traceback, subprocess, shutil, platform, datetime
from pathlib import Path

# 1. IMMEDIATE LOGGING
os.makedirs(os.path.expanduser("~/.emata"), exist_ok=True)
BOOT_LOG = os.path.expanduser("~/.emata/boot_debug.log")

def log(msg):
    try:
        # Simple print for immediate feedback
        print(f"> {msg}")
        with open(BOOT_LOG, "a") as f:
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            f.write(f"[{ts}] {msg}\n")
    except: pass

log("--- EMATA STARTUP v1.0.12 ---")

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
    
    choice = input("\nChoice (1/2): ").strip()
    log(f"User choice: {choice}")
    
    if choice == "1":
        key = input("Enter GEMINI_API_KEY: ").strip()
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
                
                input("\nPress Enter to return to menu...")
                return

            try:
                adc_path = Path.home() / ".config/gcloud/application_default_credentials.json"
                if not adc_path.exists():
                    log("Handshake required.")
                    console.print("[yellow]Handshake required.[/yellow]")
                    if input("Run 'gcloud login' now? (y/N): ").lower() == "y":
                        subprocess.run([gcloud_abs_path, "auth", "application-default", "login", "--no-browser"])
                
                if adc_path.exists():
                    config.update_env_file("EMATA_AUTH_MODE", "google_auth")
                    console.print("[green]Google Auth ready.[/green]")
                else:
                    console.print("[red]Auth failed.[/red]")
                    input("\nPress Enter...")
            except Exception as e:
                log(f"ADC Error: {e}")
                input("Press Enter...")
        except Exception as e:
            log(f"Search Error: {e}")
            input("Press Enter...")

def main():
    config = Config()
    while not config.check_auth():
        handle_auth_setup(config)
        if not config.check_auth():
            console.print("\n[yellow]Auth not configured.[/yellow]")
            choice = input("Retry? (Y/n) or 'exit': ").lower().strip()
            if choice == "exit" or choice == "n":
                sys.exit(0)

    try:
        agent = Agent(config)
        console.print(Panel(Text("🛰️ EMATA Online", style="bold cyan"), border_style="cyan"))
        while True:
            user_input = input("\ngagent > ").strip()
            if user_input.lower() in [":exit", ":quit"]: break
            if not user_input: continue
            if user_input.lower() == ":auth":
                handle_auth_setup(config)
                agent = Agent(config)
                continue
            
            print("Working...", end="\r")
            for chunk in agent.send_message_stream(user_input):
                if "text" in chunk: console.print(chunk["text"], end="")
            console.print()
    except Exception as e:
        log(f"Loop Error: {e}")
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        err = traceback.format_exc()
        log(f"FATAL: {err}")
        print(f"\nCRITICAL FAILURE: {err}")
        input("Press Enter to exit...")
