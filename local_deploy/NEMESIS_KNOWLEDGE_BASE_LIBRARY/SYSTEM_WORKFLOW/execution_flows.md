# NEMESIS Platform Execution Flows

This document outlines the complete start-to-end execution flows for the three core pillars of the NEMESIS platform: **NEMESIS ID**, the **NEMESIS Tracer**, and the **BALIF Scenario Auto-Learning Engine**.

---

## 1. NEMESIS ID: Start-to-End Execution Flow

The NEMESIS ID is a synchronous, API-driven intelligence resolver that aggregates on-chain telemetry, OSINT, and machine learning heuristics into a single dossier.

```mermaid
sequenceDiagram
    participant User
    participant SPA as NEMESIS SPA (Frontend)
    participant API as FastAPI Backend (/api/intel)
    participant Chain as EVM Nodes (Etherscan/RPC)
    participant ML as ML Clustering Module
    participant Core as Core Engines (ACE, UGET, NLIE)

    User->>SPA: Enters Address & Clicks "RESOLVE"
    SPA->>SPA: Display AJAX Loader & Identify Network Prefix
    SPA->>API: GET /api/intel?wallet_address=0x...
    
    API->>Chain: Fetch live token transactions (offset=50)
    Chain-->>API: Raw Ledger Data
    
    API->>API: Build Asset Lifecycle & Detect Blackholes
    
    API->>Core: Pass Tx data to Core Engines
    Note right of API: ACE detects cyclical loops<br/>UGET resolves taxonomy flags<br/>NLIE generates CEX Subpoenas
    Core-->>API: Advanced Heuristics Output
    
    API->>ML: run_syndicate_clustering(formatted_ledger)
    ML-->>API: Syndicate Cluster ID (e.g. LONE WOLF)
    
    API->>API: Compile JSON Payload (Financials, Threat Tags)
    API-->>SPA: Return unified JSON Dossier
    
    SPA->>SPA: Hydrate DOM (Inject Ledger Stats, AI Content)
    SPA->>SPA: Render Vis.js Knowledge Graph
    SPA-->>User: Display Populated Bento-Box Dashboard
```

---

## 2. NEMESIS Tracer: Start-to-End Execution Flow

The NEMESIS Tracer is an asynchronous, WebSocket-driven application designed to stream real-time node discoveries to a physical, force-directed graph.

```mermaid
sequenceDiagram
    participant User
    participant React as Tracer Component (React)
    participant WS as WebSocket Endpoint (/api/antigravity/c2)
    participant Chain as EVM Nodes

    User->>React: Enters Target Address in Terminal
    React->>WS: WebSocket Connect
    WS-->>React: Handshake (Cluster: ONLINE)
    
    User->>React: Types: START_TRACE 0x...
    React->>WS: Send JSON: {action: "START_TRACE", target: "0x..."}
    
    WS->>React: Stream Event: AG_LOG "Initiating Swarm..."
    
    WS->>Chain: Fetch real transactions
    Chain-->>WS: Raw Tx Data
    
    loop Unrolling Graph
        WS->>WS: Wait (Simulated Breadth-First-Search delay)
        WS->>WS: Calculate Node Risk Score
        WS->>React: Send JSON: {type: "trace_update", data: {...}}
        React->>React: Update React State & Render Force Graph Physics
    end
    
    WS->>React: Stream Event: {type: "trace_complete"}
    React-->>User: Traversal finished, Graph stabilized.
```

---

## 3. BALIF Scenario Auto-Learning Engine: Execution Flow

This engine autonomously crawls the blockchain, seeded by known CEX wallets, to generate a massive local dataset (`BALIF-NEMESIS-Scenario-Library`) of laundering topologies. It streams live updates to a dedicated Light-Theme Web3GL Dashboard.

```mermaid
sequenceDiagram
    participant CEX as Known CEX Seeds (.env)
    participant BalifEngine as balif_engine.py (Python Backend)
    participant RPC as blockchain.nodes (RPCs)
    participant DB as MongoDB / Local FS
    participant SPA as Light-Theme Web3GL Dashboard

    Note over BalifEngine: Engine initialized on boot
    SPA->>BalifEngine: Connect WebSocket (/api/balif/stream)
    
    loop Infinite Auto-Learn Crawler
        BalifEngine->>CEX: Pull Target Seed (e.g. Binance Hot Wallet)
        BalifEngine->>RPC: Fetch 1st & 2nd Degree interactions
        RPC-->>BalifEngine: Raw Unclustered Tx Graph
        
        BalifEngine->>BalifEngine: Auto-Cluster & Label Entities
        BalifEngine->>BalifEngine: Detect Laundering Topology (e.g. Peel Chain)
        
        BalifEngine->>DB: Write to Local FS (e.g. ETH_0042.json)
        Note right of BalifEngine: Adheres to Schema validation
        
        BalifEngine->>SPA: WebSocket Emit: "New Scenario Learned" + Graph Edge
        SPA->>SPA: Render Web3GL Particle Edge
        SPA->>SPA: Update Live Ledger Feed
    end
```

### Detailed Breakdown:
1. **Engine Initialization**: The `balif_engine.py` runs as a persistent background daemon. It loads the database credentials, proxy endpoints, and known CEX seed wallets from the `.env` file.
2. **Auto-Clustering Crawler**: The engine iterates through the seed wallets. It hits the configured RPCs (`blockchain.nodes`) to pull the raw transaction graph. 
3. **Topology Detection**: It analyzes the 1st and 2nd-degree connections. If it detects a specific pattern (e.g., `Flash Loan -> Arbitrage -> Tornado Cash`), it tags this as a new scenario.
4. **Dataset Generation**: It formats the data into the strict `BALIF-NEMESIS` JSON schema (containing entities, graph edges, expected normalized events, and MITRE ATT&CK mapping). It saves this payload directly into the `BALIF-NEMESIS-Scenario-Library` directory structure.
5. **Real-Time Web3GL Streaming**: Simultaneously, the engine pushes a WebSocket event to the Light-Theme SPA Dashboard. The frontend intercepts this JSON payload and dynamically updates the Live Ledger Table and the Web3GL Knowledge Graph visualizer.
