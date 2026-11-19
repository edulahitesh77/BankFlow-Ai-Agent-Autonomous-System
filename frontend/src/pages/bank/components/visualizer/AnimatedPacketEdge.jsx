import React, { memo } from 'react';
import { getBezierPath, EdgeLabelRenderer, BaseEdge } from 'reactflow';
import { Radio } from 'lucide-react';

export const AnimatedPacketEdge = memo(
  ({
    id,
    source,
    target,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    style = {},
    markerEnd,
    data = {},
    selected,
  }) => {
    const [edgePath, labelX, labelY] = getBezierPath({
      sourceX,
      sourceY,
      sourcePosition,
      targetX,
      targetY,
      targetPosition,
    });

    const {
      active_event,
      request_id,
      label,
      routing_key,
      is_supervisor_link = false,
      is_active = false,
      color = '#10b981',
    } = data;

    // Supervisor links have distinct subtle styling
    const strokeColor = is_supervisor_link
      ? is_active
        ? '#818cf8'
        : 'rgba(99, 102, 241, 0.25)'
      : is_active
      ? '#06b6d4'
      : selected
      ? '#10b981'
      : 'rgba(148, 163, 184, 0.35)';

    const strokeDasharray = is_supervisor_link ? '5 5' : is_active ? '6 6' : undefined;

    return (
      <>
        {/* Glow halo when active */}
        {is_active && (
          <path
            d={edgePath}
            fill="none"
            stroke={is_supervisor_link ? 'rgba(99,102,241,0.4)' : 'rgba(6,182,212,0.4)'}
            strokeWidth={8}
            className="blur-sm transition-all"
          />
        )}

        {/* Primary Edge Line */}
        <BaseEdge
          path={edgePath}
          markerEnd={markerEnd}
          style={{
            ...style,
            stroke: strokeColor,
            strokeWidth: is_active ? 2.5 : selected ? 2.5 : 1.5,
            strokeDasharray: strokeDasharray,
            animation: is_active ? 'flowDash 1.2s linear infinite' : undefined,
          }}
        />

        {/* Animated Moving Packet traveling along the path */}
        {is_active && (
          <g>
            <circle r="5" fill="#06b6d4" className="filter drop-shadow-[0_0_6px_#06b6d4]">
              <animateMotion dur="2.2s" repeatCount="indefinite" path={edgePath} />
            </circle>
            <circle r="2" fill="#ffffff">
              <animateMotion dur="2.2s" repeatCount="indefinite" path={edgePath} />
            </circle>
          </g>
        )}

        {/* Edge Middle Badge / Inspector Trigger */}
        {(label || active_event) && (
          <EdgeLabelRenderer>
            <div
              style={{
                position: 'absolute',
                transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
                pointerEvents: 'all',
              }}
              className="nodrag nopan"
            >
              <button
                type="button"
                className={`px-2 py-0.5 rounded-full text-[9px] font-mono font-bold transition-all flex items-center space-x-1 shadow-lg ${
                  is_active
                    ? 'bg-cyan-950/90 text-cyan-300 border border-cyan-500/60 shadow-[0_0_12px_rgba(6,182,212,0.3)] animate-pulse'
                    : selected
                    ? 'bg-emerald-950 text-emerald-300 border border-emerald-500 scale-105'
                    : 'bg-slate-900/90 text-slate-400 border border-slate-800 hover:text-white hover:border-slate-700'
                }`}
              >
                {is_active && <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping mr-0.5" />}
                <span className="truncate max-w-[130px]">{active_event || label}</span>
                {request_id && (
                  <span className="text-[8px] bg-slate-800 px-1 rounded text-cyan-400 ml-1">
                    {request_id.split('-').pop()}
                  </span>
                )}
              </button>
            </div>
          </EdgeLabelRenderer>
        )}
      </>
    );
  }
);
