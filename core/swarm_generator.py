import os
import json
import uuid
from google import genai
from google.genai import types

def generate_swarm_agents(fsm_state: str, target: str):
    api_keys_str = os.getenv("GEMINI_API_KEYS", "")
    keys = [k.strip().replace('"', '').replace("'", "") for k in api_keys_str.split(",") if k.strip()]
    valid_keys = [k for k in keys if k.startswith("AIza") or k.startswith("AQ.")]
    if not valid_keys:
        print("[SwarmGenerator] No valid API keys found.")
        return []
    
    client = genai.Client(api_key=valid_keys[0])
    
    prompt = f"""
    The NEMESIS OS is currently transitioning into the FSM state: {fsm_state}.
    The current intelligence target is: {target}.
    
    You must auto-generate between 1 and 3 specialized Swarm Agents required to execute operations for this state.
    Output ONLY valid JSON. Do not include markdown blocks. The output must be an array of objects matching this schema:
    [
        {{
            "agent_id": "string",
            "agent_name": "string (e.g. 'Deep_Graph_Analyzer')",
            "system_role": "string",
            "system_instructions": "string (detailed prompt instructions on how they should execute the task using Omni-Engineer toolset)"
        }}
    ]
    """
    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.7)
        )
        
        # Clean JSON markdown if present
        text = response.text.replace('```json', '').replace('```', '').strip()
        agents = json.loads(text)
        return agents
    except Exception as e:
        print(f"[SwarmGenerator] Failed to generate agents: {e}")
        return []
