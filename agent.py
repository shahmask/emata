import os
import logging
import warnings
import traceback
import time
import json
import hashlib
import base64
from google import genai
from tools import TOOL_MAPPING, ALL_TOOLS

# Suppress annoying warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*urllib3 v2 only supports OpenSSL1.1.1+.*")

logger = logging.getLogger("emata.agent")

class Agent:
    def __init__(self, config):
        self.config = config
        self.session_dir = os.path.expanduser("~/.emata/sessions")
        try:
            if not config.api_key:
                raise ValueError("Missing API Key.")
            
            self.client = genai.Client(api_key=config.api_key)
            self.history = []
            
            self.system_instruction = (
                "You are EMATA (Enduring Multi-Agent Terminal App). "
                "You have full autonomous access to the user's terminal via tools. "
                "You can read/write files and run shell commands. "
                "Be pragmatic, concise, and helpful. "
                "ALWAYS use tools to verify facts about the system or files. "
                "\n\n" + self.config.system_instructions
            )
            
            self.load_session()
            logger.info("Agent initialized with API Key")
        except Exception as e:
            logger.error(f"Failed to initialize Client: {e}")
            raise RuntimeError(f"Authentication Failure: {e}")

    def _get_session_path(self):
        cwd = os.getcwd()
        h = hashlib.sha256(cwd.encode('utf-8')).hexdigest()[:12]
        folder_name = os.path.basename(cwd) or "root"
        safe_folder_name = "".join([c if c.isalnum() else "_" for c in folder_name])
        session_id = os.environ.get("TMUX_SESSION_NAME", "default")
        return os.path.join(self.session_dir, f"{safe_folder_name}_{h}_{session_id}.json")

    def serialize_history(self):
        serialized = []
        for content in self.history:
            parts_data = []
            if not content.get("parts"): continue
            for part in content["parts"]:
                if "text" in part:
                    parts_data.append({"type": "text", "text": part["text"]})
                elif "function_call" in part:
                    fc = part["function_call"]
                    parts_data.append({
                        "type": "function_call",
                        "name": fc.name,
                        "args": fc.args
                    })
                elif "function_response" in part:
                    fr = part["function_response"]
                    parts_data.append({
                        "type": "function_response",
                        "name": fr.name,
                        "response": fr.response
                    })
            serialized.append({"role": content["role"], "parts": parts_data})
        return serialized

    def deserialize_history(self, serialized):
        history = []
        for item in serialized:
            parts = []
            for p in item["parts"]:
                if p["type"] == "text":
                    parts.append({"text": p["text"]})
                elif p["type"] == "function_call":
                    # We need the actual genai types for execution, but for history storage we use dicts
                    # The send_message_stream expects parts as dicts or types.
                    parts.append({"function_call": genai.types.FunctionCall(name=p["name"], args=p["args"])})
                elif p["type"] == "function_response":
                    parts.append({"function_response": genai.types.FunctionResponse(name=p["name"], response=p["response"])})
            history.append({"role": item["role"], "parts": parts})
        return history

    def save_session(self):
        try:
            os.makedirs(self.session_dir, exist_ok=True)
            path = self._get_session_path()
            data = {"cwd": os.getcwd(), "history": self.serialize_history()}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving session: {e}")

    def load_session(self):
        path = self._get_session_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.history = self.deserialize_history(data.get("history", []))
                # Prune trailing user messages
                while self.history and self.history[-1]["role"] == "user":
                    self.history.pop()
                return True
            except: pass
        return False

    def clear_session(self):
        path = self._get_session_path()
        if os.path.exists(path):
            try: os.remove(path)
            except: pass
        self.history = []

    def send_message_stream(self, message):
        """Sends a message and handles tool calling loop manually with retry logic."""
        if message:
            self.history.append({"role": "user", "parts": [{"text": message}]})
        
        # Novice Protection: If history gets too long, truncate oldest turns
        if len(self.history) > 40:
            logger.info("Truncating history to save context")
            self.history = self.history[-30:]

        max_retries = 3
        while True:
            retries = 0
            while retries <= max_retries:
                try:
                    response_stream = self.client.models.generate_content_stream(
                        model=self.config.model,
                        contents=self.history,
                        config=genai.types.GenerateContentConfig(
                            tools=ALL_TOOLS,
                            system_instruction=self.system_instruction,
                            automatic_function_calling={"disable": True}
                        )
                    )

                    full_response_parts = []
                    is_thinking = False
                    current_calls = []

                    for chunk in response_stream:
                        thought = getattr(chunk, 'thought', None)
                        if thought:
                            if not is_thinking:
                                yield {"type": "thought_start"}
                                is_thinking = True
                            yield {"type": "thought", "content": thought}
                        
                        for candidate in chunk.candidates:
                            if candidate.content and candidate.content.parts:
                                for part in candidate.content.parts:
                                    if part.text:
                                        if is_thinking:
                                            yield {"type": "thought_end"}
                                            is_thinking = False
                                        yield {"type": "text", "content": part.text}
                                        full_response_parts.append({"text": part.text})
                                    
                                    if part.function_call:
                                        if is_thinking:
                                            yield {"type": "thought_end"}
                                            is_thinking = False
                                        
                                        call = part.function_call
                                        yield {"type": "tool_call", "name": call.name, "args": call.args}
                                        full_response_parts.append({"function_call": call})
                                        current_calls.append(call)

                    if full_response_parts:
                        self.history.append({"role": "model", "parts": full_response_parts})
                        self.save_session()

                    if current_calls:
                        yield {"type": "awaiting_execution", "calls": current_calls}
                        return 
                    
                    return

                except Exception as e:
                    err_str = str(e)
                    if "maximum number of tokens allowed" in err_str:
                        yield {"type": "error", "content": "Context Limit Reached! Truncating history..."}
                        self.history = self.history[-10:]
                        self.save_session()
                        retries = 0 
                        continue

                    is_transient = any(msg in err_str for msg in ["503", "429", "high demand", "temporary", "UNAVAILABLE"])
                    if is_transient and retries < max_retries:
                        retries += 1
                        wait_time = 2 ** retries
                        yield {"type": "thought", "content": f"\n[Transient Error: {err_str}. Retrying in {wait_time}s...]\n"}
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Loop error: {e}")
                        yield {"type": "error", "content": err_str}
                        return

    def inject_tool_results(self, tool_responses):
        parts = []
        for name, result in tool_responses.items():
            parts.append({"function_response": genai.types.FunctionResponse(
                name=name,
                response={"result": str(result)}
            )})
        if parts:
            self.history.append({"role": "user", "parts": parts})
            self.save_session()

    def clear_history(self):
        """Resets conversation history."""
        self.history = []
        self.save_session()
