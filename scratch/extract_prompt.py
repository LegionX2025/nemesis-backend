import json
import os

transcript_path = r"C:\Users\LEGIONX\.gemini\antigravity\brain\aadd294e-cc7f-424d-b7cc-bdcf5823b852\.system_generated\logs\transcript_full.jsonl"
with open(transcript_path, 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        if data.get('type') == 'USER_INPUT' and 'Forensic Report' in data.get('content', ''):
            with open('scratch/full_user_prompt.txt', 'w', encoding='utf-8') as out:
                out.write(data['content'])
            break
