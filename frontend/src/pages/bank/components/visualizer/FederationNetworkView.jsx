import React, { useState, useEffect, useCallback, useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';

import {
  Network,
  ShieldCheck,
  ShieldAlert,
  Server,
  Database,
  ArrowRight,
  Play,
  RotateCw,
  Clock,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Eye,
  X,
  Layers,
  Radio,
  Lock,
  Pause,
} from 'lucide-react';

import {
  fetchVisualizerFederationTopology,
  simulateVisualizerFederationExchange,
} from '../../../../api/auth';

// Custom Branch Node Component
const BranchNodeComponent = ({ data }) => {
  const isSelected = data.isSelected;
  return (
    <div
      className={`px-5 py-4 rounded-2xl bg-[#0b152e] border transition-all duration-300 shadow-xl cursor-pointer min-w-[220px] ${
        isSelected
          ? 'border-cyan-400 ring-2 ring-cyan-500/30 shadow-cyan-500/20'
          : 'border-slate-700/80 hover:border-slate-500'
      }`}
    >
      <div className="flex items-center justify-between mb-2.5">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Server className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-white tracking-tight">{data.branch_name}</h4>
            <span className="text-[10px] font-mono font-bold text-cyan-400">{data.branch_id}</span>
          </div>
        </div>
        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
          {data.branch_status || 'ACTIVE'}
        </span>
      </div>

      <div className="space-y-1.5 text-[11px] text-slate-400 pt-2 border-t border-slate-800">
        <div className="flex items-center justify-between">
          <span>Location:</span>
          <span className="text-slate-200 font-medium truncate max-w-[120px]">{data.location}</span>
        </div>
        <div className="flex items-center justify-between">
          <span>Isolated DB:</span>
          <span className="text-slate-300 font-mono text-[10px]">{data.database_name}</span>
        </div>
        <div className="flex items-center justify-between">
          <span>Gateway Link:</span>
          <span className="text-emerald-400 font-semibold">TLS 1.3 / HMAC</span>
        </div>
      </div>
    </div>
  );
};

// Custom Central Gateway Node Component
const GatewayNodeComponent = ({ data }) => {
  return (
    <div className="px-6 py-5 rounded-2xl bg-gradient-to-b from-[#0f1d3d] to-[#0a1329] border-2 border-emerald-500/60 shadow-2xl shadow-emerald-500/10 min-w-[280px] text-center">
      <div className="w-12 h-12 rounded-2xl bg-emerald-500/15 border border-emerald-500/40 flex items-center justify-center text-emerald-400 mx-auto mb-3 shadow-inner">
        <Network className="w-6 h-6 animate-pulse" />
      </div>
      <h3 className="text-base font-bold text-white tracking-tight">{data.name}</h3>
      <span className="text-xs font-mono text-emerald-400 font-bold block mb-3">{data.id}</span>

      <div className="grid grid-cols-2 gap-2 text-left text-[10px] pt-3 border-t border-slate-800">
        <div className="p-2 rounded-lg bg-slate-900/60 border border-slate-800">
          <span className="text-slate-400 block">Scope Check:</span>
          <span className="text-emerald-400 font-bold">STRICT_WHITELIST</span>
        </div>
        <div className="p-2 rounded-lg bg-slate-900/60 border border-slate-800">
          <span className="text-slate-400 block">Anti-Replay:</span>
          <span className="text-cyan-400 font-bold">IDEMPOTENT_CACHE</span>
        </div>
        <div className="p-2 rounded-lg bg-slate-900/60 border border-slate-800">
          <span className="text-slate-400 block">HMAC Auth:</span>
          <span className="text-purple-400 font-bold">SHA-256 CONSTANT</span>
        </div>
        <div className="p-2 rounded-lg bg-slate-900/60 border border-slate-800">
          <span className="text-slate-400 block">Dual Audit:</span>
          <span className="text-amber-400 font-bold">POSTGRESQL_PERSIST</span>
        </div>
      </div>
    </div>
  );
};

const nodeTypes = {
  branchNode: BranchNodeComponent,
  gatewayNode: GatewayNodeComponent,
};

export const FederationNetworkView = () => {
  const [topology, setTopology] = useState(null);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [activeSimulation, setActiveSimulation] = useState(null);
  const [selectedBranch, setSelectedBranch] = useState(null);
  const [selectedPacket, setSelectedPacket] = useState(null);
  const [isPaused, setIsPaused] = useState(false);
  const [filterBranch, setFilterBranch] = useState('ALL');

  // React Flow state
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const loadTopology = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchVisualizerFederationTopology();
      setTopology(data);
    } catch (err) {
      console.error('Failed to load federation topology:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTopology();
  }, [loadTopology]);

  // Construct React Flow Nodes and Edges when topology is loaded
  useEffect(() => {
    if (!topology) return;

    const gatewayNode = {
      id: 'FED-GATEWAY-CORE',
      type: 'gatewayNode',
      position: { x: 420, y: 160 },
      data: topology.gateway,
    };

    // Position the 3 branches around the gateway
    const branchPositions = {
      BLR001: { x: 80, y: 180 },
      CHE001: { x: 780, y: 80 },
      HYD001: { x: 780, y: 320 },
    };

    const branchNodes = (topology.branches || []).map((b) => ({
      id: b.branch_id,
      type: 'branchNode',
      position: branchPositions[b.branch_id] || { x: 100, y: 100 },
      data: {
        ...b,
        isSelected: selectedBranch?.branch_id === b.branch_id,
      },
    }));

    setNodes([gatewayNode, ...branchNodes]);

    // Construct directed edges connecting branches to gateway
    const newEdges = [
      {
        id: 'edge-BLR001-GATEWAY',
        source: 'BLR001',
        target: 'FED-GATEWAY-CORE',
        animated: true,
        style: { stroke: '#06b6d4', strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#06b6d4' },
      },
      {
        id: 'edge-GATEWAY-BLR001',
        source: 'FED-GATEWAY-CORE',
        target: 'BLR001',
        animated: true,
        style: { stroke: '#06b6d4', strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#06b6d4' },
      },
      {
        id: 'edge-GATEWAY-CHE001',
        source: 'FED-GATEWAY-CORE',
        target: 'CHE001',
        animated: true,
        style: { stroke: '#10b981', strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#10b981' },
      },
      {
        id: 'edge-CHE001-GATEWAY',
        source: 'CHE001',
        target: 'FED-GATEWAY-CORE',
        animated: true,
        style: { stroke: '#10b981', strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#10b981' },
      },
      {
        id: 'edge-GATEWAY-HYD001',
        source: 'FED-GATEWAY-CORE',
        target: 'HYD001',
        animated: true,
        style: { stroke: '#a855f7', strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#a855f7' },
      },
      {
        id: 'edge-HYD001-GATEWAY',
        source: 'HYD001',
        target: 'FED-GATEWAY-CORE',
        animated: true,
        style: { stroke: '#a855f7', strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#a855f7' },
      },
    ];

    setEdges(newEdges);
  }, [topology, selectedBranch, setNodes, setEdges]);

  // Handle node click
  const onNodeClick = useCallback(
    (_, node) => {
      if (node.type === 'branchNode') {
        setSelectedBranch(node.data);
      } else {
        setSelectedBranch(null);
      }
    },
    []
  );

  // Trigger cross-branch simulation
  const handleTriggerSimulation = async (source, dest, scope, mode) => {
    try {
      setSimulating(true);
      const res = await simulateVisualizerFederationExchange({
        source_branch_id: source,
        destination_branch_id: dest,
        requested_scope: scope,
        auth_mode: mode,
      });

      setActiveSimulation(res);
      setSelectedPacket(res);

      // Refresh topology events list
      loadTopology();
    } catch (err) {
      console.error('Simulation error:', err);
    } finally {
      setSimulating(false);
    }
  };

  // Filtered recent events
  const filteredEvents = useMemo(() => {
    if (!topology?.recent_events) return [];
    if (filterBranch === 'ALL') return topology.recent_events;
    return topology.recent_events.filter(
      (e) => e.source_branch === filterBranch || e.destination_branch === filterBranch
    );
  }, [topology, filterBranch]);

  return (
    <div className="space-y-6">
      {/* View Header with Action Controls */}
      <div className="bg-[#0b152e] border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-cyan-400 text-xs font-bold uppercase tracking-wider mb-1">
              <Network className="w-4 h-4" />
              <span>Multi-Branch Federation Network</span>
            </div>
            <h2 className="text-xl font-extrabold text-white tracking-tight">
              Central Federation Gateway & Branch Mesh
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Strictly authenticated cross-branch information verification between Bengaluru (BLR001), Chennai (CHE001), and Hyderabad (HYD001).
            </p>
          </div>

          {/* Quick Simulation Trigger Buttons */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              disabled={simulating}
              onClick={() =>
                handleTriggerSimulation('BLR001', 'CHE001', 'ACCOUNT_STATUS_CONFIRMATION', 'VALID')
              }
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-cyan-500/15 text-cyan-300 border border-cyan-500/40 hover:bg-cyan-500/25 transition disabled:opacity-50"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>BLR → CHE (Valid Query)</span>
            </button>

            <button
              disabled={simulating}
              onClick={() =>
                handleTriggerSimulation('BLR001', 'HYD001', 'CUSTOMER_KYC_VERIFICATION', 'VALID')
              }
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/40 hover:bg-emerald-500/25 transition disabled:opacity-50"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>BLR → HYD (KYC Check)</span>
            </button>

            <button
              disabled={simulating}
              onClick={() =>
                handleTriggerSimulation('BLR001', 'CHE001', 'ACCOUNT_STATUS_CONFIRMATION', 'INVALID_KEY')
              }
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-red-500/15 text-red-300 border border-red-500/40 hover:bg-red-500/25 transition disabled:opacity-50"
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Forged Key (Reject 401)</span>
            </button>

            <button
              disabled={simulating}
              onClick={() =>
                handleTriggerSimulation('BLR001', 'CHE001', 'RAW_UNRESTRICTED_DATABASE_ACCESS', 'VALID')
              }
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-orange-500/15 text-orange-300 border border-orange-500/40 hover:bg-orange-500/25 transition disabled:opacity-50"
            >
              <Lock className="w-3.5 h-3.5" />
              <span>Scope Violation (Deny 403)</span>
            </button>

            <button
              disabled={simulating}
              onClick={() =>
                handleTriggerSimulation('BLR001', 'CHE001', 'ACCOUNT_STATUS_CONFIRMATION', 'DUPLICATE_REPLAY')
              }
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-purple-500/15 text-purple-300 border border-purple-500/40 hover:bg-purple-500/25 transition disabled:opacity-50"
            >
              <RotateCw className="w-3.5 h-3.5" />
              <span>Duplicate Anti-Replay</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Graph Canvas and Side Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* React Flow Network Canvas */}
        <div className="lg:col-span-2 h-[520px] bg-[#070d1e] rounded-2xl border border-slate-800 overflow-hidden relative shadow-2xl">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
            attributionPosition="bottom-left"
          >
            <Background color="#1e293b" gap={20} size={1} />
            <Controls className="!bg-slate-900 !border-slate-800 !text-slate-300" />
            <MiniMap
              nodeColor={(n) => (n.id === 'FED-GATEWAY-CORE' ? '#10b981' : '#06b6d4')}
              className="!bg-slate-950/80 !border-slate-800 rounded-xl"
            />
          </ReactFlow>

          {/* Active Simulation Floating Overlay */}
          {activeSimulation && (
            <div className="absolute top-4 left-4 max-w-sm p-4 rounded-xl bg-slate-950/90 border border-cyan-500/40 backdrop-blur-md shadow-2xl z-10 animate-fade-in">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400">
                  {activeSimulation.is_success ? 'Cross-Branch Packet Authorized' : 'Security Defense Intercepted'}
                </span>
                <button
                  onClick={() => setActiveSimulation(null)}
                  className="p-1 text-slate-400 hover:text-white"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="space-y-1 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Route:</span>
                  <span className="font-bold text-white font-mono">
                    {activeSimulation.source_branch} → {activeSimulation.destination_branch}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Scope:</span>
                  <span className="text-cyan-300 font-mono text-[10px] truncate max-w-[170px]">
                    {activeSimulation.requested_scope}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Result:</span>
                  <span
                    className={`font-bold text-[11px] ${
                      activeSimulation.is_success ? 'text-emerald-400' : 'text-red-400'
                    }`}
                  >
                    {activeSimulation.result?.authorization_result || 'COMPLETED'}
                  </span>
                </div>
              </div>

              {/* Trajectory Step Preview */}
              <div className="mt-3 pt-2 border-t border-slate-800 space-y-1">
                <span className="text-[10px] text-slate-500 uppercase font-bold">Packet Trajectory:</span>
                <div className="flex items-center space-x-1 overflow-x-auto py-1">
                  {activeSimulation.trajectory_steps.map((st, i) => (
                    <span
                      key={i}
                      className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold whitespace-nowrap ${
                        st.status === 'PASS'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                          : st.status === 'BLOCKED' || st.status === 'FAIL'
                          ? 'bg-red-500/10 text-red-400 border border-red-500/30'
                          : 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                      }`}
                      title={st.description}
                    >
                      {st.stage}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Side Panel: Branch Inspector or Packet Details */}
        <div className="bg-[#0b152e] rounded-2xl border border-slate-800 p-5 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                <Eye className="w-4 h-4 text-cyan-400" />
                <span>{selectedBranch ? `Branch Inspector: ${selectedBranch.branch_id}` : 'Federation Packet Inspector'}</span>
              </h3>
              {selectedBranch && (
                <button
                  onClick={() => setSelectedBranch(null)}
                  className="text-xs text-cyan-400 hover:underline"
                >
                  Clear Selection
                </button>
              )}
            </div>

            {selectedBranch ? (
              <div className="space-y-3 text-xs">
                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                  <span className="text-slate-400 block text-[11px] mb-1">Branch Identity:</span>
                  <span className="text-base font-bold text-white block">{selectedBranch.branch_name}</span>
                  <span className="text-xs font-mono text-cyan-400">{selectedBranch.branch_id}</span>
                </div>

                <div className="space-y-2 text-slate-300">
                  <div className="flex justify-between py-1 border-b border-slate-850">
                    <span className="text-slate-400">Location:</span>
                    <span className="font-medium text-white">{selectedBranch.location}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-850">
                    <span className="text-slate-400">Database Isolation:</span>
                    <span className="font-mono text-emerald-400">{selectedBranch.database_name}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-850">
                    <span className="text-slate-400">Gateway Status:</span>
                    <span className="font-bold text-emerald-400">CONNECTED</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-850">
                    <span className="text-slate-400">Internal Endpoint:</span>
                    <span className="font-mono text-[10px] text-slate-400 truncate max-w-[160px]">{selectedBranch.endpoint}</span>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-800/40 text-[11px] text-cyan-300">
                  <span className="font-bold block mb-1">Database Isolation Guarantee:</span>
                  Direct peer-to-peer database queries are physically prevented. All queries must route through the Central Federation Gateway via HMAC-signed envelopes.
                </div>
              </div>
            ) : selectedPacket ? (
              <div className="space-y-3 text-xs">
                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400 text-[11px]">Correlation ID:</span>
                    <span className="text-[10px] font-mono text-cyan-400 font-bold">{selectedPacket.correlation_id}</span>
                  </div>
                  <div className="mt-1 flex items-center justify-between text-sm font-bold text-white">
                    <span>{selectedPacket.source_branch}</span>
                    <ArrowRight className="w-4 h-4 text-cyan-400" />
                    <span>{selectedPacket.destination_branch}</span>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between py-1 border-b border-slate-850">
                    <span className="text-slate-400">Event ID:</span>
                    <span className="font-mono text-[10px] text-slate-300">
                      {selectedPacket.result?.federation_event_id}
                    </span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-850">
                    <span className="text-slate-400">Requested Scope:</span>
                    <span className="font-mono text-[10px] text-purple-300 truncate max-w-[150px]">
                      {selectedPacket.requested_scope}
                    </span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-850">
                    <span className="text-slate-400">HMAC Auth:</span>
                    <span className="font-bold text-emerald-400">
                      {selectedPacket.result?.authorization_result === 'REJECTED_AUTHENTICATION' ? 'REJECTED' : 'AUTHENTICATED'}
                    </span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-850">
                    <span className="text-slate-400">Scope Authorization:</span>
                    <span
                      className={`font-bold ${
                        selectedPacket.result?.authorization_result === 'REJECTED_UNAUTHORIZED'
                          ? 'text-red-400'
                          : 'text-emerald-400'
                      }`}
                    >
                      {selectedPacket.result?.authorization_result}
                    </span>
                  </div>
                </div>

                {/* Sanitized Response Data */}
                {selectedPacket.result?.data && (
                  <div className="p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-800/40 text-[11px]">
                    <span className="font-bold text-emerald-400 block mb-1">Sanitized Confirmation:</span>
                    <pre className="text-[10px] font-mono text-emerald-200 overflow-x-auto">
                      {JSON.stringify(selectedPacket.result.data, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12 text-slate-500 space-y-2">
                <Network className="w-10 h-10 mx-auto text-slate-600" />
                <p className="text-xs">Click on any branch node or trigger a cross-branch exchange above to inspect the federation packet.</p>
              </div>
            )}
          </div>

          <div className="pt-4 border-t border-slate-800">
            <span className="text-[10px] text-slate-500 font-mono block">
              Protocol: HTTPS / TLS 1.3 • Dual Audit Enabled
            </span>
          </div>
        </div>
      </div>

      {/* Dual Branch Audit Trail Ledger */}
      <div className="bg-[#0b152e] rounded-2xl border border-slate-800 p-5 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
              <Layers className="w-4 h-4 text-cyan-400" />
              <span>Authentic Federation Gateway Event Log</span>
            </h3>
            <span className="text-xs text-slate-400">Dual-branch immutable ledger synchronized across isolated databases</span>
          </div>

          {/* Filter by branch */}
          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-400">Filter Branch:</span>
            <select
              value={filterBranch}
              onChange={(e) => setFilterBranch(e.target.value)}
              className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
            >
              <option value="ALL">All Branches</option>
              <option value="BLR001">Bengaluru (BLR001)</option>
              <option value="CHE001">Chennai (CHE001)</option>
              <option value="HYD001">Hyderabad (HYD001)</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider">
                <th className="py-2.5 px-3">Event ID</th>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Source → Dest</th>
                <th className="py-2.5 px-3">Scope</th>
                <th className="py-2.5 px-3">Authorization Result</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
              {filteredEvents.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-slate-500 font-sans">
                    No cross-branch federation events found. Trigger a simulation above.
                  </td>
                </tr>
              ) : (
                filteredEvents.slice(0, 8).map((ev) => (
                  <tr key={ev.event_id} className="hover:bg-slate-900/50 transition">
                    <td className="py-2.5 px-3 text-cyan-400 font-bold">{ev.event_id}</td>
                    <td className="py-2.5 px-3 text-slate-400 font-sans text-xs">
                      {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : 'Recent'}
                    </td>
                    <td className="py-2.5 px-3 text-white font-bold">
                      {ev.source_branch} → {ev.destination_branch}
                    </td>
                    <td className="py-2.5 px-3 text-purple-300 truncate max-w-[140px]">{ev.scope}</td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          ev.authorization_result === 'AUTHORIZED'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                            : 'bg-red-500/10 text-red-400 border border-red-500/30'
                        }`}
                      >
                        {ev.authorization_result}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          ev.status === 'SUCCESS'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                            : ev.status === 'DUPLICATE'
                            ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                            : 'bg-red-500/10 text-red-400 border border-red-500/30'
                        }`}
                      >
                        {ev.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={() =>
                          setSelectedPacket({
                            correlation_id: ev.correlation_id,
                            source_branch: ev.source_branch,
                            destination_branch: ev.destination_branch,
                            requested_scope: ev.scope,
                            result: {
                              federation_event_id: ev.event_id,
                              authorization_result: ev.authorization_result,
                              status: ev.status,
                              data: ev.response_payload,
                            },
                          })
                        }
                        className="px-2.5 py-1 rounded-lg text-[10px] font-sans font-bold bg-slate-800 hover:bg-slate-700 text-slate-200 transition"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
