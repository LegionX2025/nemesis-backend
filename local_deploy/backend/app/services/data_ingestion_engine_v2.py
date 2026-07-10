import os
import json
import asyncio
import logging

logger = logging.getLogger("NemesisIngestion")

class DataIngestionEngine:
    """Handles efficient, chunked reading of massive JSON datasets."""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    async def stream_json_array(self, filename: str, chunk_size: int = 100):
        """
        Streams a massive JSON array file efficiently without loading it all into memory.
        Assumes the file is formatted as a single JSON array or line-delimited JSON.
        Yields chunks of records to be broadcasted or processed.
        """
        file_path = os.path.join(self.data_dir, filename)
        if not os.path.exists(file_path):
            logger.error(f"Dataset {file_path} not found.")
            return

        logger.info(f"Initiating chunked stream for {filename}")
        
        # Check if it's JSONL or a single large JSON Array
        # We will do a simplistic line-by-line reading assuming the data
        # is somewhat cleanly formatted. For true massive JSON arrays without newlines,
        # a library like ijson would be required, but we will use an iterative approach here.
        
        try:
            # We'll use aiofiles if available, otherwise fallback to standard open
            import aiofiles
            
            chunk = []
            async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
                async for line in f:
                    line = line.strip()
                    if not line or line == "[" or line == "]" or line == "},":
                        continue
                        
                    # Basic cleanup for array elements
                    if line.endswith(","):
                        line = line[:-1]
                        
                    try:
                        record = json.loads(line)
                        chunk.append(record)
                        
                        if len(chunk) >= chunk_size:
                            yield chunk
                            chunk = []
                            await asyncio.sleep(0.01) # Yield control
                    except json.JSONDecodeError:
                        # Skip malformed lines in naive parsing
                        continue
                        
            # Yield remaining
            if chunk:
                yield chunk
                
        except ImportError:
            # Fallback to synchronous reading if aiofiles isn't installed
            with open(file_path, mode='r', encoding='utf-8') as f:
                chunk = []
                for line in f:
                    line = line.strip()
                    if not line or line == "[" or line == "]" or line == "},":
                        continue
                        
                    if line.endswith(","):
                        line = line[:-1]
                        
                    try:
                        record = json.loads(line)
                        chunk.append(record)
                        
                        if len(chunk) >= chunk_size:
                            yield chunk
                            chunk = []
                    except json.JSONDecodeError:
                        continue
                if chunk:
                    yield chunk

ingestion_engine = DataIngestionEngine(data_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data")))
