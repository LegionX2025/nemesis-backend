import os
import asyncio
from services.auto_indexer import indexer

def append_to_env():
    env_path = ".env"
    key_line = "BITQUERY_V2_TOKEN=ory_at_OPk5pzBLSLdISNOBfUKLJpAXsXzSheuz86ltIh8VIp0.UmAM9swbcKeJaGMNS4hG_b1frXR2x1gFeToAthjVC5A"
    
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            if key_line in f.read():
                print("BITQUERY_V2_TOKEN is already in .env!")
                return
    
    with open(env_path, "a") as f:
        f.write(f"\n{key_line}\n")
    print(f"Successfully added BITQUERY_V2_TOKEN to {env_path}")

async def run_indexer():
    print("Running Auto-Indexer for Bitquery API Documentation...")
    # This uses the new default_docs array which includes Bitquery API docs
    result = await indexer.fetch_and_index(None)
    print("Indexer Result:")
    print(result)

if __name__ == "__main__":
    append_to_env()
    asyncio.run(run_indexer())
