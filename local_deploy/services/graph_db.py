import os
import logging
from neo4j import GraphDatabase, AsyncGraphDatabase

logger = logging.getLogger("Neo4jService")

class Neo4jService:
    def __init__(self):
        self.uri = os.environ.get("NEO4J_URI", "neo4j+s://89ea7d8f.databases.neo4j.io")
        self.username = os.environ.get("NEO4J_USERNAME", "89ea7d8f")
        self.password = os.environ.get("NEO4J_PASSWORD", "pMyRVGUtCLJCHBph0vR3FBVk5Ct1jkrThq-ApD2cJAA")
        self.database = os.environ.get("NEO4J_DATABASE", "neo4j")
        self.driver = None

    async def connect(self):
        try:
            self.driver = AsyncGraphDatabase.driver(self.uri, auth=(self.username, self.password))
            logger.info(f"[*] Connected to Neo4j Aura Instance: {self.uri}")
        except Exception as e:
            logger.error(f"[!] Failed to connect to Neo4j Aura: {e}")

    async def close(self):
        if self.driver:
            await self.driver.close()

    async def add_wallet_node(self, address: str, chain: str, tags: list):
        query = """
        MERGE (w:Wallet {address: $address, chain: $chain})
        SET w.tags = $tags, w.last_seen = timestamp()
        RETURN w
        """
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, address=address.lower(), chain=chain.upper(), tags=tags)
            return await result.single()

    async def add_transaction_edge(self, from_addr: str, to_addr: str, tx_hash: str, chain: str, value: float):
        query = """
        MERGE (sender:Wallet {address: $from_addr})
        MERGE (receiver:Wallet {address: $to_addr})
        MERGE (sender)-[t:TRANSACTED_WITH {tx_hash: $tx_hash, chain: $chain}]->(receiver)
        SET t.value = $value, t.timestamp = timestamp()
        RETURN t
        """
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, from_addr=from_addr.lower(), to_addr=to_addr.lower(), tx_hash=tx_hash, chain=chain.upper(), value=value)
            return await result.single()

    async def auto_save_entity(self, address: str, chain: str, entity_type: str, cluster: str, dom_tags: list, scores: dict, osint_evidence: list = None):
        """Automatically resolve, label, cluster and save wallets from Swarm/DOM/OSINT."""
        query = """
        MERGE (w:Wallet {address: $address})
        SET w.chain = $chain,
            w.entity_type = $entity_type,
            w.cluster = $cluster,
            w.dom_tags = $dom_tags,
            w.osint_evidence = $osint_evidence,
            w.confidence_score = $conf_score,
            w.threat_score = $threat_score,
            w.last_scraped = timestamp()
        RETURN w
        """
        conf_score = scores.get("Confidence_Score", 0) if scores else 0
        threat_score = scores.get("Threat_Score", 0) if scores else 0
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    query, 
                    address=address.lower(), 
                    chain=chain.upper(), 
                    entity_type=entity_type or "Unknown",
                    cluster=cluster or "Unclustered",
                    dom_tags=dom_tags or [],
                    osint_evidence=osint_evidence or [],
                    conf_score=conf_score,
                    threat_score=threat_score
                )
                logger.info(f"[*] Auto-Saved Hyper-Node: {address} ({cluster})")
                return await result.single()
        except Exception as e:
            logger.error(f"[!] Neo4j auto_save_entity failed for {address}: {e}")
            return None

    async def add_social_edge(self, address: str, platform: str, handle: str, confidence: float, evidence_url: str):
        query = """
        MERGE (w:Wallet {address: $address})
        MERGE (s:SocialProfile {handle: $handle, platform: $platform})
        MERGE (w)-[r:LINKED_TO {evidence_url: $evidence_url}]->(s)
        SET r.confidence = $confidence, r.timestamp = timestamp()
        RETURN r
        """
        async with self.driver.session(database=self.database) as session:
            await session.run(query, address=address.lower(), platform=platform, handle=handle, confidence=confidence, evidence_url=evidence_url)

    async def add_developer_edge(self, address: str, platform: str, repo: str, confidence: float, evidence_url: str):
        query = """
        MERGE (w:Wallet {address: $address})
        MERGE (d:DeveloperRepo {repo: $repo, platform: $platform})
        MERGE (w)-[r:CONTRIBUTED_TO {evidence_url: $evidence_url}]->(d)
        SET r.confidence = $confidence, r.timestamp = timestamp()
        RETURN r
        """
        async with self.driver.session(database=self.database) as session:
            await session.run(query, address=address.lower(), platform=platform, repo=repo, confidence=confidence, evidence_url=evidence_url)

    async def add_domain_edge(self, address: str, domain: str, confidence: float, evidence_url: str):
        query = """
        MERGE (w:Wallet {address: $address})
        MERGE (d:Domain {domain: $domain})
        MERGE (w)-[r:OWNS_DOMAIN {evidence_url: $evidence_url}]->(d)
        SET r.confidence = $confidence, r.timestamp = timestamp()
        RETURN r
        """
        async with self.driver.session(database=self.database) as session:
            await session.run(query, address=address.lower(), domain=domain, confidence=confidence, evidence_url=evidence_url)

# Singleton instance
neo4j_db = Neo4jService()
