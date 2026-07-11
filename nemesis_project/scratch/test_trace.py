import asyncio
import sys
import os

# Add the project root to sys.path so we can import services
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.trace_engine import TraceEngine

async def main():
    print("Testing TraceEngine...")
    e = TraceEngine("test1")
    # Using the BTC address from the user's prompt
    e.setup(["bc1qpa8n0a5ckt7wkdw3cn8eklsz3z0kn89knme5a9"], 1600000)
    await e.run()
    print("Ledger length:", len(e.ledger))
    
    for entry in e.ledger[:5]:
        print(entry)

if __name__ == "__main__":
    asyncio.run(main())
