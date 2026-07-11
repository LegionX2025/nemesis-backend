import httpx
from bs4 import BeautifulSoup
import asyncio
import os
import re

from dotenv import load_dotenv
load_dotenv()

class AutoDynamicIndexer:
    def __init__(self):
        self.default_docs = [
            "https://developers.cloudflare.com/fundamentals/api/get-started/",
            "https://docs.render.com/api",
            "https://docs.github.com/en/rest"
        ]
        
        API_DOC_MAP = {
            "ETHERSCAN_API_KEY": "https://docs.etherscan.io/",
            "OKLINK_API_KEY": "https://www.oklink.com/docs/en/",
            "TATUM_API_KEY": "https://apidoc.tatum.io/",
            "ANKR_API_KEY": "https://www.ankr.com/docs/advanced-api/",
            "INFURA_API_KEY": "https://docs.infura.io/api/",
            "BITQUERY_API_TOKEN": "https://docs.bitquery.io/docs/category/graphql-api/",
            "BITQUERY_V2_TOKEN": "https://docs.bitquery.io/docs/category/graphql-api/",
            "GETBLOCK_ETH_KEY": "https://getblock.io/docs/"
        }
        
        for key, doc_url in API_DOC_MAP.items():
            if os.environ.get(key) and doc_url not in self.default_docs:
                self.default_docs.append(doc_url)
        self.kb_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge_base")
        os.makedirs(self.kb_dir, exist_ok=True)

    async def fetch_and_index(self, url: str) -> dict:
        urls_to_index = [url] if url else self.default_docs
        results = []
        
        async with httpx.AsyncClient() as client:
            for u in urls_to_index:
                try:
                    response = await client.get(u, follow_redirects=True, timeout=15.0)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    title = soup.title.string if soup.title else "Unknown Title"
                    
                    # Extract text content
                    # Remove scripts and styles
                    for script in soup(["script", "style", "nav", "footer"]):
                        script.extract()
                    
                    text = soup.get_text(separator='\n')
                    # Clean up empty lines
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = '\n'.join(chunk for chunk in chunks if chunk)
                    
                    # Save to local file for LLM reference
                    safe_title = re.sub(r'[^a-zA-Z0-9]', '_', title).lower()
                    filepath = os.path.join(self.kb_dir, f"{safe_title}.md")
                    
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(f"# {title}\n")
                        f.write(f"Source: {u}\n\n")
                        f.write(text)
                        
                    results.append(f"Indexed [{title}] -> saved to knowledge_base/{safe_title}.md")
                except Exception as e:
                    results.append(f"Failed to index {u}: {str(e)}")
                    
        return {
            "status": "success",
            "message": " | ".join(results)
        }

indexer = AutoDynamicIndexer()

if __name__ == "__main__":
    print("Running Auto-Dynamic Indexer directly...")
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else None
    result = asyncio.run(indexer.fetch_and_index(target))
    print(result)
