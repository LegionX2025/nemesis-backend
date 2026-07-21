import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.tracing_engine_v33 import NemesisV33Engine

engine = NemesisV33Engine()
print(f"Engine loaded. Registered providers: {engine.api_registry.list_providers()}")
