import httpx
from bs4 import BeautifulSoup
import asyncio
import os
import re

class AutoDynamicIndexer:
    def __init__(self):
        self.default_docs = [
            "https://developers.cloudflare.com/fundamentals/api/get-started/",
            "https://docs.render.com/api",
            "https://docs.github.com/en/rest"
        ]
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
