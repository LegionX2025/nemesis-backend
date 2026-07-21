import os
import sys
import json
import uuid
import datetime
from google import genai
from google.genai import types

# Add parent directory to path so we can import omni_engineer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from omni_engineer import run_omni_agent, get_valid_keys
except ImportError:
    pass

class NemesisLLM:
    def __init__(self):
        self.api_keys = self._get_valid_keys()
        self.model = "gemini-3.1-pro"
        self.memory_dir = os.path.join(os.getcwd(), "datasets")
        self.kb_dir = os.path.join(os.getcwd(), "NEMESIS_KNOWLEDGE_BASE_LIBRARY")
        os.makedirs(self.memory_dir, exist_ok=True)
        os.makedirs(self.kb_dir, exist_ok=True)
        
        self.system_instruction = """
        You are NEMESIS AI, the central intelligence layer of the NEMESIS OS.
        You perform deep blockchain analytics, forensic reasoning, and autonomous threat analysis.
        You have the ability to read from the internal datasets and apply advanced heuristics.
        Always respond with high professionalism and tactical precision.
        """
        self.chat_sessions = {}

    def _get_valid_keys(self):
        api_keys_str = os.getenv("GEMINI_API_KEYS", "")
        keys = [k.strip().replace('"', '').replace("'", "") for k in api_keys_str.split(",") if k.strip()]
        return [k for k in keys if k.startswith("AIza") or k.startswith("AQ.")]

    def get_client(self):
        if not self.api_keys:
            raise ValueError("No valid GEMINI_API_KEYS found.")
        return genai.Client(api_key=self.api_keys[0])

    def start_chat(self, session_id):
        client = self.get_client()
        chat = client.chats.create(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=0.3
            )
        )
        self.chat_sessions[session_id] = chat
        return session_id

    def chat(self, session_id, message):
        if session_id not in self.chat_sessions:
            self.start_chat(session_id)
        
        chat = self.chat_sessions[session_id]
        
        # Inject RAG / Context from local datasets
        context = self._retrieve_context()
        if context:
            message = f"--- INTERNAL OS MEMORY CONTEXT ---\n{context}\n--------------------------------\n\nUSER PROMPT:\n{message}"
            
        try:
            response = chat.send_message(message)
            return response.text
        except Exception as e:
            return f"NEMESIS AI Error: {e}"

    def _retrieve_context(self):
        dataset_path = os.path.join(self.memory_dir, "nemesis_memory.jsonl")
        if not os.path.exists(dataset_path):
            return ""
        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                lines = f.readlines()[-20:] # Retrieve last 20 memories
                return "".join(lines)
        except Exception:
            return ""

    def auto_teach(self, trace_result: dict):
        """ The AutoTeacher module converts raw trace results into fine-tuning/RAG datasets """
        client = self.get_client()
        prompt = f"Analyze the following trace result and extract 3 key heuristic rules or threat patterns in JSON format:\n{json.dumps(trace_result)}"
        
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash", 
                contents=prompt
            )
            insight_id = str(uuid.uuid4())
            memory_record = {
                "id": insight_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "type": "heuristic_extraction",
                "content": response.text,
                "raw_trace": trace_result
            }
            
            dataset_path = os.path.join(self.memory_dir, "nemesis_memory.jsonl")
            with open(dataset_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(memory_record) + "\n")
                
            return memory_record
        except Exception as e:
            print(f"[AutoTeacher] Failed to extract heuristic: {e}")
            return None

    def dispatch_swarm_agent(self, agent_profile: dict):
        """ Invokes the Omni-Engineer protocol to give the AI physical execution capability based on auto-generated profiles """
        try:
            print(f"[NEMESIS LLM] Dispatching Swarm Agent: {agent_profile['agent_name']} - {agent_profile['system_role']}")
            valid_keys = get_valid_keys()
            if not valid_keys:
                return False
                
            prompt = f"SYSTEM INSTRUCTIONS:\n{agent_profile['system_instructions']}\n\nYou are executing as {agent_profile['agent_name']}. Perform your tasks."
            # In a production environment this would be run asynchronously to not block the main OS thread
            success = run_omni_agent(valid_keys, prompt)
            return success
        except Exception as e:
            print(f"[NEMESIS LLM] Failed to dispatch swarm agent: {e}")
            return False

nemesis_ai_engine = NemesisLLM()
