# Bitquery V2 API Docs | Bitquery Docs
Source: https://docs.bitquery.io/docs/category/graphql-api/

Bitquery V2 API Docs | Bitquery Docs
Skip to main content
New
Pricing plans starting at
$49/mo
Explore plans →
V2 · GraphQL · 40+ chains
Bitquery Streaming API docs.
Query and stream historical and real-time blockchain data through GraphQL, WebSocket, Kafka, MCP and cloud exports — one schema, many interfaces.
Search the docs — “OHLCV”, “Kafka”, “Pump.fun”…
⌘K
Getting started — 5 min
Starter queries
Live streams
Platform overview
first_query.graphql
one schema
# your first query — runs in the IDE
query
{
Solana
{
DEXTrades
(
limit
:
{count
:
3
}
)
{
Trade
{
Buy
{
Price Currency
{
Symbol
} } }
Dex
{
ProtocolName
}
}
}
}
Response
SOL/USDC
buy
$184.20
Raydium
BONK/SOL
sell
$0.0000241
Orca
WIF/USDC
buy
$2.14
Meteora
200 · 312ms
same fields → WS · Kafka · gRPC · MCP
GraphQL
WebSocket
Kafka
MCP
Solana gRPC
Cloud / S3
Your first query in 5 minutes.
Three steps from sign-up to streaming live data.
Step 01
Get your API key
Sign in to the GraphQL IDE — your access token is generated automatically, no setup.
Authorization:
Bearer
<your-token>
Open the IDE
→
Step 02
Write a query
Pick a chain and a dataset, shape the fields you want, and run it against live or historical data.
query
{ Solana { DEXTrades { … } } }
First query guide
→
Step 03
Stream it live
Swap
query
for
subscription
— the same fields now push over WebSocket in real time.
subscription
{ Solana { DEXTrades { … } } }
Live subscriptions
→
01
What you query
Data & metrics
The datasets you can query and stream — and the docs that show you how to build with each.
Token prices & OHLCV
Real-time & historical candles, price index methodology.
Open docs
→
DEX trades
Swaps, venues and USD notionals across 300+ DEXs.
Open docs
→
Transfers & wallet flows
Token movements and counterparties, decoded.
Open docs
→
Contract calls & traces
Decoded calls and internal transactions.
Open docs
→
Smart-contract events
Logs, protocols and aggregations by signature.
Open docs
→
NFTs & metadata
Collections, transfers and marketplace activity.
Open docs
→
Balances & holders
EVM & Solana holder sets and snapshots.
Open docs
→
Mempool & pending txs
Pre-confirmation activity, before the block lands.
Open docs
→
02
How you connect
Interfaces
One mental model: design the shape in GraphQL, then stream the same fields over whatever fits your stack.
# design the shape once…
subscription
{
EVM
{
DEXTrades
{
Trade
{ Buy { Price } }
}
}
}
…then deliver the
same fields
anywhere.
You never re-model your data to change transport. Author and validate in GraphQL, then point a different interface at the identical field selection — for live apps, scale-out pipelines, AI agents or your warehouse.
GraphQL
→
archives
WebSocket
→
live apps
Kafka
→
pipelines
MCP
→
agents
gRPC
→
HFT
Cloud
→
warehouses
GQL
GraphQL (HTTP)
Queries & archives. Shape the fields, run ad-hoc or backfill.
First query
→
WS
WebSocket
Live subscriptions in the browser, server-side filtered.
Subscriptions
→
KF
Kafka
Protobuf streams with replay for high-volume pipelines.
Kafka concepts
→
New
MCP
MCP server
Natural-language access for AI agents — ClickHouse-backed.
MCP docs
→
gRPC
Solana gRPC · CoreCast
Ultra-low-latency binary streaming for MEV & HFT.
CoreCast docs
→
S3
Cloud datasets
Parquet exports into Snowflake, BigQuery & warehouses.
Cloud docs
→
V1 and V2
use different GraphQL schemas and IDE flows. Compare them if you're migrating or reusing older queries.
V1 vs V2 API guide
→
03
Ship faster
Tools & explorers
Explore markets, debug queries, and browse demos and SDKs built on Bitquery.
DEXrabbit ↗
Real-time DEX analytics — tokens, pairs & market heatmaps.
Open tool
→
Explorer ↗
Search transactions, tokens & activity across chains.
Open tool
→
GraphQL IDE ↗
Author, test & share queries against the API.
Open tool
→
Other tools
Apps, dashboards, SDKs & agent skills built on Bitquery.
Browse directory
→
04
Coverage
Blockchains supported
40+ networks across V1 & V2 — EVM, Solana, Tron, Bitcoin and more, all on one schema.
Ethereum
Solana
BNB Chain
Base
Polygon
Arbitrum
OP
Optimism
Tron
₿
Bitcoin
+ 30 more · all chains
→
Who builds here
Built for your team
From discretionary traders to audit-ready reporting — pick a path and open the matching docs.
01
Traders & desks
Low-latency prices, OHLC, DEX flow, Pump.fun and the Solana tape.
Explore
→
02
Analysts & quants
Cross-chain aggregates, historical archives, repeatable GraphQL patterns.
Explore
→
03
Auditors & finance
Balances, transfers and settlement trails for proof and reconciliation.
Explore
→
04
Investigators & compliance
Wallet timelines, money-flow tracing, entity helpers, exportable datasets.
Explore
→
Popular right now
Trending documentation
High-traffic guides teams open first when integrating streaming market data.
Featured
Pump.fun API
Live memecoin trades, OHLCV, bonding curve and PumpSwap migration.
Open guide
→
Token prices & OHLCV
Multi-chain candles, 1s bars and price-index methodology.
Open guide
→
Polymarket on-chain
Prediction markets, wallets, PnL and streaming fills.
Open guide
→
Token holders
Top holders, concentration and balance snapshots.
Open guide
→
MCP for trading data
Natural language over ClickHouse — IDE & agent ready.
Open guide
→
Kafka streaming
Scale-out consumers across trading and EVM topics.
Open guide
→
Recipes
Use cases & how-tos
End-to-end examples: bots, dashboards, alerts and research pipelines.
Telegram trading bot
Polymarket alerts
Balance tracker
Mempool fee analysis
NFT analytics
Copy trading bot
TradingView OHLC feed
All how-to guides
→
Watch
Intro walkthrough — IDE & your first query
A short tour of the GraphQL IDE: find a dataset, shape a query, run it, and turn it into a live stream.
Start the 5-min guide
→
Open the IDE
intro_video.mp4 · ~3 min
Production scale
Trusted for on-chain data.
Exchanges, funds, protocols and investigators rely on Bitquery for trading, compliance and research — from ad-hoc GraphQL to Kafka-scale delivery.
Start with your first query
→
Enterprise & sales
Platform overview