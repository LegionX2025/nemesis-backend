import React, { useEffect, useRef, useState } from 'react';
import Graph from 'graphology';
import forceAtlas2 from 'graphology-layout-forceatlas2';
import Sigma from 'sigma';
import { motion } from 'framer-motion';
import { Settings, Shield, ShieldAlert, Link as LinkIcon, Database, CheckCircle, Activity } from 'lucide-react';

export default function App() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [sigmaInstance, setSigmaInstance] = useState<Sigma | null>(null);
  const [graph] = useState(() => new Graph());
  const [nodes, setNodes] = useState<any[]>([]);
  const [edges, setEdges] = useState<any[]>([]);

  useEffect(() => {
    if (!containerRef.current) return;

    // 1. Initialize Graphology
    // Mock Data for Testing
    graph.addNode('n1', { x: 0, y: 0, size: 20, color: 'transparent', label: 'Binance', type: 'exchange', value: '$865,737.47', address: 'rZJ3YPCB9Vi67Fep5...', kyc: true, asset: 'BNB' });
    graph.addNode('n2', { x: 5, y: 5, size: 15, color: 'transparent', label: 'Unknown Wallet', type: 'unknown', value: '$0.00', address: 'ra58pa...3urq', kyc: false, asset: 'TRX' });
    
    graph.addEdge('n1', 'n2', { size: 2, color: '#334155', amount: '$432,868.736', asset: 'USDT', network: 'TRC20', type: 'outflow' });

    // Official Icon Mapping Dictionary
    const getIcon = (type: string, asset: string) => {
      if (type === 'exchange') return <div className="w-12 h-12 bg-yellow-500 rounded-full flex items-center justify-center text-slate-900 font-bold text-xl">{asset}</div>;
      if (type === 'contract') return <div className="w-12 h-12 bg-purple-500 rounded-full flex items-center justify-center text-white"><Database className="w-6 h-6" /></div>;
      if (type === 'bridge') return <div className="w-12 h-12 bg-cyan-500 rounded-full flex items-center justify-center text-white"><LinkIcon className="w-6 h-6" /></div>;
      if (type === 'mixer') return <div className="w-12 h-12 bg-red-500 rounded-full flex items-center justify-center text-white"><Activity className="w-6 h-6" /></div>;
      // Default Unknown
      return <div className="w-12 h-12 bg-slate-700 rounded-full flex items-center justify-center text-slate-400"><Shield className="w-6 h-6" /></div>;
    };
    const sigma = new Sigma(graph, containerRef.current, {
      renderLabels: false,
      renderEdgeLabels: false,
      zoomToSizeRatioFunction: (ratio) => ratio,
    });

    setSigmaInstance(sigma);

    // Layout
    forceAtlas2.assign(graph, { iterations: 100, settings: { gravity: 10 } });

    // Camera listener for Overlays
    sigma.getCamera().on('updated', () => {
      updateOverlays();
    });
    
    const updateOverlays = () => {
      const nodePositions: any[] = [];
      graph.forEachNode((node, attrs) => {
        const viewportPos = sigma.graphToViewport(attrs);
        nodePositions.push({ id: node, ...attrs, ...viewportPos });
      });
      setNodes(nodePositions);

      const edgePositions: any[] = [];
      graph.forEachEdge((edge, attrs, source, target) => {
        const sourcePos = sigma.graphToViewport(graph.getNodeAttributes(source));
        const targetPos = sigma.graphToViewport(graph.getNodeAttributes(target));
        // Midpoint
        const midX = (sourcePos.x + targetPos.x) / 2;
        const midY = (sourcePos.y + targetPos.y) / 2;
        edgePositions.push({ id: edge, ...attrs, x: midX, y: midY });
      });
      setEdges(edgePositions);
    };

    updateOverlays();

    return () => {
      sigma.kill();
    };
  }, []);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100vh', backgroundColor: '#0f172a', overflow: 'hidden' }}>
      {/* Layer 1: Canvas / Sigma WebGL */}
      <div ref={containerRef} style={{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0 }} />

      {/* Layer 2: React HTML Overlays */}
      <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
        
        {/* Render Edges Metadata (Transaction Cards) */}
        {edges.map(edge => (
          <motion.div
            key={edge.id}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${edge.x}px, ${edge.y}px)`,
              pointerEvents: 'auto'
            }}
          >
            <div className="bg-slate-800/90 border border-slate-700 rounded-lg p-2 flex flex-col items-center shadow-xl backdrop-blur-md">
              <span className="text-emerald-400 font-bold text-xs uppercase tracking-widest">{edge.asset} • {edge.type}</span>
              <span className="text-white font-mono text-sm">⬇ {edge.amount}</span>
              <span className="text-slate-400 text-[10px] uppercase">{edge.network}</span>
            </div>
          </motion.div>
        ))}

        {/* Render Nodes (Wallet Cards) */}
        {nodes.map(node => (
          <div
            key={node.id}
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${node.x}px, ${node.y}px)`,
              pointerEvents: 'auto'
            }}
          >
            {/* Enterprise Node Card */}
            <div className={`
              group w-56 bg-slate-900 border rounded-xl overflow-hidden shadow-2xl transition-all duration-300
              ${node.type === 'exchange' ? 'border-blue-500/50 hover:border-blue-400 hover:shadow-blue-500/20' : 'border-slate-700 hover:border-slate-500'}
            `}>
              
              {/* Header Badge */}
              {node.kyc && (
                <div className="bg-emerald-500/20 text-emerald-400 text-[10px] uppercase tracking-wider font-bold text-center py-1 border-b border-emerald-500/20">
                  <CheckCircle className="inline-block w-3 h-3 mr-1 -mt-0.5" /> Verified Entity
                </div>
              )}

              {/* Logo Box */}
              <div className="p-4 flex justify-center bg-slate-800/50">
                {getIcon(node.type, node.asset)}
              </div>

              {/* Metadata */}
              <div className="p-3 text-center border-t border-slate-800">
                <div className="text-xl font-mono text-white mb-1">{node.value}</div>
                <div className="text-sm font-bold text-slate-200 uppercase tracking-wide">{node.label}</div>
                <div className="text-xs text-slate-500 uppercase mb-2">{node.type}</div>
                <div className="text-xs font-mono text-slate-400 bg-slate-950 rounded py-1 px-2 border border-slate-800 truncate">
                  {node.address}
                </div>
              </div>
              
              {/* Footer Tags */}
              <div className="bg-slate-950 p-2 flex justify-center gap-2 border-t border-slate-800 text-[10px] text-slate-400 uppercase tracking-wider">
                <span>TRON</span> • <span>{node.type === 'exchange' ? 'Hot Wallet' : 'External'}</span>
              </div>

            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
