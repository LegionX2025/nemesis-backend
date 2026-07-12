import asyncio
import logging
import sys
import os
from dotenv import load_dotenv

# Load env variables before initializing Nemesis modules
load_dotenv()

from test_trace import test_trace

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Nemesis_v32_SafeRunner")

async def main():
    logger.info("Initializing NEMESIS v32 Autonomous Multi-Chain Intelligence OS...")
    
    # Check locks and instances
    lock_file = ".nemesis_v32.lock"
    if os.path.exists(lock_file):
        logger.warning("Another instance might be running. Ignoring lock for multi-instance runner.")
        
    try:
        with open(lock_file, "w") as f:
            f.write(str(os.getpid()))
            
        logger.info("Databases are initialized within test_trace()...")
        
        logger.info("Spawning Safe Runner Tracing Instance...")
        await test_trace()
        
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    finally:
        if os.path.exists(lock_file):
            os.remove(lock_file)
        logger.info("NEMESIS v32 OS Exited cleanly.")

if __name__ == "__main__":
    asyncio.run(main())
