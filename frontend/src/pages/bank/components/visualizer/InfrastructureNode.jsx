import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Radio, Database, Server, Cpu, CheckCircle } from 'lucide-react';

export const InfrastructureNode = memo(({ data, selected }) => {
  const {
    type = 'RABBITMQ', // 'RABBITMQ' | 'POSTGRESQL'
    title = 'Message Broker',
    subtitle = 'amqp://rabbitmq:5672',
    metric_label = 'Active Queues',
    metric_value = '6 Queues',
    status = 'CONNECTED',
  } = data;

  const isRabbit = type === 'RABBITMQ';
  const Icon = isRabbit ? Radio : Database;
  const accentColor = isRabbit ? 'text-orange-400' : 'text-blue-400';
  const borderColor = isRabbit
    ? 'border-orange-500/50 hover:border-orange-400 shadow-[0_0_15px_rgba(249,115,22,0.2)]'
    : 'border-blue-500/50 hover:border-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.2)]';
  const badgeColor = isRabbit
    ? 'bg-orange-500/10 text-orange-300 border-orange-500/30'
    : 'bg-blue-500/10 text-blue-300 border-blue-500/30';

  return (
    <div
      className={`relative min-w-[210px] max-w-[250px] rounded-2xl bg-[#091124]/95 backdrop-blur-md p-3.5 border transition-all duration-300 cursor-pointer shadow-lg ${borderColor} ${
        selected ? 'ring-2 ring-emerald-400 scale-[1.02]' : ''
      }`}
    >
      {/* Target Handle (Left) */}
      <Handle
        type="target"
        position={Position.Left}
        className={`w-2.5 h-2.5 border-2 border-[#070d1e] !-left-1.5 ${isRabbit ? 'bg-orange-400' : 'bg-blue-400'}`}
      />

      {/* Target Handle (Top for Supervisor heartbeat check) */}
      <Handle
        type="target"
        position={Position.Top}
        id="top"
        className="w-2 h-2 bg-indigo-400 border-2 border-[#070d1e] !-top-1"
      />

      {/* Header */}
      <div className="flex items-center space-x-2.5 mb-2.5">
        <div
          className={`w-8 h-8 rounded-xl flex items-center justify-center border ${badgeColor} ${accentColor}`}
        >
          <Icon className="w-4 h-4" />
        </div>
        <div className="min-w-0 flex-1">
          <h4 className="text-xs font-bold text-white truncate">{title}</h4>
          <span className="text-[10px] text-slate-400 font-mono truncate block">{subtitle}</span>
        </div>
      </div>

      {/* Metric Capsule */}
      <div className="px-2.5 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 text-[11px] flex items-center justify-between mb-2">
        <span className="text-slate-400 text-[10px] uppercase font-semibold">{metric_label}:</span>
        <span className="font-mono text-slate-200 font-bold">{metric_value}</span>
      </div>

      {/* Footer Status */}
      <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-800/80">
        <span className="flex items-center space-x-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="text-emerald-400 font-semibold">{status}</span>
        </span>
        <span className="text-[9px] font-mono text-slate-400">
          {isRabbit ? 'TOPIC / DIRECT' : 'ACID / ENCRYPTED'}
        </span>
      </div>

      {/* Source Handle (Right) */}
      <Handle
        type="source"
        position={Position.Right}
        className={`w-2.5 h-2.5 border-2 border-[#070d1e] !-right-1.5 ${isRabbit ? 'bg-orange-400' : 'bg-blue-400'}`}
      />
    </div>
  );
});
