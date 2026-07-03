DROP TABLE IF EXISTS audit_logs;
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    target_wallet TEXT,
    actor_ip TEXT,
    severity TEXT DEFAULT 'INFO',
    details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS cached_traces;
CREATE TABLE cached_traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seed_wallet TEXT NOT NULL,
    chain TEXT NOT NULL,
    trace_data JSON,
    cached_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME
);
