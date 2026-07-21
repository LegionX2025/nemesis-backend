import os
import asyncio
import aiohttp
import logging
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("UNIVERSAL_API_INDEXER")

try:
    import motor.motor_asyncio
    MOTOR_AVAILABLE = True
except ImportError:
    MOTOR_AVAILABLE = False
    logger.error("Motor is not installed. Please install motor (`pip install motor`).")

# Mapping of .env key prefixes to their official documentation URLs
PROVIDER_DOC_MAP = {
    "ETHERSCAN": "https://docs.etherscan.io/",
    "BSCSCAN": "https://docs.bscscan.com/",
    "POLYGONSCAN": "https://docs.polygonscan.com/",
    "ARBISCAN": "https://docs.arbiscan.io/",
    "BASESCAN": "https://docs.basescan.org/",
    "TRONSCAN": "https://developers.tron.network/reference/",
    "SHODAN": "https://developer.shodan.io/api",
    "CENSYS": "https://search.censys.io/api",
    "HUNTER": "https://hunter.io/api-documentation",
    "GEMINI": "https://ai.google.dev/api",
    "AIML": "https://aimlapi.com/docs",
    "BITQUERY": "https://docs.bitquery.io/docs/intro/",
    "TATUM": "https://apidoc.tatum.io/",
    "INFURA": "https://docs.infura.io/api",
    "GETBLOCK": "https://getblock.io/docs/"
}

class UniversalAPICrawler:
    def __init__(self, env_path: str = "../.env"):
        self.env_path = env_path
        self.providers = []
        self.crawled_data = []
        
        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.db_name = "nemesis_osint"
        self.collection_name = "intel_api_docs"
        self.collection = None

    def detect_providers(self):
        """Parses the .env file to identify active API providers."""
        if not os.path.exists(self.env_path):
            logger.error(f".env file not found at {self.env_path}")
            # Fallback to defaults for testing
            self.providers = [("BITQUERY", PROVIDER_DOC_MAP["BITQUERY"])]
            return

        with open(self.env_path, 'r', encoding='utf-8') as f:
            env_content = f.read()

        detected = set()
        for line in env_content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            if "=" in line:
                key = line.split("=")[0].strip().upper()
                # Check if any mapped provider prefix is in the key
                for prefix, url in PROVIDER_DOC_MAP.items():
                    if prefix in key:
                        detected.add((prefix, url))
        
        self.providers = list(detected)
        logger.info(f"Detected {len(self.providers)} active API providers from .env: {[p[0] for p in self.providers]}")

    async def init_db(self):
        if not MOTOR_AVAILABLE:
            return False
        try:
            client = motor.motor_asyncio.AsyncIOMotorClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            self.collection = client[self.db_name][self.collection_name]
            await self.collection.create_index("url", unique=True)
            await self.collection.create_index("provider")
            logger.info(f"Connected to MongoDB: {self.mongo_uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False

    async def crawl_provider(self, session: aiohttp.ClientSession, provider_name: str, start_url: str):
        """Crawls a specific provider's documentation."""
        visited = set()
        queue = [start_url]
        base_domain = urlparse(start_url).netloc
        
        # Limit the number of pages per provider to avoid crawling the entire internet
        max_pages = 50 
        pages_crawled = 0
        
        logger.info(f"Starting crawl for {provider_name} at {start_url}")

        while queue and pages_crawled < max_pages:
            current_url = queue.pop(0)
            
            if current_url in visited:
                continue
            visited.add(current_url)
            
            try:
                async with session.get(current_url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract content
                        main_content = soup.find('main') or soup.find('article') or soup.find('body')
                        if main_content:
                            title = soup.find('title')
                            title_text = title.text if title else "Unknown Title"
                            text_content = main_content.get_text(separator='\n', strip=True)
                            
                            # Extremely simple regex to find API endpoint signatures (e.g. GET /api/v1/user)
                            endpoints = re.findall(r'(GET|POST|PUT|DELETE|PATCH)\s+/[a-zA-Z0-9_/-]+', text_content)
                            
                            doc_entry = {
                                "provider": provider_name,
                                "url": current_url,
                                "title": title_text,
                                "content": text_content[:15000], # Cap size to prevent massive BSON objects
                                "detected_endpoints": list(set(endpoints)),
                                "crawled_at": datetime.datetime.utcnow().isoformat()
                            }
                            self.crawled_data.append(doc_entry)
                            pages_crawled += 1
                        
                        # Find more links
                        for a_tag in soup.find_all('a', href=True):
                            href = a_tag['href']
                            full_url = urljoin(current_url, href).split('#')[0]
                            parsed = urlparse(full_url)
                            
                            # Filter: Same domain, and path must imply documentation or api
                            if parsed.netloc == base_domain:
                                path_lower = parsed.path.lower()
                                if any(x in path_lower for x in ['/api', '/docs', '/reference', '/developers']):
                                    if full_url not in visited and full_url not in queue:
                                        queue.append(full_url)
            except Exception as e:
                logger.debug(f"Error fetching {current_url}: {e}")
                
            await asyncio.sleep(0.5) # Throttle

    async def run(self):
        self.detect_providers()
        db_ok = await self.init_db()
        
        if not self.providers:
            logger.warning("No providers detected.")
            return

        async with aiohttp.ClientSession() as session:
            tasks = []
            for provider_name, url in self.providers:
                tasks.append(self.crawl_provider(session, provider_name, url))
            
            # Run all provider crawls concurrently
            await asyncio.gather(*tasks)
            
        logger.info(f"Finished crawling. Extracted {len(self.crawled_data)} total documentation pages.")
        
        if db_ok and self.crawled_data:
            success = 0
            for doc in self.crawled_data:
                try:
                    await self.collection.update_one(
                        {"url": doc["url"]},
                        {"$set": doc},
                        upsert=True
                    )
                    success += 1
                except Exception as e:
                    logger.error(f"MongoDB Upsert Error: {e}")
            logger.info(f"Successfully upserted {success} documents to DB.")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Adjust path if running from scripts directory directly
    env_path = ".env" if os.path.exists(".env") else "../.env"
    crawler = UniversalAPICrawler(env_path=env_path)
    asyncio.run(crawler.run())
