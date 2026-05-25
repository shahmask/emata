import os
import logging
import warnings
import traceback
from google import genai
from tools import TOOL_MAPPING, ALL_TOOLS

# Suppress annoying warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*urllib3 v2 only supports OpenSSL1.1.1+.*")

logger = logging.getLogger("emata.agent")

class Agent:
    def __init__(self, config):
        self.config = config
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
            
            logger.info("Agent initialized with API Key")
        except Exception as e:
            logger.error(f"Failed to initialize Client: {e}")
            raise RuntimeError(f"Authentication Failure: {e}")

    def send_message_stream(self, message):
        """Sends a message and handles tool calling loop manually."""
        if message:
            self.history.append({"role": "user", "parts": [{"text": message}]})
        
        try:
            # Novice Protection: If history gets too long, truncate oldest turns
            if len(self.history) > 40: # roughly 20 turns
                logger.info("Truncating history to save context")
                self.history = self.history[-30:] # Keep last 15 turns

            while True:
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
                    # Thoughts
                    thought = getattr(chunk, 'thought', None)
                    if thought:
                        if not is_thinking:
                            yield {"type": "thought_start"}
                            is_thinking = True
                        yield {"type": "thought", "content": thought}
                    
                    # Text and Tool Calls
                    for candidate in chunk.candidates:
                        if candidate.content and candidate.content.parts:
                            for part in candidate.content.parts:
                                if part.text:
                                    if is_thinking:
                                        yield {"type": "thought_end"}
                                        is_thinking = False
                                    yield {"type": "text", "content": part.text}
                                    full_response_parts.append(part)
                                
                                if part.function_call:
                                    if is_thinking:
                                        yield {"type": "thought_end"}
                                        is_thinking = False
                                    
                                    call = part.function_call
                                    yield {"type": "tool_call", "name": call.name, "args": call.args}
                                    full_response_parts.append(part)
                                    current_calls.append(call)

                if full_response_parts:
                    self.history.append({"role": "model", "parts": full_response_parts})

                if current_calls:
                    yield {"type": "awaiting_execution", "calls": current_calls}
                    return 
                
                break
                    
        except Exception as e:
            err_msg = str(e)
            logger.error(f"Loop error: {err_msg}")
            
            # Specific novice-friendly error handling
            if "maximum number of tokens allowed" in err_msg:
                yield {"type": "error", "content": "Context Limit Reached! Clearing oldest history and retrying..."}
                self.history = self.history[-10:] # Aggressive truncation
                if message: # Retry once with truncated history
                    yield from self.send_message_stream(None)
            elif "429" in err_msg or "Resource has been exhausted" in err_msg:
                yield {"type": "error", "content": "Rate Limit (429) Reached! Please wait a few seconds before your next query."}
            else:
                yield {"type": "error", "content": err_msg}

    def inject_tool_results(self, tool_responses):
        parts = []
        for name, result in tool_responses.items():
            parts.append(genai.types.Part(
                function_response=genai.types.FunctionResponse(
                    name=name,
                    response={"result": str(result)}
                )
            ))
        if parts:
            self.history.append({"role": "user", "parts": parts})

    def clear_history(self):
        """Resets conversation history for performance."""
        self.history = []
