#!/usr/bin/env python3
import sys, os, traceback

# 1. IMMEDIATE LOGGING SETUP
os.makedirs(os.path.expanduser("~/.emata"), exist_ok=True)
BOOT_LOG = os.path.expanduser("~/.emata/boot_debug.log")

def log(msg):
    with open(BOOT_LOG, "a") as f:
        f.write(f"{msg}\n")

log("\n--- NEW BOOT ATTEMPT ---")

try:
    log("Importing base modules...")
    import argparse
    import subprocess
    from pathlib import Path
    
    log("Importing project modules...")
    from config import Config
    from agent import Agent
    from logging_config import setup_logging
    
    log("Importing UI modules...")
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    import shutil
    
    log("Initializing Rich...")
    console = Console()
    
    def handle_auth_setup(config):
        log("Inside handle_auth_setup")
        console.print("\n[bold cyan]🔐 Auth Setup[/bold cyan]")
        console.print("1. API Key\n2. Google Auth")
        
        choice = input("\nChoice: ").strip()
        log(f"User choice: {choice}")
        
        if choice == "2":
            log("Running gcloud...")
            # DIRECT CALL - No bells or whistles
            cmd = ["gcloud", "auth", "application-default", "login", "--no-browser"]
            log(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd)
            log(f"gcloud exit code: {result.returncode}")
            
            # Re-check
            adc = Path.home() / ".config/gcloud/application_default_credentials.json"
            if adc.exists():
                log("ADC found!")
                config.update_env_file("EMATA_AUTH_MODE", "google_auth")
            else:
                log("ADC NOT found after run.")

    def main():
        log("Inside main()")
        config = Config()
        
        if not config.check_auth():
            log("Auth missing, calling setup")
            handle_auth_setup(config)
            
        log("Initializing Agent...")
        agent = Agent(config)
        log("Agent ready. Starting loop.")
        
        console.print("[bold green]EMATA Live.[/bold green]")
        while True:
            cmd = input("emata > ")
            if cmd == ":exit": break
            if cmd == ":auth": handle_auth_setup(config)

    if __name__ == "__main__":
        main()

except Exception as e:
    err = traceback.format_exc()
    log(f"FATAL BOOT ERROR:\n{err}")
    print(f"\n\n!!! CRITICAL BOOT FAILURE !!!\n{err}")
    input("\nPress Enter to close this window...")
