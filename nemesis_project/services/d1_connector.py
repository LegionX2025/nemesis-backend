import logging

logger = logging.getLogger(__name__)

class CloudflareD1Connector:
    """
    Connects to the native Cloudflare D1 Serverless SQL databases.
    
    When running in the Cloudflare Worker V8 Isolate (Pyodide), D1 databases 
    are exposed as JavaScript objects attached to the `env` argument.
    """
    def __init__(self, env):
        self.env = env
        
        # We mapped these to three unique bindings in wrangler.toml
        self.audit_db = getattr(env, "DB", None)
        self.primary_db = getattr(env, "NEMESIS_DB_PRIMARY", None)
        self.secondary_db = getattr(env, "NEMESIS_DB_SECONDARY", None)
        
        if not self.audit_db:
            logger.warning("D1 Binding 'DB' (nemesis_audit_db) not found.")
        if not self.primary_db:
            logger.warning("D1 Binding 'NEMESIS_DB_PRIMARY' (nemesis) not found.")
        if not self.secondary_db:
            logger.warning("D1 Binding 'NEMESIS_DB_SECONDARY' (nemesis-db) not found.")

    async def execute_query(self, database_binding: str, query: str, params: list = None):
        """
        Executes a SQL query on a specific D1 database binding.
        
        Usage:
            await d1.execute_query("NEMESIS_DB_PRIMARY", "SELECT * FROM users WHERE id = ?", [1])
        """
        db = getattr(self, database_binding.lower(), None)
        if not db:
            db = getattr(self.env, database_binding, None)
            
        if not db:
            raise ValueError(f"D1 Database binding '{database_binding}' is not available in this environment.")
            
        try:
            # Prepare the D1 statement (Requires Pyodide async/await interop)
            statement = db.prepare(query)
            
            if params:
                # D1 .bind() expects spread arguments, but Pyodide proxies Python lists to JS arrays 
                # For multiple parameters, you might need to use *params or apply in JS.
                # The Pyodide wrapper usually handles this cleanly.
                statement = statement.bind(*params)
                
            # Execute and return all rows
            result = await statement.all()
            
            return {
                "success": result.success,
                "results": result.results.to_py() if hasattr(result.results, "to_py") else result.results,
                "error": result.error
            }
            
        except Exception as e:
            logger.error(f"D1 Query Execution Failed on {database_binding}: {e}")
            return {"success": False, "error": str(e), "results": []}

# Global instance initialized during worker boot
d1_engine = None

def init_d1(env):
    global d1_engine
    d1_engine = CloudflareD1Connector(env)
    return d1_engine
