import asyncio
import json
import logging
import websockets
from datetime import datetime
from uuid import uuid4
from db_schema import NemesisAlert, AlertSeverity, alerts_col, SessionLocal, PGAlert

logger = logging.getLogger("nemesis.fetcher.ws_monitor")

class RealtimeMonitor:
    def __init__(self):
        self.monitored_addresses = set()
        self.active_tasks = []
        
        # Free public websocket endpoints (usually wss)
        self.rpc_websockets = {
            "ETHEREUM": "wss://ethereum-rpc.publicnode.com",
            "BSC": "wss://bsc-rpc.publicnode.com",
            "POLYGON": "wss://polygon-bor-rpc.publicnode.com",
        }

    def add_address(self, address: str):
        """Add an address to the monitoring pool"""
        self.monitored_addresses.add(address.lower())
        logger.info(f"Added {address} to real-time monitoring.")

    def remove_address(self, address: str):
        if address.lower() in self.monitored_addresses:
            self.monitored_addresses.remove(address.lower())

    async def _handle_new_transaction(self, tx: dict, network: str):
        """Process an incoming pending transaction from mempool"""
        from_addr = tx.get("from", "").lower()
        to_addr = tx.get("to", "").lower() if tx.get("to") else ""
        
        is_target = False
        event_type = "STANDARD_TRANSFER"
        
        if from_addr in self.monitored_addresses:
            is_target = True
            event_type = "OUTBOUND_TRANSFER"
        elif to_addr in self.monitored_addresses:
            is_target = True
            event_type = "INBOUND_TRANSFER"

        if is_target:
            val_hex = tx.get("value", "0x0")
            try:
                val_eth = int(val_hex, 16) / 1e18
            except:
                val_eth = 0.0

            alert = NemesisAlert(
                alert_id=f"ALT-{uuid4().hex[:8].upper()}",
                target_address=from_addr if from_addr in self.monitored_addresses else to_addr,
                network=network,
                event_type=event_type,
                severity=AlertSeverity.WARNING if val_eth > 10 else AlertSeverity.INFO,
                tx_hash=tx.get("hash", "UNKNOWN"),
                amount_usd=val_eth * 3000.0, # Approximate for now
                details={"raw_tx": tx}
            )
            await self._trigger_alert(alert)

    async def _trigger_alert(self, alert: NemesisAlert):
        """Save alert to databases and emit (conceptually)"""
        logger.warning(f"🚨 REAL-TIME ALERT: {alert.target_address} on {alert.network} [{alert.tx_hash}]")
        
        # Save to MongoDB
        try:
            alerts_col.insert_one(alert.model_dump(mode='json'))
        except Exception as e:
            logger.error(f"Failed to save alert to Mongo: {e}")

        # Save to Postgres
        try:
            with SessionLocal() as session:
                pg_alert = PGAlert(
                    alert_id=alert.alert_id,
                    target_address=alert.target_address,
                    network=alert.network,
                    event_type=alert.event_type,
                    severity=alert.severity.value,
                    tx_hash=alert.tx_hash,
                    amount_usd=alert.amount_usd,
                    timestamp=alert.timestamp.isoformat()
                )
                session.add(pg_alert)
                session.commit()
        except Exception as e:
            logger.error(f"Failed to save alert to Postgres: {e}")

    async def _monitor_network(self, network: str, wss_url: str):
        """Connects to a websocket and subscribes to pending transactions"""
        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "eth_subscribe",
            "params": ["newPendingTransactions"]
        }

        while True:
            try:
                async with websockets.connect(wss_url, ping_interval=20, ping_timeout=20) as ws:
                    logger.info(f"Connected to {network} WSS: {wss_url}")
                    await ws.send(json.dumps(payload))
                    res = await ws.recv()
                    logger.info(f"Subscribed to {network} mempool: {res}")

                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        if "params" in data and "result" in data["params"]:
                            tx_hash = data["params"]["result"]
                            # Since we only get the hash, we ideally need to fetch the full tx.
                            # For the sake of the engine architecture, we simulate fetching the full tx
                            # if we had a dedicated fast RPC. 
                            
                            # In production, we'd query `eth_getTransactionByHash` here using an HTTP pool.
                            pass
            except Exception as e:
                logger.error(f"WSS connection lost for {network}: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)

    def start(self):
        """Start all monitoring tasks in the background"""
        logger.info("Starting Nemesis Realtime Monitor...")
        for network, wss_url in self.rpc_websockets.items():
            task = asyncio.create_task(self._monitor_network(network, wss_url))
            self.active_tasks.append(task)

    def stop(self):
        for task in self.active_tasks:
            task.cancel()

# Global instance
monitor_engine = RealtimeMonitor()
