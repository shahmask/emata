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
log(f"System PATH: {os.environ.get('PATH')}")

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
    print(f"\n[bold red]FATAL IMPORT ERROR:[/bold red] {e}")
    print("Ensure you are running inside the virtual environment.")
    input("Press Enter to exit...")
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
    
    elif choice == "2":
        try:
            log("User chose Google Auth. Starting path search...")
            # FIND THE ABSOLUTE PATH OF GCLOUD
            gcloud_abs_path = shutil.which("gcloud")
            log(f"shutil.which found gcloud at: {gcloud_abs_path}")
            
            # SEARCH COMMON MAC PATHS IF NOT FOUND
            sys_platform = platform.system()
            log(f"Detected Platform: {sys_platform}")
            
            if not gcloud_abs_path and sys_platform == "Darwin":
                log("Searching common Mac paths...")
                search_paths = [
                    "/usr/local/bin/gcloud",
                    "/opt/homebrew/bin/gcloud",
                    str(Path.home() / "google-cloud-sdk/bin/gcloud")
                ]
                for p in search_paths:
                    if os.path.exists(p):
                        gcloud_abs_path = p
                        log(f"Found gcloud in fallback search: {p}")
                        break

            if not gcloud_abs_path:
                log("GCLOUD NOT FOUND AFTER EXHAUSTIVE SEARCH")
                console.print("\n[bold red]❌ Error: Google Cloud SDK (gcloud) not found.[/bold red]")
                
                if sys_platform == "Darwin":
                    console.print("\n[bold cyan]How to install on Mac:[/bold cyan]")
                    console.print("Run: [green]brew install --cask google-cloud-sdk[/green]")
                else:
                    console.print("\n[bold cyan]How to install:[/bold cyan]")
                    console.print("1. Visit: [blue]https://cloud.google.com/sdk/docs/install[/blue]")
                    console.print("2. Follow the instructions for your OS.")
                    console.print("3. Restart your terminal after installation.")
                
                input("\nPress Enter to return to menu...")
                return

            # IF WE REACH HERE, gcloud_abs_path IS VALID
            try:
                adc_path = Path.home() / ".config/gcloud/application_default_credentials.json"
                log(f"Checking for ADC file at: {adc_path}")
                if not adc_path.exists():
                    console.print("[yellow]⚠️  Handshake required.[/yellow]")
                    if input("Run 'gcloud login' now? (y/N): ").lower() == "y":
                        log(f"Launching gcloud at: {gcloud_abs_path}")
                        try:
                            # USE THE ABSOLUTE PATH WE FOUND
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
        except Exception as e:
            log(f"Error during ADC check/login: {e}")
            console.print(f"[red]Authentication error: {e}[/red]")
            input("Press Enter...")

def main():
    config = Config()
    
    # LOOP UNTIL AUTH IS VALID OR USER EXITS
    while not config.check_auth():
        handle_auth_setup(config)
        if not config.check_auth():
            console.print("\n[yellow]⚠️  Authentication is still not configured.[/yellow]")
            choice = input("Retry setup? (Y/n) or type 'exit': ").lower().strip()
            if choice == "exit" or choice == "n":
                console.print("[red]Exiting...[/red]")
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
        log(f"Main Loop Error: {e}")
        console.print(f"\n[bold red]FATAL ERROR:[/bold red] {e}")
        traceback.print_exc()
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        err = traceback.format_exc()
        log(f"FATAL:\n{err}")
        print(f"\nCRITICAL FAILURE:\n{err}")
        input("Press Enter to exit...")
