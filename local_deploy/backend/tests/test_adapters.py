import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from app.adapters.account_adapter import AccountAdapter
from app.adapters.utxo_adapter import UTXOAdapter

@pytest.fixture
def account_adapter():
    return AccountAdapter(endpoints={})

@pytest.fixture
def utxo_adapter():
    return UTXOAdapter(api_keys={})

@pytest.mark.asyncio
async def test_account_adapter_solana(account_adapter):
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_resp = AsyncMock()
        mock_resp.json.return_value = {"result": {"transaction": "data"}}
        mock_post.return_value.__aenter__.return_value = mock_resp
        
        result = await account_adapter.fetch_transaction("SOLANA", "tx123")
        assert result == {"transaction": "data"}

@pytest.mark.asyncio
async def test_account_adapter_tron(account_adapter):
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_resp = AsyncMock()
        mock_resp.json.return_value = {"raw_data": "tron_data"}
        mock_post.return_value.__aenter__.return_value = mock_resp
        
        result = await account_adapter.fetch_transaction("TRON", "tx123")
        assert result == {"raw_data": "tron_data"}

@pytest.mark.asyncio
async def test_account_adapter_unsupported(account_adapter):
    result = await account_adapter.fetch_transaction("STELLAR", "tx123")
    assert "error" in result
    assert "not supported" in result["error"]

@pytest.mark.asyncio
async def test_utxo_adapter_bitcoin(utxo_adapter):
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json.return_value = {
            "txid": "test_tx",
            "fee": 1000,
            "vin": [{"prevout": {"scriptpubkey_address": "addr1", "value": 500000000}}],
            "vout": [{"scriptpubkey_address": "addr2", "value": 400000000}, 
                     {"scriptpubkey_address": "addr1", "value": 9999000}]
        }
        mock_get.return_value.__aenter__.return_value = mock_resp
        
        result = await utxo_adapter.fetch_utxo_graph("test_tx", "BITCOIN")
        
        assert result["txid"] == "test_tx"
        assert len(result["inputs"]) == 1
        assert len(result["outputs"]) == 2
        assert result["inputs"][0]["address"] == "addr1"
        assert result["inputs"][0]["value"] == 5.0  # 500M sats to BTC
        
        # Test change probability logic
        # addr1 is an input and also an output, so it should be detected as change (0.95 prob)
        assert result["change_probability"] == 0.95

@pytest.mark.asyncio
async def test_utxo_adapter_unsupported(utxo_adapter):
    result = await utxo_adapter.fetch_utxo_graph("test_tx", "KASPA")
    assert "error" in result
    assert "not fully implemented" in result["error"]
