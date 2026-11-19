import React from 'react';
import { X, Radio, ArrowRight, Layers, Clock, ShieldCheck, Hash, Send } from 'lucide-react';

export const EdgeInspectorDrawer = ({ edge, onClose, onSelectRequest }) => {
  if (!edge) return null;

  const { source, target, data = {} } = edge;
  const {
    label,
    active_event,
    request_id,
    routing_key = 'bankflow.workflow.direct',
    channel_type = 'RabbitMQ Direct Exchange',
    timestamp,
    is_supervisor_link = false,
  } = data;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-[#091126]/98 backdrop-blur-xl border-l border-slate-800 shadow-2xl flex flex-col transform transition-transform duration-300">
      {/* Top Header */}
      <div className="p-4 sm:p-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Radio className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide">Communication Channel</h3>
            <div className="text-xs text-slate-400 font-mono">
              {is_supervisor_link ? 'Supervision Heartbeat Bus' : channel_type}
            </div>
          </div>
        </div>

        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Content Scroll */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-5">
        {/* Source -> Target Visual Route */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
          <span className="text-xs uppercase font-semibold text-slate-400 block">Agent Link Topology</span>
          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs">
            <div className="text-center flex-1">
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Origin / Sender</span>
              <span className="font-mono font-bold text-emerald-400 block mt-0.5">{source}</span>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-500 flex-shrink-0 mx-2" />
            <div className="text-center flex-1">
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Destination / Consumer</span>
              <span className="font-mono font-bold text-cyan-400 block mt-0.5">{target}</span>
            </div>
          </div>
        </div>

        {/* Message Event Telemetry */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
          <span className="text-xs uppercase font-semibold text-slate-400 block">Event Transmission</span>

          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 border border-slate-850">
              <span className="text-slate-400">Event Type:</span>
              <span className="font-mono font-bold text-white">{active_event || label || 'IDLE_LINK'}</span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 border border-slate-850">
              <span className="text-slate-400">Routing Key:</span>
              <span className="font-mono text-cyan-400 text-[11px]">{routing_key}</span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 border border-slate-850">
              <span className="text-slate-400">Protocol Delivery:</span>
              <span className="text-emerald-400 font-mono font-semibold">AMQP 0-9-1 Reliable</span>
            </div>
          </div>
        </div>

        {/* Active Payload Context */}
        {request_id && (
          <div className="p-4 rounded-xl bg-cyan-950/40 border border-cyan-800/40 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-[10px] text-cyan-400 uppercase font-semibold block">Payload Request</span>
                <span className="font-mono text-sm font-bold text-white">{request_id}</span>
              </div>
              {onSelectRequest && (
                <button
                  onClick={() => onSelectRequest(request_id)}
                  className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition"
                >
                  View Request
                </button>
              )}
            </div>
          </div>
        )}

        {/* Timestamp */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span className="flex items-center space-x-1.5">
            <Clock className="w-3.5 h-3.5" />
            <span>Telemetry Recorded:</span>
          </span>
          <span className="font-mono text-slate-200">
            {timestamp ? new Date(timestamp).toLocaleTimeString() : 'Real-time Connected'}
          </span>
        </div>
      </div>

      {/* Drawer Footer */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/80 flex justify-end">
        <button
          onClick={onClose}
          className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition"
        >
          Close Channel
        </button>
      </div>
    </div>
  );
};
