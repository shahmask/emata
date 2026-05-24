#!/usr/bin/env python3
import sys, os, traceback, subprocess, shutil, webbrowser, urllib.parse, platform, datetime
from pathlib import Path

# 1. LOGGING & INITIALIZATION
os.makedirs(os.path.expanduser("~/.emata"), exist_ok=True)
BOOT_LOG = os.path.expanduser("~/.emata/boot_debug.log")

def log(msg):
    try:
        with open(BOOT_LOG, "a") as f:
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            f.write(f"[{ts}] {msg}\n")
    except: pass

try:
    from config import Config
    from agent import Agent
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    console = Console()
except Exception as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def handle_auth_setup(config):
    console.print("\n[bold cyan]🔐 Authentication Setup[/bold cyan]")
    console.print("1. [bold]API Key[/bold] (Recommended for local use)\n2. [bold]Google Auth (ADC)[/bold] (Enterprise/Headless)")
    
    choice = input("\nChoice (1/2): ").strip()
    
    if choice == "1":
        key = input("Enter GEMINI_API_KEY: ").strip()
        if key: config.update_env_file("GEMINI_API_KEY", key)
        config.update_env_file("EMATA_AUTH_MODE", "api_key")
        console.print("[green]✓ API Key configured.[/green]")
        
    elif choice == "2":
        gcloud_path = shutil.which("gcloud")
        if not gcloud_path:
            console.print("[bold red]❌ Error: 'gcloud' command not found.[/bold red]")
            console.print("[dim]Please install the Google Cloud SDK first: https://cloud.google.com/sdk/docs/install[/dim]")
            input("\nPress Enter to return...")
            return

        adc_path = Path.home() / ".config/gcloud/application_default_credentials.json"
        if not adc_path.exists():
            console.print("[yellow]⚠️  Handshake required (Application Default Credentials missing).[/yellow]")
            if input("Run 'gcloud login' now? (y/N): ").lower() == "y":
                console.print("\n[bold yellow]🚀 Launching gcloud...[/bold yellow]")
                console.print("[dim]Follow the instructions in your browser and check all boxes.[/dim]\n")
                try:
                    subprocess.run(["gcloud", "auth", "application-default", "login", "--no-browser"])
                except Exception as e:
                    console.print(f"[red]Execution error: {e}[/red]")
        
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
            console.print("[bold red]Authentication is required to continue.[/bold red]")
            input("Press Enter to exit...")
            sys.exit(1)
            
    try:
        agent = Agent(config)
    except Exception as e:
        console.print(f"[bold red]AI Engine Error:[/bold red] {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)

    console.print(Panel(Text("🛰️ EMATA Online", style="bold cyan"), border_style="cyan"))
    
    while True:
        try:
            user_input = input("\ngagent > ").strip()
            if user_input.lower() in [":exit", ":quit"]: break
            if not user_input: continue
            if user_input.lower() == ":auth":
                handle_auth_setup(config)
                agent = Agent(config)
                continue
            
            # Message Loop
            print("Working...", end="\r")
            for chunk in agent.send_message_stream(user_input):
                if "text" in chunk:
                    console.print(chunk["text"], end="")
            console.print()
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Use :exit to quit.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        err = traceback.format_exc()
        log(f"FATAL:\n{err}")
        console.print(f"\n[bold red]CRITICAL FAILURE[/bold red]\n{err}")
        input("\nPress Enter to exit...")
