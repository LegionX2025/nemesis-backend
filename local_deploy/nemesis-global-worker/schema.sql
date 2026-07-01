-- Cloudflare D1 Schema for Nemesis OmniChain Engine

CREATE TABLE IF NOT EXISTS traces (
    trace_id TEXT PRIMARY KEY,
    seeds TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    tx_count INTEGER DEFAULT 0,
    narrative TEXT
);

CREATE TABLE IF NOT EXISTS trace_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id TEXT NOT NULL,
    from_address TEXT NOT NULL,
    to_address TEXT NOT NULL,
    tx_hash TEXT NOT NULL,
    chain TEXT NOT NULL,
    asset TEXT NOT NULL,
    amount TEXT NOT NULL,
    usd_value REAL DEFAULT 0,
    edge_type TEXT NOT NULL,
    timestamp DATETIME,
    confidence TEXT,
    is_terminal BOOLEAN DEFAULT 0,
    FOREIGN KEY (trace_id) REFERENCES traces(trace_id)
);

CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY, -- Composite: address_chain
    address TEXT NOT NULL,
    chain TEXT NOT NULL,
    type TEXT DEFAULT 'wallet',
    labels TEXT,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    tx_hash TEXT PRIMARY KEY,
    chain TEXT NOT NULL,
    block_time DATETIME,
    from_address TEXT NOT NULL,
    to_address TEXT NOT NULL,
    value TEXT NOT NULL,
    parsed_data TEXT
);

CREATE TABLE IF NOT EXISTS bridge_links (
    lock_tx TEXT PRIMARY KEY,
    asset TEXT,
    chain TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_trace_edges ON trace_edges(trace_id, from_address, to_address);
CREATE INDEX IF NOT EXISTS idx_entities_address ON entities(address);
CREATE INDEX IF NOT EXISTS idx_tx_hash ON transactions(tx_hash);
