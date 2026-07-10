import os
import json
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import shutil

class NemesisConfigManager:
    """Manages reading and writing to the .env file and loading configurations."""
    
    def __init__(self, env_path: str = ".env"):
        self.env_path = env_path
        # Use absolute path to ensure we always write to the correct .env
        self.abs_env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", self.env_path))

    def load_config(self) -> Dict[str, str]:
        """Load all variables from the .env file into a dictionary."""
        config = {}
        if not os.path.exists(self.abs_env_path):
            return config
            
        with open(self.abs_env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    # Strip quotes if present
                    val = val.strip("\"'")
                    config[key.strip()] = val
        return config

    def update_config(self, updates: Dict[str, str]) -> bool:
        """Update specific keys in the .env file. Preserves comments and ordering."""
        # Create file if it doesn't exist
        if not os.path.exists(self.abs_env_path):
            with open(self.abs_env_path, "w", encoding="utf-8") as f:
                f.write("# NEMESIS OMEGA CONFIGURATION\n")

        lines = []
        with open(self.abs_env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        updated_keys = set()
        new_lines = []
        
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                new_lines.append(line)
                continue
                
            if "=" in stripped:
                key = stripped.split("=", 1)[0].strip()
                if key in updates:
                    # Update existing key
                    new_lines.append(f"{key}={updates[key]}\n")
                    updated_keys.add(key)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        # Append new keys that weren't found in the file
        for key, val in updates.items():
            if key not in updated_keys:
                new_lines.append(f"{key}={val}\n")

        # Create a backup before writing
        backup_path = f"{self.abs_env_path}.backup"
        if os.path.exists(self.abs_env_path):
            shutil.copy2(self.abs_env_path, backup_path)

        # Write the new configuration
        with open(self.abs_env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
            
        # Update running os.environ so process doesn't need to restart to see changes
        for k, v in updates.items():
            os.environ[k] = str(v)
            
        return True

    def get_structured_config(self):
        """Returns the configuration grouped into logical categories for the UI."""
        raw = self.load_config()
        
        return {
            "api_keys": {
                "GEMINI_API_KEY": raw.get("GEMINI_API_KEY", ""),
                "OPENAI_API_KEY": raw.get("OPENAI_API_KEY", ""),
                "ANTHROPIC_API_KEY": raw.get("ANTHROPIC_API_KEY", ""),
                "XAI_API_KEY": raw.get("XAI_API_KEY", "")
            },
            "blockchain": {
                "ETH_RPC_URL": raw.get("ETH_RPC_URL", "https://eth.llamarpc.com"),
                "BSC_RPC_URL": raw.get("BSC_RPC_URL", "https://binance.llamarpc.com"),
                "SOL_RPC_URL": raw.get("SOL_RPC_URL", "https://api.mainnet-beta.solana.com"),
                "POLYGONSCAN_API_KEY": raw.get("POLYGONSCAN_API_KEY", ""),
                "ETHERSCAN_API_KEY": raw.get("ETHERSCAN_API_KEY", ""),
                "BSCSCAN_API_KEY": raw.get("BSCSCAN_API_KEY", "")
            },
            "database": {
                "MONGODB_URI": raw.get("MONGODB_URI", "mongodb://localhost:27017/"),
                "NEO4J_URI": raw.get("NEO4J_URI", "bolt://localhost:7687"),
                "NEO4J_USER": raw.get("NEO4J_USER", "neo4j"),
                "NEO4J_PASSWORD": raw.get("NEO4J_PASSWORD", "password")
            },
            "system": {
                "VITE_TOR_AUTO_START": raw.get("VITE_TOR_AUTO_START", "false"),
                "NEMESIS_SECURITY_LEVEL": raw.get("NEMESIS_SECURITY_LEVEL", "MAXIMUM"),
                "MAX_WORKER_THREADS": raw.get("MAX_WORKER_THREADS", "8")
            }
        }

# Global singleton instance
config_manager = NemesisConfigManager()
