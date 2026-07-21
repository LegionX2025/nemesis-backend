"""
NEMESIS v3.1 Enterprise
Model Context Protocol (MCP) Client
Connects the NEMESIS AI Fabric directly to external MCP Servers (e.g. Bitquery).
"""

import logging
import json
import httpx
from typing import Dict, Any, Optional

logger = logging.getLogger("AIFabric.MCPClient")

class MCPClient:
    def __init__(self, mcp_url: str, token: Optional[str] = None):
        self.mcp_url = mcp_url.rstrip("/")
        self.token = token
        
    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
        
    async def list_tools(self) -> Dict[str, Any]:
        """Fetches the list of available tools from the MCP server."""
        try:
            url = f"{self.mcp_url}/tools/list"
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to list MCP tools at {self.mcp_url}: {e}")
            return {}

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a specific MCP tool dynamically.
        Uses Streamable HTTP if supported, fallback to standard POST.
        """
        try:
            url = f"{self.mcp_url}/tools/{tool_name}/execute"
            async with httpx.AsyncClient() as client:
                # Appending token in URL as fallback if OAuth isn't used
                req_url = url
                if self.token and "Bearer" not in self._get_headers().get("Authorization", ""):
                    req_url = f"{url}?token={self.token}"
                    
                response = await client.post(req_url, json={"arguments": arguments}, headers=self._get_headers())
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to execute MCP tool '{tool_name}': {e}")
            return {"error": str(e)}
            
    async def execute_prompt(self, prompt_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a ready-made MCP Prompt workflow (e.g. money_flow, risk_screen).
        """
        try:
            url = f"{self.mcp_url}/prompts/{prompt_name}/execute"
            async with httpx.AsyncClient() as client:
                req_url = url
                if self.token and "Bearer" not in self._get_headers().get("Authorization", ""):
                    req_url = f"{url}?token={self.token}"
                    
                response = await client.post(req_url, json={"arguments": arguments}, headers=self._get_headers())
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to execute MCP prompt '{prompt_name}': {e}")
            return {"error": str(e)}

# Initialize global Bitquery MCP Singleton
# Token is usually fetched from env or OAuth flow.
bitquery_mcp = MCPClient(mcp_url="https://mcp.bitquery.io")
