import os
import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BITQUERY_DOC_INDEXER")

# Safely import motor (Async MongoDB)
try:
    import motor.motor_asyncio
    MOTOR_AVAILABLE = True
except ImportError:
    MOTOR_AVAILABLE = False
    logger.error("Motor is not installed. Please install motor (`pip install motor`).")

class BitqueryDocCrawler:
    def __init__(self, start_url: str):
        self.start_url = start_url
        self.base_domain = urlparse(start_url).netloc
        self.visited_urls = set()
        self.urls_to_visit = [start_url]
        self.docs = []
        
        # MongoDB Connection
        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.db_name = "nemesis_osint"
        self.collection_name = "intel_bitquery_docs"
        self.client = None
        self.db = None
        self.collection = None

    async def init_db(self):
        if not MOTOR_AVAILABLE:
            return False
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            
            # Create a unique index on the URL to prevent duplicates
            await self.collection.create_index("url", unique=True)
            logger.info(f"Connected to MongoDB: {self.mongo_uri} | DB: {self.db_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False

    async def extract_links_and_content(self, html: str, current_url: str):
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract Content (Bitquery docs are typically in a <main> or <article> tag)
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='theme-doc-markdown')
        
        if main_content:
            # Clean up the HTML to plain text (very basic markdown-like stripping)
            title_element = soup.find('title')
            title = title_element.text if title_element else "Unknown Title"
            
            text_content = main_content.get_text(separator='\n', strip=True)
            
            self.docs.append({
                "url": current_url,
                "title": title,
                "content": text_content,
                "crawled_at": datetime.datetime.utcnow().isoformat()
            })
            
        # Extract Links
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(current_url, href)
            parsed_full = urlparse(full_url)
            
            # Only follow links within the docs domain and docs path to prevent spidering the whole internet
            if parsed_full.netloc == self.base_domain and "/docs/" in parsed_full.path:
                # Remove URL fragments (#) so we don't index the same page multiple times
                clean_url = full_url.split('#')[0]
                if clean_url not in self.visited_urls and clean_url not in self.urls_to_visit:
                    self.urls_to_visit.append(clean_url)

    async def crawl(self):
        logger.info(f"Starting BFS crawl at {self.start_url}")
        
        async with aiohttp.ClientSession() as session:
            while self.urls_to_visit:
                current_url = self.urls_to_visit.pop(0)
                
                if current_url in self.visited_urls:
                    continue
                    
                self.visited_urls.add(current_url)
                logger.info(f"Crawling: {current_url} | Queue size: {len(self.urls_to_visit)}")
                
                try:
                    async with session.get(current_url, timeout=10) as response:
                        if response.status == 200:
                            html = await response.text()
                            await self.extract_links_and_content(html, current_url)
                        else:
                            logger.warning(f"Failed to fetch {current_url}: HTTP {response.status}")
                except Exception as e:
                    logger.error(f"Error crawling {current_url}: {e}")
                
                # Throttle requests to avoid Cloudflare blocks (2 requests per second)
                await asyncio.sleep(0.5)

    async def upsert_to_mongo(self):
        if not self.collection:
            logger.error("MongoDB not initialized. Cannot save docs.")
            return

        logger.info(f"Upserting {len(self.docs)} documents to MongoDB...")
        
        success_count = 0
        for doc in self.docs:
            try:
                await self.collection.update_one(
                    {"url": doc["url"]},
                    {"$set": doc},
                    upsert=True
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to upsert doc {doc['url']}: {e}")
                
        logger.info(f"Successfully upserted {success_count}/{len(self.docs)} documents.")

async def run_indexer():
    start_url = "https://docs.bitquery.io/docs/intro/"
    crawler = BitqueryDocCrawler(start_url)
    
    db_ok = await crawler.init_db()
    if not db_ok:
        logger.warning("Proceeding without MongoDB. Data will not be saved.")
        
    await crawler.crawl()
    
    if db_ok:
        await crawler.upsert_to_mongo()
        
    logger.info("Indexing complete.")

if __name__ == "__main__":
    # Fix for Windows event loops
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(run_indexer())
