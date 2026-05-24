#!/usr/bin/env python3
import sys, os, traceback, subprocess, shutil, platform, datetime
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

log("\n--- STARTING EMATA ---")

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
    sys.exit(1)

def handle_auth_setup(config):
    console.print("\n[bold cyan]🔐 Authentication Setup[/bold cyan]")
    console.print("1. [bold]API Key[/bold]\n2. [bold]Google Auth (ADC)[/bold]")
    
    choice = input("\nChoice (1/2): ").strip()
    log(f"User choice: {choice}")
    
    if choice == "1":
        key = input("Enter GEMINI_API_KEY: ").strip()
        if key: config.update_env_file("GEMINI_API_KEY", key)
        config.update_env_file("EMATA_AUTH_MODE", "api_key")
    
    elif choice == "2":
        # FIND THE ABSOLUTE PATH OF GCLOUD
        gcloud_abs_path = shutil.which("gcloud")
        log(f"shutil.which found gcloud at: {gcloud_abs_path}")
        
        if not gcloud_abs_path:
            log("GCLOUD NOT FOUND IN PATH")
            console.print("\n[bold red]❌ Error: Google Cloud SDK (gcloud) not found.[/bold red]")
            if platform.system() == "Darwin":
                console.print("To fix this, run: [green]brew install --cask google-cloud-sdk[/green]")
            input("\nPress Enter to return...")
            return

        adc_path = Path.home() / ".config/gcloud/application_default_credentials.json"
        if not adc_path.exists():
            console.print("[yellow]⚠️  Handshake required.[/yellow]")
            if input("Run 'gcloud login' now? (y/N): ").lower() == "y":
                log(f"Launching gcloud at: {gcloud_abs_path}")
                try:
                    # PASS THE ABSOLUTE PATH DIRECTLY
                    subprocess.run([gcloud_abs_path, "auth", "application-default", "login", "--no-browser"])
                    log("gcloud command finished successfully.")
                except Exception as e:
                    log(f"Execution failed: {e}")
                    console.print(f"[red]Execution error: {e}[/red]")
                    input("Press Enter...")
        
        if adc_path.exists():
            config.update_env_file("EMATA_AUTH_MODE", "google_auth")
            console.print("[green]✅ Google Auth ready.[/green]")
        else:
            console.print("[red]❌ Auth failed or cancelled.[/red]")
            input("\nPress Enter...")

def main():
    config = Config()
    if not config.check_auth():
        handle_auth_setup(config)
        if not config.check_auth():
            console.print("[bold red]Auth required.[/bold red]")
            input("Press Enter to exit...")
            sys.exit(1)
            
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
        log(f"Main Loop Error: {e}")
        console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        err = traceback.format_exc()
        log(f"FATAL:\n{err}")
        print(f"\nCRITICAL FAILURE:\n{err}")
        input("Press Enter to exit...")
