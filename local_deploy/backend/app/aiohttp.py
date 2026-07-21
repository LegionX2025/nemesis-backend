# Aiohttp Polyfill for Cloudflare Workers (Pyodide)
# Maps aiohttp async calls to httpx natively.

import httpx
from contextlib import asynccontextmanager

class TCPConnector:
    def __init__(self, *args, **kwargs):
        pass

class ClientResponse:
    def __init__(self, response):
        self.response = response
        self.status = response.status_code
        self.status_code = response.status_code

    async def json(self):
        try:
            return self.response.json()
        except:
            return {}

    async def text(self):
        try:
            return self.response.text
        except:
            return ""

class ClientSession:
    def __init__(self, *args, **kwargs):
        headers = kwargs.get("headers", None)
        self.client = httpx.AsyncClient(headers=headers, verify=False, timeout=15.0)

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    @asynccontextmanager
    async def get(self, url, *args, **kwargs):
        kwargs.pop("ssl", None)
        timeout = kwargs.pop("timeout", None)
        if timeout:
            pass # Use httpx default instead
            
        try:
            res = await self.client.get(url, *args, **kwargs)
            yield ClientResponse(res)
        except Exception as e:
            class DummyRes:
                status_code = 500
                def json(self): return {}
                def text(self): return ""
            yield ClientResponse(DummyRes())

    @asynccontextmanager
    async def post(self, url, *args, **kwargs):
        kwargs.pop("ssl", None)
        timeout = kwargs.pop("timeout", None)
        try:
            res = await self.client.post(url, *args, **kwargs)
            yield ClientResponse(res)
        except Exception as e:
            class DummyRes:
                status_code = 500
                def json(self): return {}
                def text(self): return ""
            yield ClientResponse(DummyRes())

ClientError = Exception
