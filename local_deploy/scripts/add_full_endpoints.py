import os
import re

def update_deployer():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    deployer_path = os.path.join(root_dir, 'deployer.py')
    
    with open(deployer_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_endpoints = """
      // Nemesis ID - Profile
      else if (path.startsWith('/api/nemesis_id/profile/')) {
        const address = path.split('/').pop();
        const chain = url.searchParams.get('chain') || 'ethereum';
        const [balance, txs, entity] = await Promise.all([
            fetchBalance(env, address, chain),
            fetchTransactions(env, address, chain, 50),
            scrapeEntityLabel(env, address, chain)
        ]);
        let totalIn = 0; let totalOut = 0;
        txs.forEach(tx => {
            const val = parseFloat(tx.value) || 0;
            if (tx.to && tx.to.toLowerCase() === address.toLowerCase()) totalIn += val;
            if (tx.from && tx.from.toLowerCase() === address.toLowerCase()) totalOut += val;
        });
        response = json({
            address, chain, balance,
            firstActivity: txs.length ? txs[txs.length-1].timestamp : null,
            lastActivity: txs.length ? txs[0].timestamp : null,
            totalTransactions: txs.length,
            totalInboundNative: totalIn,
            totalOutboundNative: totalOut,
            entity: entity || { label: 'Unknown', type: 'unknown' }
        });
      }
      // Nemesis ID - AML
      else if (path.startsWith('/api/nemesis_id/aml/')) {
        const address = path.split('/').pop();
        const chain = url.searchParams.get('chain') || 'ethereum';
        const entity = await scrapeEntityLabel(env, address, chain);
        const riskScore = entity?.type === 'malicious' ? 0.95 : entity?.type === 'mixer' ? 0.8 : entity?.type === 'exchange' ? 0.2 : 0.1;
        response = json({
            address, riskScore,
            riskLevel: riskScore > 0.7 ? 'CRITICAL' : riskScore > 0.4 ? 'ELEVATED' : 'LOW',
            flags: entity?.type ? [entity.type] : [],
            lastScreened: Date.now()
        });
      }
      // Nemesis ID - TX History
      else if (path.startsWith('/api/nemesis_id/tx_history/')) {
        const address = path.split('/').pop();
        const chain = url.searchParams.get('chain') || 'ethereum';
        const txs = await fetchTransactions(env, address, chain, 100);
        response = json({ address, chain, transactions: txs });
      }
      // Nemesis ID - GeoRisk
      else if (path.startsWith('/api/nemesis_id/georisk/')) {
        const address = path.split('/').pop();
        response = json({
            address,
            primaryRegion: 'Unknown',
            jurisdictionRisk: 'Medium',
            nodes: []
        });
      }
      // Nemesis ID - AI Insights
      else if (path.startsWith('/api/nemesis_id/ai_insights/')) {
        const address = path.split('/').pop();
        const chain = url.searchParams.get('chain') || 'ethereum';
        const prompt = `Analyze blockchain entity ${address} on ${chain}. Provide a 3-sentence threat intelligence summary.`;
        const ai = await aiAnalyze(env, prompt);
        response = json({ address, insights: ai.text, model: ai.model });
      }
      // OSINT
      else if (path.startsWith('/api/osint/')) {
        const address = path.split('/').pop();
        const chain = url.searchParams.get('chain') || 'ethereum';
        const entity = await scrapeEntityLabel(env, address, chain);
        response = json({ address, osint: entity });
      }
"""
    
    # Check if we already injected this to avoid duplication
    if 'Nemesis ID - Profile' not in content:
        # We will inject this right before the // Bitquery Proxy line
        content = content.replace('      // Bitquery Proxy', new_endpoints + '      // Bitquery Proxy')
        
        # Also update the 404 endpoint list to include these
        endpoints_regex = r"(endpoints: \['[^\]]+)\]"
        content = re.sub(endpoints_regex, r"\1, '/api/nemesis_id/*', '/api/osint/*']", content)
        
        with open(deployer_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("[*] Successfully injected all full API endpoints into deployer.py")
    else:
        print("[*] API Endpoints already exist in deployer.py")

if __name__ == "__main__":
    update_deployer()
