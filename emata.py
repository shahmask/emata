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

console = Console()

def parse_args():
    parser = argparse.ArgumentParser(
        description="EMATA - Enduring Multi-Agent Terminal App. A local, interactive terminal AI agent."
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        help="Override the default model (e.g. gemini-2.0-flash, gemini-3.5-flash)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging to ~/.emata/emata.log"
    )
    return parser.parse_args()

def show_welcome_banner(config: Config, debug: bool = False):
    import os
    banner_text = Text()
    banner_text.append("🚀 EMATA Online (Enduring Multi-Agent Terminal App)\n", style="bold cyan")
    banner_text.append(f"Model: {config.model}", style="green")
    
    if config.system_instructions:
        banner_text.append(" | ", style="white")
        banner_text.append("⚙️ Local instructions loaded", style="bold yellow")
        
    if debug:
        banner_text.append(" | ", style="white")
        banner_text.append("🐞 Debug mode", style="bold red")

    session_id = os.environ.get("TMUX_SESSION_NAME")
    if session_id:
        banner_text.append("\nSession ID: ", style="bold magenta")
        banner_text.append(session_id, style="bold cyan")
        
    banner_text.append("\n\nType your request. Commands: :clear (reset chat), :session (list work), :exit", style="dim white")
    banner_text.append("\n[dim]💡 Tip: Hold [bold]Shift[/bold] while dragging with your mouse to copy text instantly.[/dim]")
    
    panel = Panel(banner_text, border_style="cyan", title="[bold cyan]EMATA Engine[/bold cyan]")
    console.print(panel)

def on_tool_call(name: str, args: dict):
    # Print the tool execution with styling
    args_str = ", ".join(f"{k}={repr(v)}" for k, v in args.items())
    console.print(f"\n[bold yellow]🛠️  Tool Call:[/bold yellow] [cyan]{name}({args_str})[/cyan]")

def prompt_create_gemini_file(config: Config):
    """Checks if gemini.md or .gemini exists; prompts to create gemini.md if not."""
    cwd = Path.cwd()
    gemini_file_md = cwd / "gemini.md"
    gemini_file_dot = cwd / ".gemini"
    
    if not gemini_file_md.exists() and not gemini_file_dot.exists():
        console.print("[yellow]⚠️  No gemini.md or .gemini file found in this directory.[/yellow]")
        try:
            create_choice = console.input("[bold cyan]Would you like to create a gemini.md file with custom instructions? (y/N): [/bold cyan]").strip().lower()
            if create_choice in ("y", "yes"):
                console.print("[cyan]Enter your instructions (press Enter on an empty line to finish):[/cyan]")
                lines = []
                while True:
                    line = input()
                    if line == "":
                        break
                    lines.append(line)
                
                instructions = "\n".join(lines).strip()
                if instructions:
                    try:
                        with open(gemini_file_md, "w", encoding="utf-8") as f:
                            f.write(instructions + "\n")
                        console.print(f"[bold green]✓ Successfully created gemini.md with your instructions![/bold green]\n")
                        config.system_instructions = instructions
                    except Exception as e:
                        console.print(f"[bold red]Error creating gemini.md: {e}[/bold red]\n")
                else:
                    console.print("[yellow]No instructions entered. gemini.md was not created.[/yellow]\n")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Skipped gemini.md creation.[/yellow]\n")

def get_tmux_mouse_state():
    if not os.environ.get("TMUX"):
        return None
    try:
        res = subprocess.run(["tmux", "show-options", "-g", "mouse"], capture_output=True, text=True, check=True)
        output = res.stdout.strip()
        if "mouse off" in output:
            return "off"
        elif "mouse on" in output:
            return "on"
    except Exception:
        pass
    return None

def set_tmux_mouse(state: str):
    if not os.environ.get("TMUX"):
        return
    try:
        subprocess.run(["tmux", "set", "-g", "mouse", state], capture_output=True, check=True)
    except Exception:
        pass

def main():
    args = parse_args()
    
    # Initialize logging
    logger = setup_logging(debug=args.debug)
    logger.info("Starting gagent session")

    # Initialize configuration
    config = Config()
    
    # CLI override for model
    if args.model:
        config.model = args.model
        
    # Check for authentication
    if not config.check_auth():
        logger.error("Authentication Error: GEMINI_API_KEY not set")
        console.print(Panel(
            "[bold red]Authentication Error:[/bold red] GEMINI_API_KEY environment variable is not set.\n\n"
            "Please set the API key in your environment:\n"
            "  [green]export GEMINI_API_KEY=\"your-api-key\"[/green]\n\n"
            "Or create a [yellow].env[/yellow] file in this directory containing:\n"
            "  [green]GEMINI_API_KEY=your-api-key[/green]",
            border_style="red",
            title="[bold red]Missing API Key[/bold red]"
        ))
        sys.exit(1)
        
    # Prompt to create gemini.md if missing
    prompt_create_gemini_file(config)
    
    # Initialize the agent
    try:
        agent = Agent(config)
    except Exception as e:
        logger.exception("Initialization Error: Could not start agent")
        console.print(f"[bold red]Initialization Error:[/bold red] Could not start agent: {e}")
        sys.exit(1)

    show_welcome_banner(config, debug=args.debug)

    if agent.history:
        console.print("[bold cyan]✨ Previous session details loaded. (Type ':clear' to start fresh)[/bold cyan]\n")

    # Enable tmux mouse mode automatically for smooth scrolling within gagent
    original_mouse_state = get_tmux_mouse_state()

    if original_mouse_state is not None:
        set_tmux_mouse("on")

    try:
        # Main interactive loop
        while True:
            try:
                # Elegant prompt indicator using raw ANSI escapes wrapped in \001 and \002
                # to let readline compute prompt width correctly and allow backspacing over wrapped lines.
                prompt = "\001\x1b[1;36m\002gagent > \001\x1b[0m\002"
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                    
                # Handle special console commands
                if user_input.lower() in [":exit", ":quit"]:
                    agent.history.clear()
                    agent.clear_session()
                    console.print("[cyan]Exiting EMATA and clearing session. Goodbye![/cyan]")
                    break
                    
                elif user_input.lower() == ":clear":
                    agent.history.clear()
                    agent.clear_session()
                    console.print("[bold green]✓ Conversation history cleared.[/bold green]")
                    continue
                    
                elif user_input.lower() == ":config":
                    console.print(Panel(
                        f"[bold cyan]Active Model:[/bold cyan] [green]{config.model}[/green]\n"
                        f"[bold cyan]Auth Mode:[/bold cyan] [green]{config.auth_mode}[/green]\n"
                        f"[bold cyan]Local Rules:[/bold cyan] [green]{'Loaded' if config.system_instructions else 'None'}[/green]\n"
                        f"[bold cyan]Session ID: [/bold cyan] [magenta]{os.environ.get('TMUX_SESSION_NAME', 'Standalone')}[/magenta]",
                        title="[bold cyan]Configuration[/bold cyan]"
                    ))
                    continue
                    
                elif user_input.lower() in [":change-model", ":chante-model"]:
                    console.print("[yellow]Fetching available models...[/yellow]")
                    models = agent.list_available_models()
                    # Filter for generative models
                    gen_models = [m for m in models if "gemini" in m.lower()]
                    
                    if not gen_models:
                        console.print("[red]No Gemini models found or error fetching models.[/red]")
                    else:
                        console.print("\n[bold cyan]Available Models:[/bold cyan]")
                        for i, m in enumerate(gen_models, 1):
                            console.print(f"  {i}. [yellow]{m}[/yellow]")
                        
                        try:
                            choice = console.input("\n[bold cyan]Select a model number to set as default (or Enter to cancel): [/bold cyan]").strip()
                            if choice.isdigit() and 1 <= int(choice) <= len(gen_models):
                                selected = gen_models[int(choice)-1]
                                config.update_env_file("GEMINI_MODEL", selected)
                                agent.config.model = selected
                                console.print(f"[bold green]✓ Default model updated to: {selected}[/bold green]")
                        except (KeyboardInterrupt, EOFError):
                            console.print("\n[yellow]Cancelled model change.[/yellow]")
                    continue

                elif user_input.lower() == ":auth":
                    console.print("\n[bold cyan]🔐 Authentication Setup:[/bold cyan]")
                    console.print(f"  Current Mode: [yellow]{config.auth_mode}[/yellow]")
                    console.print("-" * 30)
                    console.print("  1. [bold]API Key[/bold] (Standard, works everywhere)")
                    console.print("  2. [bold]Google Auth[/bold] (Enterprise, uses your gcloud session)")
                    
                    try:
                        choice = console.input("\n[bold cyan]Select auth mode (1/2 or Enter to cancel): [/bold cyan]").strip()
                        if choice == "1":
                            new_key = console.input("[bold cyan]Enter your GEMINI_API_KEY (leave blank to keep current): [/bold cyan]").strip()
                            if new_key:
                                config.update_env_file("GEMINI_API_KEY", new_key)
                            config.update_env_file("EMATA_AUTH_MODE", "api_key")
                            console.print("[bold green]✓ Auth mode set to API Key.[/bold green]")
                        
                        elif choice == "2":
                            # Perform diagnostics for Google Auth
                            console.print("\n[bold yellow]🔍 Checking Google Cloud environment...[/bold yellow]")
                            
                            has_gcloud = subprocess.run(["which", "gcloud"], capture_output=True).returncode == 0
                            adc_path = Path.home() / ".config/gcloud/application_default_credentials.json"
                            has_adc = adc_path.exists()
                            
                            if not has_gcloud:
                                console.print("[red]❌ Error: 'gcloud' CLI not found.[/red]")
                                console.print("[dim]Please install it first: https://cloud.google.com/sdk/docs/install[/dim]")
                            elif not has_adc:
                                console.print("[yellow]⚠️  Handshake required![/yellow]")
                                console.print("Your gcloud session is active, but Application Default Credentials (ADC) are missing.")
                                console.print("\n[bold cyan]To fix this, run this command in your terminal:[/bold cyan]")
                                console.print(Panel("[white]gcloud auth application-default login[/white]", border_style="green"))
                                
                                try:
                                    run_it = console.input("\n[bold cyan]Would you like to run this command now? (y/N): [/bold cyan]").strip().lower()
                                    if run_it == 'y':
                                        console.print("\n[bold yellow]🚀 Launching gcloud auth...[/bold yellow]")
                                        console.print("[bold red]⚠️  IMPORTANT:[/bold red] In your browser, you [bold]MUST check all the checkboxes[/bold]")
                                        console.print("for the permissions listed (e.g., 'See, edit, configure...') or gcloud will crash.")
                                        
                                        # Use a more explicit scope list to help prevent the 'Scope has changed' error
                                        scopes = "https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/userinfo.email,openid"
                                        subprocess.run(["gcloud", "auth", "application-default", "login", f"--scopes={scopes}"])
                                        
                                        # Re-check after the command runs
                                        if adc_path.exists():
                                            console.print("[green]✅ Google Auth is now ready![/green]")
                                            config.update_env_file("EMATA_AUTH_MODE", "google_auth")
                                            console.print("[bold green]✓ Auth mode set to Google Auth (ADC).[/bold green]")
                                            console.print("[dim]Please restart EMATA for the engine to switch clients.[/dim]")
                                        else:
                                            console.print("[red]❌ ADC file still not found. Authentication might have failed.[/red]")
                                    else:
                                        console.print("\n[dim]Once done, come back and switch to Google Auth again.[/dim]")
                                except (KeyboardInterrupt, EOFError):
                                    console.print("\n[yellow]Cancelled auth handshake.[/yellow]")
                            else:
                                console.print("[green]✅ Google Auth is ready to use![/green]")
                                config.update_env_file("EMATA_AUTH_MODE", "google_auth")
                                console.print("[bold green]✓ Auth mode set to Google Auth (ADC).[/bold green]")
                                console.print("[dim]Please restart EMATA for the engine to switch clients.[/dim]")
                                
                    except (KeyboardInterrupt, EOFError):
                        console.print("\n[yellow]Cancelled auth change.[/yellow]")
                    continue

                elif user_input.lower().startswith(":model"):
                    parts = user_input.split(maxsplit=1)
                    if len(parts) < 2:
                        console.print("[red]Usage: :model <model_name> (e.g., :model gemini-3-flash-preview)[/red]")
                    else:
                        new_model = parts[1].strip()
                        config.model = new_model
                        agent.config.model = new_model
                        console.print(f"[bold green]✓ Switched model to: {new_model}[/bold green]")
                    continue
                    
                elif user_input.lower() == ":mouse":
                    if not os.environ.get("TMUX"):
                        console.print("[yellow]⚠️  Mouse management is only available inside tmux.[/yellow]")
                        continue
                    
                    current = get_tmux_mouse_state()
                    new_state = "off" if current == "on" else "on"
                    set_tmux_mouse(new_state)
                    
                    msg = "[bold green]✓ Mouse Mode ON[/bold green] (Scrolling active)" if new_state == "on" else \
                          "[bold yellow]✓ Mouse Mode OFF[/bold yellow] (Native Highlighting/Copying active)"
                    console.print(msg)
                    if new_state == "on":
                        console.print("[dim]💡 Tip: Hold [bold]Shift[/bold] while dragging to copy text without turning this off.[/dim]")
                    continue

                elif user_input.lower() == ":help":
                    console.print("[bold cyan]Available Commands:[/bold cyan]")
                    console.print("  [yellow]:clear[/yellow]          Reset conversation history")
                    console.print("  [yellow]:sessions[/yellow]       List all concurrent EMATA sessions (alias: :session)")
                    console.print("  [yellow]:change-model[/yellow]  List and select a default model from the API (alias: :chante-model)")
                    console.print("  [yellow]:model <name>[/yellow]    Switch active model for this session")
                    console.print("  [yellow]:auth[/yellow]           Toggle between API Key and Google Auth")
                    console.print("  [yellow]:mouse[/yellow]          Toggle Mouse Mode (Turn OFF to copy text easily)")
                    console.print("                  [dim]Note: You can also hold [bold]Shift[/bold] to copy anytime.[/dim]")
                    console.print("  [yellow]:config[/yellow]         View active configuration and Session ID")
                    console.print("  [yellow]:exit[/yellow] or [yellow]:quit[/yellow]    Exit current session and clear history")
                    continue

                elif user_input.lower() in [":session", ":sessions"]:
                    if not os.environ.get("TMUX"):
                        console.print("[yellow]⚠️  Session management is only available when running inside tmux.[/yellow]")
                        continue

                    console.print("[bold cyan]Concurrent EMATA Sessions in this Directory:[/bold cyan]")
                    try:
                        current_session = os.environ.get("TMUX_SESSION_NAME")
                        current_dir = os.getcwd()
                        res = subprocess.run(
                            ["tmux", "list-sessions", "-F", "#{session_name} #{session_attached} #{@gagent_pwd}"],
                            capture_output=True, text=True
                        )
                        if res.returncode == 0:
                            found_any = False
                            for line in res.stdout.strip().split("\n"):
                                if not line.strip(): continue
                                parts = line.split(" ", 2)
                                if len(parts) >= 3:
                                    name, attached, path = parts
                                    if path.strip() == current_dir:
                                        if name == current_session:
                                            status = "[green]● CURRENT[/green]"
                                        else:
                                            status = "[blue]🔵 Attached[/blue]" if attached == "1" else "[dim]○ Detached[/dim]"
                                        console.print(f"  {status} [bold magenta]{name}[/bold magenta]")
                                        found_any = True
                            
                            if not found_any:
                                console.print("  [dim]No other sessions found for this directory.[/dim]")
                            else:
                                console.print("\n[dim]To switch sessions: Open a new terminal and select the desired ID from the startup menu.[/dim]")
                        else:
                            console.print("  [dim]Could not query TMUX sessions.[/dim]")
                    except Exception as e:
                        console.print(f"  [red]Error querying TMUX: {e}[/red]")

                    console.print(f"\n[bold cyan]Recent History Files (~/.emata/sessions):[/bold cyan]")
                    try:
                        history_dir = Path(agent.session_dir)
                        if history_dir.exists():
                            files = sorted(history_dir.glob("*.json"), key=os.path.getmtime, reverse=True)
                            if not files:
                                console.print("  [dim]No history files found.[/dim]")
                            for f in files[:5]: # Show last 5
                                mtime = os.path.getmtime(f)
                                from datetime import datetime
                                dt = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
                                size = f.stat().st_size
                                console.print(f"  [dim]{dt}[/dim] [cyan]{f.name}[/cyan] ({size} bytes)")
                        else:
                            console.print("  [dim]History directory does not exist.[/dim]")
                    except Exception as e:
                        console.print(f"  [red]Error listing history: {e}[/red]")
                    continue
                    
                # Stream the response chunk by chunk
                full_response_text = ""
                current_type = None
                has_content = False
                
                live = None
                markdown_content = ""

                def stop_live():
                    nonlocal live
                    if live:
                        live.stop()
                        live = None

                def wrapped_on_tool_call(name, args):
                    nonlocal current_type, markdown_content
                    stop_live()
                    
                    # Show detailed tool information
                    import json
                    args_str = json.dumps(args, indent=2) if args else "{}"
                    console.print(Panel(
                        f"[bold cyan]🛠️  Executing Tool:[/bold cyan] [yellow]{name}[/yellow]\n[dim]{args_str}[/dim]",
                        border_style="cyan",
                        padding=(0, 1)
                    ))
                    
                    on_tool_call(name, args)
                    current_type = "tool"
                    markdown_content = ""

                thinking_content = ""
                
                try:
                    import logging
                    ui_logger = logging.getLogger("gagent.ui")
                    
                    for chunk in agent.send_message_stream(user_input, on_tool_call=wrapped_on_tool_call):
                        chunk_type = chunk["type"]
                        content = chunk["content"]
                        
                        ui_logger.debug(f"UI received chunk: {chunk_type}")
                        
                        if chunk_type == "heartbeat":
                            continue
                        
                        # Only mark as having content if it's something the user can actually see or a tool call
                        has_content = True
                        
                        if chunk_type == "thought":
                            stop_live()
                            if current_type != "thought":
                                console.print("[bold dim yellow]💭 Thinking...[/bold dim yellow]")
                                current_type = "thought"
                                thinking_content = ""
                            
                            # Print thought segments directly in dim style without creating new lines
                            sys.stdout.write(f"\033[2m{content}\033[0m")
                            sys.stdout.flush()
                            thinking_content += content
                        
                        elif chunk_type == "text":
                            if current_type == "thought":
                                # Finish thinking block with a clean break
                                sys.stdout.write("\n\n")
                                sys.stdout.flush()
                            
                            if current_type != "text":
                                console.print("[bold cyan]Agent:[/bold cyan]")
                                current_type = "text"
                                markdown_content = ""
                            
                            markdown_content += content
                            full_response_text += content
                            
                            if not live:
                                live = Live(Markdown(markdown_content), console=console, refresh_per_second=10, transient=False)
                                live.start()
                            else:
                                live.update(Markdown(markdown_content))
                finally:
                    stop_live()
                
                # Print a final newline
                console.print()

                if not has_content:
                    stop_live() # Extra safety
                    console.print("[bold yellow]⚠️  The model returned an empty response.[/bold yellow]")
                    console.print("[dim]This can happen if the conversation history is too long or confusing. Try typing ':clear' to reset.[/dim]\n")
                
            except KeyboardInterrupt:
                # Handle Ctrl+C gracefully
                console.print("\n[yellow]Operation aborted. Type :exit to quit.[/yellow]\n")
            except Exception as e:
                console.print(f"\n[bold red]Error:[/bold red] {e}\n")
    finally:
        # Restore original tmux mouse state on exit
        if original_mouse_state is not None:
            set_tmux_mouse(original_mouse_state)

if __name__ == "__main__":
    main()
