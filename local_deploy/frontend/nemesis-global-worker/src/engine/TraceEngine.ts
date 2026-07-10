export interface TraceEdge {
    from_address: string;
    to_address: string;
    tx_hash: string;
    chain: string;
    asset: string;
    amount: string;
    usd_value?: number;
    edge_type: string;
    timestamp: number;
    confidence: string;
    is_terminal: boolean;
}

export class TraceEngine {
    private env: any;
    
    constructor(env: any) {
        this.env = env;
    }

    async initiateTrace(seeds: string[], depth: number, traceId: string): Promise<void> {
        console.log(`[TraceEngine] Starting trace ${traceId} with seeds: ${seeds.join(', ')}`);
        
        // 1. Initialize Trace in D1
        await this.env.DB.prepare(
            `INSERT INTO traces (trace_id, seeds) VALUES (?, ?)`
        ).bind(traceId, JSON.stringify(seeds)).run();

        // 2. Begin recursive tracing
        for (const seed of seeds) {
            await this.traceWallet(seed, 'ETH', depth, traceId); // simplified: assumes ETH for demonstration
        }

        console.log(`[TraceEngine] Trace ${traceId} completed.`);
    }

    private async traceWallet(wallet: string, chain: string, depth: number, traceId: string) {
        if (depth <= 0) return;

        console.log(`[TraceEngine] Tracing wallet ${wallet} on ${chain}, depth ${depth}`);
        
        try {
            // Use Etherscan API as fallback for ETH
            const etherscanKey = this.env.ETHERSCAN_API_KEY || 'freekey';
            const url = `https://api.etherscan.io/api?module=account&action=txlist&address=${wallet}&startblock=0&endblock=99999999&page=1&offset=50&sort=desc&apikey=${etherscanKey}`;
            
            const resp = await fetch(url);
            const data: any = await resp.json();

            if (data.status === '1' && data.result) {
                const txs = data.result;
                const edges: TraceEdge[] = [];

                for (const tx of txs) {
                    if (tx.value === "0" && tx.input === "0x") continue; // Skip zero value / no data
                    
                    const amount = (parseFloat(tx.value) / 1e18).toFixed(4); // Wei to ETH
                    if (parseFloat(amount) < 0.0001) continue; // Noise filter

                    const edge: TraceEdge = {
                        from_address: tx.from,
                        to_address: tx.to,
                        tx_hash: tx.hash,
                        chain: chain,
                        asset: 'ETH',
                        amount: amount,
                        edge_type: 'transfer',
                        timestamp: parseInt(tx.timeStamp) * 1000,
                        confidence: 'high',
                        is_terminal: depth <= 1
                    };
                    
                    edges.push(edge);
                    
                    // Insert Edge into D1
                    await this.env.DB.prepare(
                        `INSERT INTO trace_edges (trace_id, from_address, to_address, tx_hash, chain, asset, amount, edge_type, timestamp, confidence, is_terminal) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
                    ).bind(
                        traceId, edge.from_address, edge.to_address, edge.tx_hash, edge.chain, 
                        edge.asset, edge.amount, edge.edge_type, edge.timestamp, edge.confidence, edge.is_terminal ? 1 : 0
                    ).run();

                    // Realtime Broadcast via RealtimeManager DO
                    await this.broadcastToRealtimeDO(traceId, edge);

                    // Recurse downstream
                    if (tx.from.toLowerCase() === wallet.toLowerCase()) {
                        await this.traceWallet(tx.to, chain, depth - 1, traceId);
                    }
                }
                
                // Update trace count
                await this.env.DB.prepare(
                    `UPDATE traces SET tx_count = tx_count + ? WHERE trace_id = ?`
                ).bind(edges.length, traceId).run();
            }
        } catch (error) {
            console.error(`[TraceEngine] Error fetching txs for ${wallet}:`, error);
        }
    }

    private async broadcastToRealtimeDO(traceId: string, edge: TraceEdge) {
        try {
            const id = this.env.REALTIME_MANAGER.idFromName('nemesis_global_socket');
            const doObj = this.env.REALTIME_MANAGER.get(id);
            await doObj.fetch('http://do/internal/broadcast', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: 'trace_node', traceId, data: edge })
            });
        } catch (error) {
            console.error(`[TraceEngine] Error broadcasting to DO:`, error);
        }
    }
}
