// --- Graph Force Layout Hook (mini physics engine) ---
function useForceLayout(
  nodes: { id: string; type: string; label: string; properties?: any }[],
  edges: { source: string; target: string }[],
  width: number,
  height: number
) {
  const [positions, setPositions] = React.useState<Map<string, { x: number; y: number }>>(new Map());

  React.useEffect(() => {
    if (nodes.length === 0) { setPositions(new Map()); return; }

    const pos = new Map<string, { x: number; y: number }>();
    nodes.forEach((n, i) => {
      const angle = (i / nodes.length) * 2 * Math.PI;
      const r = Math.min(width, height) * 0.32;
      pos.set(n.id, {
        x: width / 2 + r * Math.cos(angle) + (Math.random() - 0.5) * 40,
        y: height / 2 + r * Math.sin(angle) + (Math.random() - 0.5) * 40,
      });
    });

    const k = Math.sqrt((width * height) / (nodes.length || 1));
    const iterations = 120;
    const padding = 40;
    // Temperature proportional to canvas diagonal so nodes actually spread for large graphs
    const initTemp = Math.sqrt(width * width + height * height) * 0.15;

    for (let iter = 0; iter < iterations; iter++) {
      const temp = initTemp * (1 - iter / iterations);

      // Initialize displacement map
      const disp = new Map<string, { x: number; y: number }>();
      nodes.forEach(n => disp.set(n.id, { x: 0, y: 0 }));

      // Repulsion forces between all node pairs
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const idI = nodes[i].id;
          const idJ = nodes[j].id;
          const pi = pos.get(idI)!;
          const pj = pos.get(idJ)!;
          const dx = pi.x - pj.x;
          const dy = pi.y - pj.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 0.1;
          const force = (k * k) / dist;
          const fx = (dx / dist) * force * 0.05;
          const fy = (dy / dist) * force * 0.05;

          const dispI = disp.get(idI)!;
          const dispJ = disp.get(idJ)!;
          disp.set(idI, { x: dispI.x + fx, y: dispI.y + fy });
          disp.set(idJ, { x: dispJ.x - fx, y: dispJ.y - fy });
        }
      }

      // Attraction forces along edges
      edges.forEach(e => {
        const ps = pos.get(e.source);
        const pt = pos.get(e.target);
        if (!ps || !pt) return;
        const dx = pt.x - ps.x;
        const dy = pt.y - ps.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 0.1;
        const force = (dist * dist) / k * 0.05;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;

        const dispSrc = disp.get(e.source);
        const dispTgt = disp.get(e.target);
        if (dispSrc && dispTgt) {
          disp.set(e.source, { x: dispSrc.x - fx, y: dispSrc.y - fy });
          disp.set(e.target, { x: dispTgt.x + fx, y: dispTgt.y + fy });
        }
      });

      // Update positions with temperature capping
      nodes.forEach(n => {
        const p = pos.get(n.id)!;
        const d = disp.get(n.id) || { x: 0, y: 0 };
        const dLen = Math.sqrt(d.x * d.x + d.y * d.y) || 0.1;
        const cappedLen = Math.min(dLen, temp);
        
        let newX = p.x + (d.x / dLen) * cappedLen;
        let newY = p.y + (d.y / dLen) * cappedLen;

        newX = Math.max(padding, Math.min(width - padding, newX));
        newY = Math.max(padding, Math.min(height - padding, newY));

        pos.set(n.id, { x: newX, y: newY });
      });
    }

    setPositions(new Map(pos));
  }, [nodes, edges, width, height]);

  return positions;
}

// --- Graph Explorer Page ---
export const GraphExplorerPage: React.FC = () => {
  const { graphData, isFetchingGraph, stats, queryGraph, cleanGraph, isCleaning, fetchAssociates } = useGraph();
  const { addToast } = useUiStore();
  const svgRef = useRef<SVGSVGElement>(null);

  const [queryMode, setQueryMode] = useState<'all' | 'node' | 'date' | 'crime'>('all');
  const [nameInput, setNameInput] = useState('');
  const [dateInput, setDateInput] = useState('');
  const [crimeInput, setCrimeInput] = useState('');
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [associates, setAssociates] = useState<any[]>([]);
  const [isFetchingAssociates, setIsFetchingAssociates] = useState(false);

  const SVG_W = 700;
  const SVG_H = 500;
  const [viewBox, setViewBox] = useState({ x: 0, y: 0, w: SVG_W, h: SVG_H });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ mx: 0, my: 0, vx: 0, vy: 0 });

  const nodes = graphData?.nodes || [];
  const edges = graphData?.edges || [];
  const positions = useForceLayout(nodes, edges, SVG_W, SVG_H);

  useEffect(() => {
    queryGraph({ queryType: 'all' }).catch(() => {});
  }, []);

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (queryMode === 'all') {
        await queryGraph({ queryType: 'all' });
      } else if (queryMode === 'node') {
        if (!nameInput.trim()) { addToast('Enter a suspect name to query.', 'warning'); return; }
        await queryGraph({ queryType: 'node', centerNodeId: nameInput.trim() });
      } else if (queryMode === 'date') {
        if (!dateInput.trim()) { addToast('Enter a date in DD.MM.YYYY format.', 'warning'); return; }
        await queryGraph({ queryType: 'date', date: dateInput.trim() });
      } else if (queryMode === 'crime') {
        if (!crimeInput.trim()) { addToast('Enter a crime keyword.', 'warning'); return; }
        await queryGraph({ queryType: 'crime', crimeKeyword: crimeInput.trim() });
      }
      setSelectedNode(null);
      setAssociates([]);
    } catch (e: any) {
      addToast(`Query failed: ${e.message}`, 'error');
    }
  };

  const handleNodeClick = async (node: any) => {
    setSelectedNode(node);
    if (node.type === 'individual') {
      setIsFetchingAssociates(true);
      try {
        const result = await fetchAssociates(node.label || node.id);
        setAssociates(result);
      } catch { setAssociates([]); }
      finally { setIsFetchingAssociates(false); }
    } else {
      setAssociates([]);
    }
  };

  const handleNodeDblClick = async (node: any) => {
    try {
      await queryGraph({ queryType: 'node', centerNodeId: node.id, depth: 2 });
      setSelectedNode(node);
    } catch (e: any) {
      addToast(`Subgraph query failed: ${e.message}`, 'error');
    }
  };

  const handleCleanGraph = async () => {
    if (!window.confirm('Clean junk nodes from the graph database?')) return;
    try {
      const response = await cleanGraph();
      if (response.success) {
        addToast(`Removed ${response.data.removedCount} invalid nodes.`, 'success');
        await queryGraph({ queryType: 'all' });
      }
    } catch (e: any) {
      addToast(`Failed: ${e.message}`, 'error');
    }
  };

  const onSvgMouseDown = (e: React.MouseEvent<SVGSVGElement>) => {
    const tag = (e.target as SVGElement).tagName;
    if (tag === 'svg' || tag === 'rect') {
      setIsPanning(true);
      setPanStart({ mx: e.clientX, my: e.clientY, vx: viewBox.x, vy: viewBox.y });
    }
  };
  const onSvgMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!isPanning) return;
    const scaleX = viewBox.w / (svgRef.current?.clientWidth || SVG_W);
    const scaleY = viewBox.h / (svgRef.current?.clientHeight || SVG_H);
    setViewBox(v => ({
      ...v,
      x: panStart.vx - (e.clientX - panStart.mx) * scaleX,
      y: panStart.vy - (e.clientY - panStart.my) * scaleY,
    }));
  };
  const onSvgMouseUp = () => setIsPanning(false);
  const onSvgWheel = (e: React.WheelEvent<SVGSVGElement>) => {
    e.preventDefault();
    const factor = e.deltaY > 0 ? 1.12 : 0.88;
    setViewBox(v => {
      const newW = Math.max(200, Math.min(SVG_W * 2, v.w * factor));
      const newH = Math.max(150, Math.min(SVG_H * 2, v.h * factor));
      return { x: v.x + (v.w - newW) / 2, y: v.y + (v.h - newH) / 2, w: newW, h: newH };
    });
  };

  const NODE_COLORS: Record<string, { fill: string; stroke: string }> = {
    individual:   { fill: '#f43f5e', stroke: '#fb7185' },
    crime:        { fill: '#6366f1', stroke: '#818cf8' },
    record:       { fill: '#f59e0b', stroke: '#fcd34d' },
    case:         { fill: '#0ea5e9', stroke: '#38bdf8' },
    organization: { fill: '#10b981', stroke: '#34d399' },
    unknown:      { fill: '#64748b', stroke: '#94a3b8' },
  };
  const getColor = (type: string) => NODE_COLORS[type] || NODE_COLORS.unknown;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Intelligence Network Explorer</h1>
          <p className="text-sm text-slate-500">Query Neo4j graph by suspect name, crime keyword, or date. Double-click a node to drill into its subgraph.</p>
        </div>
        <button
          onClick={handleCleanGraph}
          disabled={isCleaning}
          className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-bold bg-rose-50 text-rose-600 hover:bg-rose-100 rounded-xl border border-rose-100 transition-colors shrink-0 shadow-sm"
        >
          <Trash2 size={13} /> Clean Junk Nodes
        </button>
      </div>

      {/* Query bar */}
      <form onSubmit={handleQuery} className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
        <div className="flex flex-wrap gap-3 items-end">
          {/* Mode buttons */}
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Query Mode</label>
            <div className="flex rounded-xl overflow-hidden border border-slate-200 text-xs font-bold divide-x divide-slate-200">
              {(['all','node','date','crime'] as const).map(m => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setQueryMode(m)}
                  className={`px-3 py-2 capitalize transition-colors ${queryMode === m ? 'bg-slate-900 text-white' : 'bg-white text-slate-500 hover:bg-slate-50'}`}
                >
                  {m === 'all' ? 'All Nodes' : m === 'node' ? 'By Name' : m === 'date' ? 'By Date' : 'By Crime'}
                </button>
              ))}
            </div>
          </div>

          {queryMode === 'node' && (
            <div className="flex-1 min-w-[180px] space-y-1">
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Suspect Name / Node ID</label>
              <Input value={nameInput} onChange={e => setNameInput(e.target.value)} placeholder="e.g. Mohammed Rafi" className="bg-slate-50 border-slate-200 text-sm" />
            </div>
          )}
          {queryMode === 'date' && (
            <div className="flex-1 min-w-[180px] space-y-1">
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Report Date (DD.MM.YYYY)</label>
              <div className="relative">
                <Input value={dateInput} onChange={e => setDateInput(e.target.value)} placeholder="06.06.2026" className="bg-slate-50 border-slate-200 text-sm pl-9" />
                <Calendar className="absolute left-3 top-2.5 text-slate-400" size={15} />
              </div>
            </div>
          )}
          {queryMode === 'crime' && (
            <div className="flex-1 min-w-[180px] space-y-1">
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Crime / Incident Keyword</label>
              <Input value={crimeInput} onChange={e => setCrimeInput(e.target.value)} placeholder="e.g. maoist, robbery, IED" className="bg-slate-50 border-slate-200 text-sm" />
            </div>
          )}

          <Button
            type="submit"
            variant="primary"
            isLoading={isFetchingGraph}
            className="bg-slate-900 hover:bg-slate-800 text-white font-bold rounded-xl px-5 py-2 text-sm flex items-center gap-1.5 self-end"
          >
            <Search size={14} /> Run Query
          </Button>
        </div>
      </form>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-5">
        {/* Left: Stats + Legend */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 space-y-3">
            <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-100 pb-2">DB Overview</h3>
            {[
              { label: 'Total Nodes', val: stats?.total_nodes },
              { label: 'Edges', val: stats?.total_edges },
              { label: 'Suspects', val: stats?.individual_nodes },
              { label: 'Crime Events', val: stats?.crime_nodes },
              { label: 'Records', val: stats?.record_nodes },
              { label: 'Cases', val: stats?.case_nodes },
            ].map(row => (
              <div key={row.label} className="flex justify-between items-center text-xs">
                <span className="text-slate-500 font-medium">{row.label}</span>
                <span className="font-bold text-slate-800 font-mono">{row.val ?? '—'}</span>
              </div>
            ))}
          </div>
          <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 space-y-2">
            <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-100 pb-2">Node Legend</h3>
            {Object.entries(NODE_COLORS).filter(([k]) => k !== 'unknown').map(([type, col]) => (
              <div key={type} className="flex items-center gap-2 text-xs font-medium text-slate-600 capitalize">
                <div className="w-3 h-3 rounded-full shrink-0" style={{ background: col.fill }} />
                {type}
              </div>
            ))}
          </div>
          <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 text-xs space-y-1.5">
            <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-100 pb-2">Visible Graph</h3>
            <div className="flex justify-between"><span className="text-slate-500">Nodes shown</span><span className="font-bold font-mono text-slate-800">{nodes.length}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Edges shown</span><span className="font-bold font-mono text-slate-800">{edges.length}</span></div>
          </div>
        </div>

        {/* Center: SVG Canvas */}
        <div className="lg:col-span-2 bg-slate-950 rounded-2xl border border-slate-800 overflow-hidden relative shadow-xl" style={{ minHeight: 500 }}>
          <div className="absolute top-3 left-3 z-10 text-[9px] text-slate-500 font-semibold uppercase tracking-widest leading-relaxed pointer-events-none">
            <div>Scroll: zoom · Drag: pan</div>
            <div>Click: inspect · Dbl-click: drill down</div>
          </div>

          {isFetchingGraph ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-400 z-10">
              <RefreshCw size={28} className="animate-spin text-cyan-400 mb-3" />
              <span className="text-xs font-bold tracking-wide">Traversing Neo4j network paths...</span>
            </div>
          ) : nodes.length === 0 ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-8 gap-3">
              <Database size={36} className="text-slate-700" />
              <div className="space-y-1">
                <p className="text-slate-400 text-sm font-bold">No graph data returned</p>
                <p className="text-slate-600 text-xs">Try "All Nodes" or refine your search criteria.</p>
              </div>
            </div>
          ) : (
            <svg
              ref={svgRef}
              className="w-full h-full select-none"
              viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`}
              style={{ cursor: isPanning ? 'grabbing' : 'grab', minHeight: 500 }}
              onMouseDown={onSvgMouseDown}
              onMouseMove={onSvgMouseMove}
              onMouseUp={onSvgMouseUp}
              onMouseLeave={onSvgMouseUp}
              onWheel={onSvgWheel}
            >
              <defs>
                <pattern id="neo-grid" width="30" height="30" patternUnits="userSpaceOnUse">
                  <path d="M 30 0 L 0 0 0 30" fill="none" stroke="rgba(255,255,255,0.025)" strokeWidth="0.5"/>
                </pattern>
                <marker id="arrowhead" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                  <path d="M 0 0 L 6 3 L 0 6 z" fill="rgba(34,211,238,0.35)" />
                </marker>
              </defs>
              <rect x={-5000} y={-5000} width={15000} height={15000} fill="url(#neo-grid)" />

              {/* Edges */}
              {edges.map((edge, idx) => {
                const src = positions.get(edge.source);
                const tgt = positions.get(edge.target);
                if (!src || !tgt) return null;
                const mx = (src.x + tgt.x) / 2;
                const my = (src.y + tgt.y) / 2;
                return (
                  <g key={edge.id || idx}>
                    <line
                      x1={src.x} y1={src.y} x2={tgt.x} y2={tgt.y}
                      stroke="rgba(34,211,238,0.18)"
                      strokeWidth={1.2}
                      markerEnd="url(#arrowhead)"
                    />
                    <text x={mx} y={my - 4} fill="rgba(34,211,238,0.4)" fontSize={7} fontWeight="600" textAnchor="middle" style={{ pointerEvents: 'none' }}>
                      {String(edge.type || '').replace(/_/g, ' ')}
                    </text>
                  </g>
                );
              })}

              {/* Nodes */}
              {nodes.map(n => {
                const pos = positions.get(n.id);
                if (!pos) return null;
                const color = getColor(n.type);
                const isSelected = selectedNode?.id === n.id;
                const r = n.type === 'record' ? 10 : n.type === 'individual' ? 15 : 12;
                const label = (n.label || n.id || '').toString().slice(0, 20);

                return (
                  <g
                    key={n.id}
                    style={{ cursor: 'pointer' }}
                    onClick={ev => { ev.stopPropagation(); handleNodeClick(n); }}
                    onDoubleClick={ev => { ev.stopPropagation(); handleNodeDblClick(n); }}
                  >
                    {isSelected && (
                      <circle cx={pos.x} cy={pos.y} r={r + 7} fill="none" stroke="rgba(34,211,238,0.5)" strokeWidth={1.5} strokeDasharray="4 2" />
                    )}
                    {isSelected && (
                      <circle cx={pos.x} cy={pos.y} r={r + 4} fill={color.fill} opacity={0.15} />
                    )}
                    <circle
                      cx={pos.x} cy={pos.y} r={r}
                      fill={color.fill}
                      stroke={color.stroke}
                      strokeWidth={isSelected ? 2.5 : 1.5}
                      style={{ filter: isSelected ? `drop-shadow(0 0 8px ${color.fill})` : `drop-shadow(0 0 3px ${color.fill}66)` }}
                    />
                    <text x={pos.x} y={pos.y + 4.5} fill="white" fontSize={9} fontWeight="900" textAnchor="middle" style={{ pointerEvents: 'none' }}>
                      {(n.type || 'U')[0].toUpperCase()}
                    </text>
                    <text x={pos.x} y={pos.y + r + 12} fill="rgba(255,255,255,0.7)" fontSize={8} fontWeight="600" textAnchor="middle" style={{ pointerEvents: 'none' }}>
                      {label}
                    </text>
                  </g>
                );
              })}
            </svg>
          )}

          <div className="absolute bottom-3 right-3 text-[9px] text-cyan-500 font-bold tracking-widest uppercase bg-slate-900/80 px-2.5 py-1 border border-slate-800 rounded-lg">
            NEO4J · {nodes.length} nodes · {edges.length} edges
          </div>
        </div>

        {/* Right: Inspector + GNN */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 space-y-3">
            <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-100 pb-2 flex items-center gap-1.5">
              <Activity size={12} className="text-cyan-600" /> Node Inspector
            </h3>
            {!selectedNode ? (
              <p className="text-xs italic text-slate-400 text-center py-4">Click a node on the graph to inspect its properties.</p>
            ) : (
              <div className="space-y-2 text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full shrink-0" style={{ background: getColor(selectedNode.type).fill }} />
                  <span className="font-bold text-slate-800 truncate">{selectedNode.label || selectedNode.id}</span>
                </div>
                <Badge variant={selectedNode.type === 'individual' ? 'red' : selectedNode.type === 'crime' ? 'blue' : 'gray'}>
                  {selectedNode.type}
                </Badge>
                <div className="bg-slate-50 rounded-xl p-2.5 space-y-2 max-h-52 overflow-y-auto">
                  {Object.entries(selectedNode.properties || {})
                    .filter(([k]) => !['node_id'].includes(k))
                    .slice(0, 14)
                    .map(([k, v]) => (
                      <div key={k} className="flex flex-col gap-0.5">
                        <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">{k.replace(/_/g, ' ')}</span>
                        <span className="font-medium text-slate-700 break-words text-[11px]">{String(v || '').slice(0, 140)}</span>
                      </div>
                    ))}
                </div>
                <button
                  onClick={() => handleNodeDblClick(selectedNode)}
                  className="w-full py-1.5 text-xs font-bold text-cyan-700 bg-cyan-50 hover:bg-cyan-100 rounded-lg border border-cyan-100 transition-colors"
                >
                  Drill into subgraph →
                </button>
              </div>
            )}
          </div>

          <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 space-y-3">
            <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-100 pb-2 flex items-center gap-1.5">
              <Cpu size={12} className="text-cyan-600" /> GNN Link Prediction
            </h3>
            {isFetchingAssociates ? (
              <div className="flex flex-col items-center py-4 text-slate-400 gap-2">
                <RefreshCw size={16} className="animate-spin text-cyan-600" />
                <span className="text-[10px] font-semibold">Running GCN model...</span>
              </div>
            ) : !selectedNode || selectedNode.type !== 'individual' ? (
              <p className="text-xs italic text-slate-400 text-center py-3">Select a suspect (individual) node to see predicted ties.</p>
            ) : associates.length === 0 ? (
              <p className="text-xs italic text-slate-400 text-center py-3">No hidden links predicted for this suspect.</p>
            ) : (
              <div className="space-y-2 max-h-56 overflow-y-auto">
                {associates.map((item: any, idx: number) => (
                  <div key={idx} className="bg-slate-50 p-2.5 rounded-xl border border-slate-100 text-xs flex justify-between items-center gap-2">
                    <div className="min-w-0">
                      <span className="font-bold text-slate-800 block truncate">{item.name}</span>
                      <span className="text-[10px] text-slate-400 font-semibold uppercase">
                        {item.hasEdge ? 'Direct Tie' : 'Predicted (GNN)'}
                      </span>
                    </div>
                    <Badge variant={item.similarity > 0.75 ? 'red' : 'blue'}>
                      {(item.similarity * 100).toFixed(0)}%
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
