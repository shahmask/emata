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
    print(f"Import Error: {e}")
    sys.exit(1)

def handle_auth_setup(config):
    console.print("\n[bold cyan]🔐 Authentication Setup[/bold cyan]")
    console.print("1. [bold]API Key[/bold]\n2. [bold]Google Auth (ADC)[/bold]")
    
    choice = input("\nChoice (1/2): ").strip()
    log(f"User selected choice: {choice}")
    
    if choice == "1":
        key = input("Enter GEMINI_API_KEY: ").strip()
        if key: config.update_env_file("GEMINI_API_KEY", key)
        config.update_env_file("EMATA_AUTH_MODE", "api_key")
        console.print("[green]✓ API Key configured.[/green]")
        
    elif choice == "2":
        log("Step 1: Checking for gcloud SDK...")
        gcloud_path = shutil.which("gcloud")
        log(f"shutil.which returned: {gcloud_path}")
        
        if not gcloud_path:
            log("Step 1 Failed: gcloud not found.")
            console.print("\n[bold red]❌ Error: Google Cloud SDK (gcloud) not found.[/bold red]")
            if platform.system() == "Darwin":
                console.print("To install on macOS: [green]brew install --cask google-cloud-sdk[/green]")
            input("\nPress Enter to return...")
            return

        log("Step 2: Checking for ADC file...")
        adc_path = Path.home() / ".config/gcloud/application_default_credentials.json"
        
        if not adc_path.exists():
            log("Step 3: ADC missing, prompting for handshake.")
            console.print("[yellow]⚠️  Handshake required.[/yellow]")
            run_it = input("Run 'gcloud login' now? (y/N): ").lower()
            if run_it == "y":
                log("Step 4: Executing gcloud login...")
                console.print("\n[bold yellow]🚀 Launching gcloud...[/bold yellow]")
                
                # USE os.system AS FALLBACK - Often more stable on macOS for interactive CLI
                try:
                    log(f"Running command: {gcloud_path} auth application-default login --no-browser")
                    # We use absolute path to be 100% sure
                    os.system(f"'{gcloud_path}' auth application-default login --no-browser")
                    log("gcloud command finished.")
                except Exception as e:
                    log(f"os.system error: {e}")
                    console.print(f"[red]Error: {e}[/red]")
            else:
                log("User declined handshake.")
        
        log("Step 5: Re-checking ADC file...")
        if adc_path.exists():
            log("Success! ADC found.")
            config.update_env_file("EMATA_AUTH_MODE", "google_auth")
            console.print("[green]✅ Google Auth ready.[/green]")
        else:
            log("Final Check: ADC still missing.")
            console.print("[red]❌ Auth failed or was cancelled.[/red]")
            input("\nPress Enter to return to menu...")

def main():
    log("Entering main()")
    config = Config()
    
    if not config.check_auth():
        log("No auth detected, opening setup.")
        handle_auth_setup(config)
        if not config.check_auth():
            log("Auth check failed after setup. Exiting.")
            console.print("[bold red]Authentication is required to continue.[/bold red]")
            input("Press Enter to exit...")
            sys.exit(1)
            
    log("Initializing Agent...")
    try:
        agent = Agent(config)
    except Exception as e:
        log(f"Agent Init Error: {e}")
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
            
            # Simple message loop
            print("Working...", end="\r")
            for chunk in agent.send_message_stream(user_input):
                if "text" in chunk:
                    console.print(chunk["text"], end="")
            console.print()
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Use :exit to quit.[/yellow]")
        except Exception as e:
            log(f"Loop error: {e}")
            console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        err = traceback.format_exc()
        log(f"FATAL CRASH:\n{err}")
        console.print(f"\n[bold red]CRITICAL FAILURE[/bold red]\n{err}")
        input("\nPress Enter to exit...")
