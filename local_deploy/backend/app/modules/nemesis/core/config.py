# nemesis/core/config.py

import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List

class NemesisConfig(BaseSettings):
    # Core Platform & Security
    node_env: str = Field(default="production", env="NODE_ENV")
    app_name: str = Field(default="nemesis-platform", env="APP_NAME")
    flask_secret_key: str = Field(default="REPLACE_ME", env="FLASK_SECRET_KEY")
    
    # Tracing
    trace_enable: bool = Field(default=True, env="TRACE_ENABLE")
    trace_max_depth: int = Field(default=20, env="TRACE_MAX_DEPTH")
    trace_stop_on_terminal: bool = Field(default=True, env="TRACE_STOP_ON_TERMINAL")
    
    # AI & Intelligence
    gemini_api_keys: str = Field(default="", env="GEMINI_API_KEYS")
    
    # APIs
    etherscan_api_key: str = Field(default="", env="ETHERSCAN_API_KEY")
    bscscan_api_key: str = Field(default="", env="BSCSCAN_API_KEY")
    polygonscan_api_key: str = Field(default="", env="POLYGONSCAN_API_KEY")
    arbiscan_api_key: str = Field(default="", env="ARBISCAN_API_KEY")
    basescan_api_key: str = Field(default="", env="BASESCAN_API_KEY")
    snowtrace_api_key: str = Field(default="", env="SNOWTRACE_API_KEY")
    optimismscan_api_key: str = Field(default="", env="OPTIMISMSCAN_API_KEY")
    
    # Datastores
    database_mongo_url: str = Field(default="", env="DATABASE_MONGO_URL")
    neo4j_uri: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(default="password", env="NEO4J_PASSWORD")
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    clickhouse_url: str = Field(default="", env="CLICKHOUSE_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore"

    def get_gemini_keys(self) -> List[str]:
        keys = [k.strip() for k in self.gemini_api_keys.replace('"', '').split(",") if k.strip() and not k.startswith("ROTATE")]
        return keys

    def get_api_key(self, chain: str) -> str:
        chain_map = {
            "ETHEREUM": self.etherscan_api_key,
            "BSC": self.bscscan_api_key,
            "POLYGON": self.polygonscan_api_key,
            "ARBITRUM": self.arbiscan_api_key,
            "BASE": self.basescan_api_key,
            "AVALANCHE": self.snowtrace_api_key,
            "OPTIMISM": self.optimismscan_api_key
        }
        key = chain_map.get(chain.upper(), "")
        return key if "ROTATE" not in key else ""

settings = NemesisConfig()
