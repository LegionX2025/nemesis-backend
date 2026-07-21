-- Nemesis v2 D1 Schema Migration 0001
CREATE TABLE IF NOT EXISTS addresses (
  id TEXT PRIMARY KEY, address TEXT NOT NULL, chain TEXT DEFAULT 'ethereum',
  label TEXT, entity_name TEXT, entity_type TEXT,
  risk_score REAL DEFAULT 0, risk_level TEXT DEFAULT 'unknown',
  total_received REAL DEFAULT 0, total_sent REAL DEFAULT 0, balance REAL DEFAULT 0,
  tx_count INTEGER DEFAULT 0, is_contract INTEGER DEFAULT 0,
  contract_name TEXT, token_name TEXT, token_symbol TEXT,
  created_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_addr_unique ON addresses(address, chain);
CREATE INDEX IF NOT EXISTS idx_addr ON addresses(address);
CREATE INDEX IF NOT EXISTS idx_addr_label ON addresses(label);

CREATE TABLE IF NOT EXISTS transactions (
  id TEXT PRIMARY KEY, tx_hash TEXT NOT NULL, chain TEXT DEFAULT 'ethereum',
  from_address TEXT, to_address TEXT, value REAL DEFAULT 0,
  token_symbol TEXT, token_contract TEXT,
  block_number INTEGER, block_timestamp TEXT,
  gas_used REAL, gas_price REAL, status INTEGER DEFAULT 1,
  is_token_transfer INTEGER DEFAULT 0, input_data TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_tx_hash ON transactions(tx_hash);
CREATE INDEX IF NOT EXISTS idx_tx_from ON transactions(from_address);
CREATE INDEX IF NOT EXISTS idx_tx_to ON transactions(to_address);

CREATE TABLE IF NOT EXISTS transaction_graph (
  id TEXT PRIMARY KEY, source_address TEXT NOT NULL, target_address TEXT NOT NULL,
  tx_hash TEXT, chain TEXT DEFAULT 'ethereum',
  value REAL DEFAULT 0, token_symbol TEXT,
  direction TEXT DEFAULT 'out', depth INTEGER DEFAULT 0, hop INTEGER DEFAULT 0,
  block_timestamp TEXT, created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_graph_src ON transaction_graph(source_address);
CREATE INDEX IF NOT EXISTS idx_graph_tgt ON transaction_graph(target_address);

CREATE TABLE IF NOT EXISTS entities (
  id TEXT PRIMARY KEY, entity_name TEXT NOT NULL, entity_type TEXT,
  description TEXT, category TEXT,
  risk_score REAL DEFAULT 0, risk_level TEXT DEFAULT 'unknown',
  address_count INTEGER DEFAULT 0, total_volume REAL DEFAULT 0,
  first_seen TEXT, last_seen TEXT, source TEXT DEFAULT 'auto',
  created_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_entity_name ON entities(entity_name);

CREATE TABLE IF NOT EXISTS labels (
  id TEXT PRIMARY KEY, address TEXT NOT NULL, label TEXT NOT NULL,
  label_type TEXT, confidence REAL DEFAULT 0.5, source TEXT DEFAULT 'auto',
  chain TEXT DEFAULT 'ethereum', created_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_label_unique ON labels(address, label, chain);
CREATE INDEX IF NOT EXISTS idx_label_addr ON labels(address);

CREATE TABLE IF NOT EXISTS traces (
  id TEXT PRIMARY KEY, trace_id TEXT UNIQUE NOT NULL,
  root_address TEXT NOT NULL, chain TEXT DEFAULT 'ethereum',
  max_depth INTEGER DEFAULT 5, max_hops INTEGER DEFAULT 10, status TEXT DEFAULT 'pending',
  node_count INTEGER DEFAULT 0, edge_count INTEGER DEFAULT 0, total_volume REAL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')), completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_trace_root ON traces(root_address);

CREATE TABLE IF NOT EXISTS trace_nodes (
  id TEXT PRIMARY KEY, trace_id TEXT NOT NULL, address TEXT NOT NULL,
  depth INTEGER, label TEXT, entity_name TEXT, is_root INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_tn_trace ON trace_nodes(trace_id);
CREATE INDEX IF NOT EXISTS idx_tn_addr ON trace_nodes(address);

CREATE TABLE IF NOT EXISTS trace_edges (
  id TEXT PRIMARY KEY, trace_id TEXT NOT NULL,
  source_address TEXT NOT NULL, target_address TEXT NOT NULL,
  tx_hash TEXT, value REAL DEFAULT 0, token_symbol TEXT, depth INTEGER,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_te_trace ON trace_edges(trace_id);

CREATE TABLE IF NOT EXISTS api_cache (
  id TEXT PRIMARY KEY, cache_key TEXT UNIQUE NOT NULL, cache_value TEXT NOT NULL,
  source TEXT, expires_at TEXT, created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_cache_key ON api_cache(cache_key);

CREATE TABLE IF NOT EXISTS crawl_jobs (
  id TEXT PRIMARY KEY, job_id TEXT UNIQUE NOT NULL,
  address TEXT NOT NULL, chain TEXT DEFAULT 'ethereum',
  status TEXT DEFAULT 'pending', source TEXT, data TEXT, error TEXT,
  created_at TEXT DEFAULT (datetime('now')), completed_at TEXT
);
