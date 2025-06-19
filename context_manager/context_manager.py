import uuid

class ContextManager:
    COMPRESSION_PROMPT = """
    You are a context summarizer for an AI agent. Your task is to take a verbose AI message and condense it to its essential parts, retaining all critical information, instructions, and data.

    RULES:
    1.  Do NOT change or omit any code blocks, file paths, or specific data values.
    2.  Remove conversational filler (e.g., "Okay, I will now...", "Here is the result...").
    3.  Condense long explanations into concise points.
    4.  Focus on the *conclusion* or *decision* the AI made.
    5.  The output must be a concise summary of the original message.

    Original Message:
    ---
    {original_ai_message}
    ---

    """

    def __init__(self, llm, compress_on_add: bool = True):
        self.llm = llm
        self.compress_on_add = compress_on_add
        self.context_history = []
        # Stores { "intent_summary": "msg_id_of_failed_ai_call" }
        self.pending_failed_tool_calls = {}
        self.uncompressed_tokens = 0
        self.compressed_tokens = 0

    def __del__(self):
        """Cleanup method to ensure no memory leaks."""
        self.context_history.clear()
        self.pending_failed_tool_calls.clear()

        self.print_status()

    def _generate_message_id(self) -> str:
        return f"msg_{uuid.uuid4().hex[:8]}"

    def _compress_content(self, content: str) -> str:
        """Uses an LLM to compress the content of an AI message."""
        if not self.compress_on_add or content.strip() == "":
            return content
        prompt = self.COMPRESSION_PROMPT.format(original_ai_message=content)
        # Assuming your LLM library has a simple invocation method
        response = self.llm.invoke(prompt)
        return response.content.strip()

    def _get_tool_intent(self, tool_call: dict) -> str:
        """Creates a simple summary of a tool call for matching failures."""
        # A more robust version could use an LLM to summarize the intent.
        return f"Tool: {tool_call['tool_name']}, Key Args: {list(tool_call.get('args', {}).keys())}"

    def add_message(self, message: dict):
        """Adds a new message to the context, processing it based on type."""
        msg_id = self._generate_message_id()
        msg_type = message["type"]
        original_content = message["content"]
        
        new_message = {
            "id": msg_id,
            "type": msg_type,
            "original_content": original_content,
            "compressed_content": original_content, # Default
            "metadata": {}
        }

        if msg_type == "system" or msg_type == "user":
            # Keep as is
            pass

        elif msg_type == "ai":
            new_message["compressed_content"] = self._compress_content(original_content)
            if message.get("tool_calls"):
                new_message["metadata"]["tool_call"] = message["tool_calls"][0] # Assuming one for simplicity

        elif msg_type == "tool":
            # This logic assumes the tool response is for the IMMEDIATELY preceding AI message.
            # A more robust system would use IDs to link them explicitly.
            last_ai_message = next((m for m in reversed(self.context_history) if m["type"] == "ai" and m["metadata"].get("tool_call")), None)
            
            if last_ai_message:
                is_successful = not ("error" in original_content.lower() or "failed" in original_content.lower()) # Use llm to determine success in a real scenario
                last_ai_message["metadata"]["tool_successful"] = is_successful
                new_message["metadata"]["is_response_to"] = last_ai_message["id"]

                if not is_successful:
                    # Mark the previous AI call as a pending failure
                    intent = self._get_tool_intent(last_ai_message["metadata"]["tool_call"])
                    self.pending_failed_tool_calls[intent] = last_ai_message["id"]
                else:
                    # If this one succeeded, check if it resolves a past failure
                    intent = self._get_tool_intent(last_ai_message["metadata"]["tool_call"])
                    if intent in self.pending_failed_tool_calls:
                        failed_msg_id = self.pending_failed_tool_calls[intent]
                        # Prune the failed AI message and its tool response
                        self.context_history = [
                            m for m in self.context_history
                            if m.get("id") != failed_msg_id and m.get("metadata", {}).get("is_response_to") != failed_msg_id
                        ]
                        del self.pending_failed_tool_calls[intent]
                        print(f"INFO: Pruned failed tool call {failed_msg_id} due to success.")

        self.context_history.append(new_message)
        # Update token counts
        self.uncompressed_tokens += len(original_content.split())
        self.compressed_tokens += len(new_message["compressed_content"].split())

    def _tool_string(self, tool_call: dict) -> str:
        """Formats a tool call for display."""
        tool_name = tool_call["tool_name"]
        args = "\n".join(f"<{k}>{v}</{k}>" for k, v in tool_call.get("args", {}).items())
        return f"<{tool_name}>\n{args}\n</{tool_name}>"
    
    def get_context(self) -> str:
        """Constructs the final context string from the processed history."""
        full_context = []
        for msg in self.context_history:
            # Simple formatting, can be customized for specific models
            role = msg['type'].capitalize()
            if role == "Ai": role = "Assistant"
            if role == "Tool": role = "Tool Response"

            full_context.append(f"{role}:\n{msg['compressed_content']}")

            # If this is an AI message with a tool call, append the tool call string
            if role == "Assistant" and msg.get("metadata", {}).get("tool_call"):
                tool_call = msg["metadata"]["tool_call"]
                tool_string = self._tool_string(tool_call)
                full_context.append(tool_string)
        
        return "\n\n".join(full_context)

    def __str__(self):
        return self.get_context()
    
    def print_status(self):
        """Prints the current status of the context manager."""
        print(f"Context Manager Status:")
        print(f"Total Messages: {len(self.context_history)}")
        print(f"Pending Failed Tool Calls: {len(self.pending_failed_tool_calls)}")
        print(f"Uncompressed Tokens: {self.uncompressed_tokens}")
        print(f"Compressed Tokens: {self.compressed_tokens}")