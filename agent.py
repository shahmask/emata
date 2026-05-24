from google import genai
from google.genai import types
from google.genai.types import Content, Part
from google.api_core import exceptions
from tools import ALL_TOOLS, TOOL_MAPPING

# --- Pydantic Monkeypatch for types.ToolConfig to support include_server_side_tool_invocations ---
original_init = types.ToolConfig.__init__
def patched_init(self, *args, **kwargs):
    flag = kwargs.pop("include_server_side_tool_invocations", None)
    original_init(self, *args, **kwargs)
    if flag is not None:
        object.__setattr__(self, "include_server_side_tool_invocations", flag)
types.ToolConfig.__init__ = patched_init

original_validate = types.ToolConfig.model_validate
@classmethod
def patched_validate(cls, obj, *args, **kwargs):
    flag = None
    if isinstance(obj, dict):
        obj = dict(obj)
        flag = obj.pop("include_server_side_tool_invocations", None)
    res = original_validate(obj, *args, **kwargs)
    if flag is not None:
        object.__setattr__(res, "include_server_side_tool_invocations", flag)
    return res
types.ToolConfig.model_validate = patched_validate

original_dump = types.ToolConfig.model_dump
def patched_dump(self, *args, **kwargs):
    data = original_dump(self, *args, **kwargs)
    if hasattr(self, "include_server_side_tool_invocations"):
        data["include_server_side_tool_invocations"] = self.include_server_side_tool_invocations
    return data
types.ToolConfig.model_dump = patched_dump
# ----------------------------------------------------------------------------------------------
import os
import hashlib
import json
import time
import logging

logger = logging.getLogger("emata.agent")

class Agent:
    def __init__(self, config):
        self.config = config
        
        try:
            # Support for API Key or Google Auth (ADC)
            if config.auth_mode == "google_auth":
                self.client = genai.Client()
                logger.info("Agent initialized using Google Auth (ADC)")
            else:
                self.client = genai.Client(api_key=config.api_key)
                logger.info("Agent initialized using API Key")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini Client: {e}")
            raise RuntimeError(f"Authentication Failure: {e}. Try running :auth to reconfigure.")
            
        self.history = []
        self.session_dir = os.path.expanduser("~/.emata/sessions")
        logger.debug(f"Agent initialized with model: {config.model}")
        
        # Dynamically locate source code directory for self-modification
        self.source_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Base system instruction for the agent
        self.base_instruction = (
            "You are EMATA (Enduring Multi-Agent Terminal App), a highly capable, pragmatic, and helpful local terminal AI coding assistant. "
            "You run directly on the user's local machine inside the terminal. "
            "You have full access to read, write, create, and delete files, and run terminal commands in the current working directory.\n\n"
            f"Current working directory: {os.getcwd()}\n"
            "Operating System: Linux (bash)\n\n"
            "Rules & Persona:\n"
            "1. Output beautiful, standard GitHub-flavored Markdown. Use clean headers, lists, code blocks, and tables.\n"
            "2. Keep your answers concise, practical, and highly direct. Avoid over-the-top politeness, flattery, or excessive wordiness.\n"
            "3. If the user asks you to modify code, write code, or run a command, use the appropriate tool to do so directly. Proactively make the changes. "
            "Always verify your changes if possible (e.g. check compilation or build if requested).\n"
            "4. NEVER invent tools. Use ONLY the tools provided to you:\n"
            "   - list_dir: to list files in a folder\n"
            "   - read_file: to inspect code or files\n"
            "   - write_file: to create or modify code/files\n"
            "   - delete_file: to clean up files\n"
            "   - run_command: to execute terminal/shell commands\n"
            "5. When executing shell commands using run_command, you MUST always use non-interactive, silent, or auto-yes flags (e.g., 'npm init -y', 'pip install --quiet', 'apt-get install -y', etc.) because the execution tool does not support interactive prompts or keyboard input.\n"
            f"6. Self-Modification & Recursive Engineering: You have full access to your own source code (located at '{self.source_dir}'). If the user requests you to add features to yourself, modify your prompts, improve your tools, or update your CLI commands, you MUST proactively read your own codebase, formulate the changes, write the code back, and notify the user that you have successfully upgraded yourself.\n"
        )
        
        # Append local project instructions (.gemini) if they exist
        if config.system_instructions:
            self.system_instruction = (
                f"{self.base_instruction}\n"
                "----------------------------------------\n"
                "CRITICAL PROJECT-SPECIFIC RULES (.gemini):\n"
                f"{config.system_instructions}\n"
                "----------------------------------------\n"
            )
        else:
            self.system_instruction = self.base_instruction

        self.session_loaded = self.load_session()

    def serialize_history(self, history):
        serialized = []
        for content in history:
            parts_data = []
            if not content.parts:
                continue
            for part in content.parts:
                # IMPORTANT: We flatten 'thought' parts into 'text' parts for history persistence.
                # Re-sending raw 'thought' parts can sometimes confuse the model's internal state
                # or trigger capacity errors (503) in preview models.
                if part.text:
                    part_dict = {"type": "text", "text": part.text}
                    if hasattr(part, 'thought_signature') and part.thought_signature:
                        import base64
                        part_dict["thought_signature"] = base64.b64encode(part.thought_signature).decode('utf-8')
                    parts_data.append(part_dict)
                elif hasattr(part, 'thought') and part.thought:
                    # Convert thoughts to a visible "Thought" block in the text history
                    thoughts_text = f"\n[Thinking Process]\n{part.thought}\n"
                    parts_data.append({"type": "text", "text": thoughts_text})
                elif part.function_call:
                    fc_dict = {
                        "type": "function_call",
                        "name": part.function_call.name,
                        "args": part.function_call.args
                    }
                    if hasattr(part.function_call, 'thought_signature') and part.function_call.thought_signature:
                        import base64
                        fc_dict["thought_signature"] = base64.b64encode(part.function_call.thought_signature).decode('utf-8')
                    parts_data.append(fc_dict)
                elif part.function_response:
                    parts_data.append({
                        "type": "function_response",
                        "name": part.function_response.name,
                        "response": part.function_response.response
                    })
            serialized.append({
                "role": content.role,
                "parts": parts_data
            })
        return serialized

    def deserialize_history(self, serialized):
        history = []
        for item in serialized:
            parts = []
            for p in item["parts"]:
                if p["type"] == "text":
                    text_part = Part.from_text(text=p["text"])
                    if "thought_signature" in p:
                        import base64
                        text_part.thought_signature = base64.b64decode(p["thought_signature"])
                    parts.append(text_part)
                elif p["type"] == "function_call":
                    import base64
                    fc = types.FunctionCall(name=p["name"], args=p["args"])
                    if "thought_signature" in p:
                        fc.thought_signature = base64.b64decode(p["thought_signature"])
                    parts.append(Part(function_call=fc))
                elif p["type"] == "function_response":
                    parts.append(Part.from_function_response(name=p["name"], response=p["response"]))
            history.append(Content(role=item["role"], parts=parts))
        return history

    def list_available_models(self):
        """Lists all models available to the current client."""
        try:
            # For public API, we usually want to filter for generativelanguage models
            models = self.client.models.list()
            # Convert to list of strings
            return [m.name for m in models]
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []

    def _get_session_path(self):
        cwd = os.getcwd()
        h = hashlib.sha256(cwd.encode('utf-8')).hexdigest()[:12]
        folder_name = os.path.basename(cwd) or "root"
        safe_folder_name = "".join([c if c.isalnum() else "_" for c in folder_name])
        
        # Unique history per TMUX session to allow concurrent independent work in same folder
        session_id = os.environ.get("TMUX_SESSION_NAME", "default")
        return os.path.join(self.session_dir, f"{safe_folder_name}_{h}_{session_id}.json")

    def save_session(self):
        try:
            os.makedirs(self.session_dir, exist_ok=True)
            path = self._get_session_path()
            logger.debug(f"Saving session to: {path}")
            data = {
                "cwd": os.getcwd(),
                "history": self.serialize_history(self.history)
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving session: {e}")

    def load_session(self):
        path = self._get_session_path()
        logger.debug(f"Loading session from: {path}")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.history = self.deserialize_history(data.get("history", []))
                
                # PRUNE TRAILING USER MESSAGES: The Gemini API requires alternating User/Model roles.
                # If the last message is from the user, it means the model never responded.
                # We remove it to keep the history valid for the next turn.
                while self.history and self.history[-1].role == "user":
                    self.history.pop()
                
                return len(self.history) > 0
            except Exception:
                pass
        return False

    def clear_session(self):
        path = self._get_session_path()
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

    def send_message_stream(self, user_text: str, on_tool_call=None, on_confirm=None):
        """Sends a message to Gemini and yields output chunks (including thinking and text) as they stream in.
        Supports executing tool calling loops interactively while streaming.
        """
        logger.info(f"Sending message: {user_text[:50]}...")
        # Append user message and save
        user_msg = Content(role="user", parts=[Part.from_text(text=user_text)])
        self.history.append(user_msg)
        self.save_session()
        
        thinking_config = None
        budget = self.config.thinking_budget
        level = self.config.thinking_level
        
        # Map thinking_level strings to integer token budgets
        if budget is None and level is not None:
            level_map = {
                "minimal": 1024,
                "low": 2048,
                "medium": 8192,
                "high": 16384
            }
            budget = level_map.get(str(level).lower(), 2048)
            
        if budget is not None:
            # ThinkingConfig in modern SDK supports thinking_budget and include_thoughts
            thinking_config = types.ThinkingConfig(
                thinking_budget=budget,
                include_thoughts=True
            )

        success = False

        try:
            while True:
                max_retries = 3
                retry_count = 0
                
                full_text = []
                function_calls = []
                last_thought_signature = None
                
                while retry_count < max_retries:
                    try:
                        logger.debug(f"Starting stream attempt {retry_count + 1}/{max_retries} using model {self.config.model}")
                        
                        active_tools = ALL_TOOLS.copy()
                        if self.config.search_enabled:
                            # Enable Google Search grounding for real-time info
                            google_search_tool = types.Tool(
                                google_search=types.GoogleSearch()
                            )
                            active_tools.append(google_search_tool)
                        
                        response_stream = self.client.models.generate_content_stream(
                            model=self.config.model,
                            contents=self.history,
                            config=types.GenerateContentConfig(
                                system_instruction=self.system_instruction,
                                tools=active_tools,
                                tool_config=types.ToolConfig(
                                    include_server_side_tool_invocations=True
                                ),
                                thinking_config=thinking_config,
                            )
                        )
                        
                        # Iterate through the stream. If a 503 happens during iteration, it will be caught here.
                        chunk_count = 0
                        for chunk in response_stream:
                            chunk_count += 1
                            logger.info(f"Chunk {chunk_count} received")
                            yield {"type": "heartbeat", "content": ""}

                            if chunk.candidates:
                                candidate = chunk.candidates[0]
                                logger.info(f"Chunk {chunk_count} Candidate: {candidate}")
                                
                                if candidate.finish_reason and candidate.finish_reason not in [types.FinishReason.STOP, types.FinishReason.OTHER]:
                                    logger.warning(f"Model halted: {candidate.finish_reason}")
                                    yield {"type": "text", "content": f"\n[bold red]⚠️  Model halted:[/bold red] {candidate.finish_reason}"}
                                    if candidate.finish_message:
                                        yield {"type": "text", "content": f" - {candidate.finish_message}"}
                                    return

                                if candidate.content and candidate.content.parts:
                                    for part in candidate.content.parts:
                                        # Capture thought signature if present
                                        if hasattr(part, 'thought_signature') and part.thought_signature:
                                            last_thought_signature = part.thought_signature

                                        if hasattr(part, 'thought') and part.thought:
                                            yield {"type": "thought", "content": part.thought}
                                        
                                        if part.text:
                                            yield {"type": "text", "content": part.text}
                                            full_text.append(part.text)
                                            
                                        if part.function_call:
                                            logger.debug(f"Received function call: {part.function_call.name}")
                                            function_calls.append(part.function_call)
                            else:
                                continue
                        
                        # If we successfully finished the loop, break the retry while loop
                        logger.debug("Stream completed successfully")
                        break
                        
                    except (exceptions.ServiceUnavailable, exceptions.InternalServerError, exceptions.DeadlineExceeded, genai.errors.ServerError, genai.errors.ClientError) as e:
                        retry_count += 1
                        # Handle both SDK exception types for code/status
                        error_code = getattr(e, "code", "Unknown")
                        if hasattr(e, "status_code"):
                            error_code = e.status_code
                            
                        # If it's a 429 (Resource Exhausted), we should show the specific message
                        if error_code == 429:
                            yield {"type": "text", "content": f"\n[bold red]⚠️ Quota Exceeded (429):[/bold red] You've hit a rate limit. Waiting before retry... ({retry_count}/{max_retries})\n"}
                            
                        logger.warning(f"API Error ({error_code}): {str(e)}. Attempt {retry_count}/{max_retries}")
                        if retry_count >= max_retries:
                            logger.error(f"Failed after {max_retries} retries: {str(e)}")
                            yield {"type": "text", "content": f"\n[bold red]❌ Request failed after {max_retries} retries:[/bold red] {str(e)}\n"}
                            break
                        
                        full_text = []
                        function_calls = []
                        
                        wait_time = 2 ** retry_count
                        yield {"type": "text", "content": f"\n[yellow]⚠️  API Error ({error_code}). Retrying in {wait_time}s... ({retry_count}/{max_retries})[/yellow]\n"}
                        time.sleep(wait_time)
                    except Exception as e:
                        logger.exception(f"Unexpected error during stream: {str(e)}")
                        yield {"type": "text", "content": f"\n[bold red]❌ Unexpected Error during stream:[/bold red] {str(e)}\n"}
                        break
                
                model_parts = []
                if full_text:
                    text_part = Part.from_text(text="".join(full_text))
                    if last_thought_signature:
                        text_part.thought_signature = last_thought_signature
                    model_parts.append(text_part)
                for fc in function_calls:
                    fc_part = Part(function_call=fc)
                    if last_thought_signature:
                        fc_part.thought_signature = last_thought_signature
                    model_parts.append(fc_part)
                    
                if model_parts:
                    logger.debug(f"Adding model response to history: {len(model_parts)} parts")
                    self.history.append(Content(role="model", parts=model_parts))
                    self.save_session()
                    success = True
                    
                if not function_calls:
                    # Final response segment - break the loop
                    break
                    
                # Execute function calls
                for function_call in function_calls:
                    name = function_call.name
                    args = function_call.args
                    
                    if on_tool_call:
                        on_tool_call(name, args)
                        
                    # Handle confirmation for risky tools
                    if on_confirm:
                        is_risky = False
                        if name == "delete_file":
                            is_risky = True
                        elif name == "run_command":
                            cmd = args.get("command", "").lower()
                            # Standard risky keywords/patterns
                            risky_keywords = ["rm ", "mv ", "git reset", "git push", "chmod", "chown", "kill", "systemctl", "sudo", "apt", ">"]
                            if any(k in cmd for k in risky_keywords):
                                is_risky = True
                        
                        if is_risky:
                            confirmed = on_confirm(name, args)
                            if not confirmed:
                                logger.info(f"User declined execution of {name}")
                                tool_part = Part.from_function_response(
                                    name=name,
                                    response={"result": f"Error: Execution of tool '{name}' was declined by the user for safety reasons."}
                                )
                                self.history.append(Content(role="tool", parts=[tool_part]))
                                self.save_session()
                                continue

                    logger.info(f"Executing tool: {name}")
                    try:
                        tool_func = TOOL_MAPPING.get(name)
                        if tool_func:
                            result = tool_func(**args)
                        else:
                            result = f"Error: Tool '{name}' not found."
                            logger.error(result)
                    except Exception as e:
                        result = f"Error executing tool '{name}': {e}"
                        logger.exception(result)
                        
                    tool_part = Part.from_function_response(
                        name=name,
                        response={"result": str(result)}
                    )
                    self.history.append(Content(role="tool", parts=[tool_part]))
                    self.save_session()
        except Exception as e:
            if not success:
                logger.exception(f"Critical Agent Error: {str(e)}")
                yield {"type": "text", "content": f"\n[bold red]❌ Critical Agent Error:[/bold red] {str(e)}\n"}
        finally:
            self.save_session()
