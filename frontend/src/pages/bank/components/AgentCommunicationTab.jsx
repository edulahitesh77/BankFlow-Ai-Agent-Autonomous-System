import React, { useState, useEffect, useCallback } from 'react';
import {
  Server,
  RefreshCw,
  Search,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Layers,
  ArrowRight,
  Database,
  Radio,
  Cpu,
  RotateCcw,
  Eye,
  X,
  Activity,
  Sliders,
  Filter,
} from 'lucide-react';
import {
  fetchBrokerStatus,
  fetchQueueStatus,
  fetchCommunicationStats,
  fetchEventHistory,
  fetchRequestTimeline,
  fetchDeadLetters,
  retryDeadLetterMessage,
  fetchAgentCommunicationMetrics,
} from '../../../api/auth';

export const AgentCommunicationTab = ({ onSelectRequest }) => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [brokerStatus, setBrokerStatus] = useState(null);
  const [queues, setQueues] = useState([]);
  const [stats, setStats] = useState(null);
  const [agentMetrics, setAgentMetrics] = useState([]);
  const [deadLetters, setDeadLetters] = useState([]);

  // Event feed state
  const [events, setEvents] = useState([]);
  const [eventTotal, setEventTotal] = useState(0);
  const [searchRequestId, setSearchRequestId] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('');
  const [selectedEventType, setSelectedEventType] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 15;

  // Timeline Modal state
  const [timelineRequestId, setTimelineRequestId] = useState(null);
  const [timelineEvents, setTimelineEvents] = useState([]);
  const [timelineLoading, setTimelineLoading] = useState(false);

  // Retry action state
  const [retryingId, setRetryingId] = useState(null);
  const [actionMessage, setActionMessage] = useState(null);

  const loadData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);

    try {
      const [bStatus, qList, commStats, evtHistory, deadList, metrics] = await Promise.all([
        fetchBrokerStatus().catch(() => null),
        fetchQueueStatus().catch(() => []),
        fetchCommunicationStats().catch(() => null),
        fetchEventHistory({
          requestId: searchRequestId.trim(),
          agentId: selectedAgent,
          eventType: selectedEventType,
          page: currentPage,
          pageSize,
        }).catch(() => ({ total: 0, items: [] })),
        fetchDeadLetters().catch(() => []),
        fetchAgentCommunicationMetrics().catch(() => []),
      ]);

      setBrokerStatus(bStatus);
      setQueues(qList || []);
      setStats(commStats);
      setEvents(evtHistory?.items || []);
      setEventTotal(evtHistory?.total || 0);
      setDeadLetters(deadList || []);
      setAgentMetrics(metrics || []);
    } catch (err) {
      console.error('Failed to load messaging data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [searchRequestId, selectedAgent, selectedEventType, currentPage]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Open timeline modal for a single request
  const handleOpenTimeline = async (reqId) => {
    setTimelineRequestId(reqId);
    setTimelineLoading(true);
    try {
      const timeline = await fetchRequestTimeline(reqId);
      setTimelineEvents(timeline || []);
    } catch (err) {
      console.error('Failed to load timeline:', err);
      setTimelineEvents([]);
    } finally {
      setTimelineLoading(false);
    }
  };

  // Replay a dead-lettered message
  const handleRetryMessage = async (msgId) => {
    setRetryingId(msgId);
    setActionMessage(null);
    try {
      const res = await retryDeadLetterMessage(msgId);
      setActionMessage({ type: 'success', text: res.message || 'Message replayed to exchange successfully.' });
      await loadData(true);
    } catch (err) {
      setActionMessage({ type: 'error', text: err.message || 'Failed to replay message.' });
    } finally {
      setRetryingId(null);
    }
  };

  const getEventTypeBadge = (type) => {
    switch (type) {
      case 'REQUEST_CREATED':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
      case 'REQUEST_CLASSIFIED':
        return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
      case 'REQUEST_ASSIGNED':
      case 'REQUEST_ACCEPTED':
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30';
      case 'VERIFICATION_COMPLETED':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'SERVICE_STARTED':
      case 'SERVICE_COMPLETED':
        return 'bg-teal-500/10 text-teal-300 border-teal-500/30';
      case 'HUMAN_REVIEW_REQUIRED':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'REQUEST_NEEDS_CORRECTION':
        return 'bg-orange-500/10 text-orange-400 border-orange-500/30';
      case 'VERIFICATION_FAILED':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      case 'AGENT_HEARTBEAT':
        return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
      case 'SUPERVISOR_ALERT':
        return 'bg-red-500/10 text-red-400 border-red-500/30';
      default:
        return 'bg-slate-500/10 text-slate-300 border-slate-500/30';
    }
  };

  if (loading && !refreshing) {
    return (
      <div className="flex flex-col items-center justify-center py-24 space-y-4 text-slate-400">
        <RefreshCw className="w-10 h-10 animate-spin text-emerald-500" />
        <p className="text-sm">Connecting to RabbitMQ Broker and loading communication channels...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner: Broker Connection & Action Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border border-slate-800 shadow-xl">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-400">
            <Radio className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-bold text-white tracking-tight">Structured Agent Communication System</h2>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                  brokerStatus?.status === 'UP'
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full mr-1.5 ${
                    brokerStatus?.status === 'UP' ? 'bg-emerald-400 animate-ping' : 'bg-rose-400'
                  }`}
                />
                Broker {brokerStatus?.status || 'UNKNOWN'}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              RabbitMQ 4.0.5 • AMQP <span className="text-slate-300 font-mono">127.0.0.1:5672</span> • Exchanges:{' '}
              <span className="text-emerald-400 font-mono">bankflow.events</span> (Topic),{' '}
              <span className="text-rose-400 font-mono">bankflow.dlx</span> (DLX)
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => loadData(true)}
            disabled={refreshing}
            className="flex items-center px-3.5 py-2 text-xs font-medium text-slate-200 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 rounded-lg transition-colors shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-2 ${refreshing ? 'animate-spin text-emerald-400' : ''}`} />
            {refreshing ? 'Refreshing...' : 'Refresh Activity'}
          </button>
        </div>
      </div>

      {actionMessage && (
        <div
          className={`p-4 rounded-xl text-xs font-medium border flex items-center justify-between ${
            actionMessage.type === 'success'
              ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
              : 'bg-rose-500/10 text-rose-300 border-rose-500/30'
          }`}
        >
          <span>{actionMessage.text}</span>
          <button onClick={() => setActionMessage(null)} className="text-slate-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Section 1: Aggregate Communication Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Published</p>
          <p className="text-xl font-bold text-white mt-1">{stats?.total_messages_published ?? 0}</p>
          <span className="text-[10px] text-slate-500">Persistent Events</span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Consumed</p>
          <p className="text-xl font-bold text-blue-400 mt-1">{stats?.total_messages_consumed ?? 0}</p>
          <span className="text-[10px] text-slate-500">Batch Received</span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Processed</p>
          <p className="text-xl font-bold text-emerald-400 mt-1">{stats?.successfully_processed ?? 0}</p>
          <span className="text-[10px] text-slate-500">Manual Acked</span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Duplicates Blocked</p>
          <p className="text-xl font-bold text-purple-400 mt-1">{stats?.duplicate_messages_caught ?? 0}</p>
          <span className="text-[10px] text-slate-500">Idempotency Kept</span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Retried</p>
          <p className="text-xl font-bold text-amber-400 mt-1">{stats?.retried_messages ?? 0}</p>
          <span className="text-[10px] text-slate-500">Max 3 attempts</span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Dead Lettered</p>
          <p className="text-xl font-bold text-rose-400 mt-1">{stats?.dead_letter_messages ?? 0}</p>
          <span className="text-[10px] text-slate-500">In bankflow.dlq</span>
        </div>
      </div>

      {/* Section 2: Queue Depths & Status */}
      <div className="p-5 rounded-2xl bg-slate-900/40 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-semibold text-white tracking-wide">Broker Queue Depths & Bindings</h3>
          </div>
          <span className="text-xs text-slate-500">{queues.length} Durable Queues Declared</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {queues.map((q) => {
            const isDLQ = q.queue_name.includes('dlq');
            return (
              <div
                key={q.queue_name}
                className={`p-3.5 rounded-xl border flex flex-col justify-between transition-all ${
                  isDLQ
                    ? q.message_count > 0
                      ? 'bg-rose-950/20 border-rose-500/40'
                      : 'bg-slate-900/70 border-slate-800'
                    : 'bg-slate-900/70 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-medium text-slate-300 truncate" title={q.queue_name}>
                    {q.queue_name}
                  </span>
                  <span
                    className={`inline-block w-2 h-2 rounded-full ${
                      q.status === 'ACTIVE' ? 'bg-emerald-400' : 'bg-rose-400'
                    }`}
                  />
                </div>
                <div className="flex items-baseline justify-between mt-3">
                  <div>
                    <span className="text-xl font-bold text-white">{q.message_count}</span>
                    <span className="text-[10px] text-slate-400 ml-1.5">pending</span>
                  </div>
                  <span className="text-xs text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700">
                    {q.consumer_count} consumers
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Section 3: Dead-Letter Queue Monitoring & Replay */}
      {deadLetters.length > 0 && (
        <div className="p-5 rounded-2xl bg-rose-950/10 border border-rose-500/30 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-rose-400" />
              <h3 className="text-sm font-semibold text-rose-300">
                Dead-Letter Queue Alerts ({deadLetters.length} Unresolved)
              </h3>
            </div>
            <span className="text-xs text-rose-400">Policy: Max 3 Retries Exceeded</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-rose-950/30 text-rose-300 border-b border-rose-500/20">
                <tr>
                  <th className="py-2.5 px-3">Message ID</th>
                  <th className="py-2.5 px-3">Request ID</th>
                  <th className="py-2.5 px-3">Event Type</th>
                  <th className="py-2.5 px-3">Consumer</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Error Description</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-rose-500/10 text-slate-300">
                {deadLetters.map((dl) => (
                  <tr key={dl.id} className="hover:bg-rose-950/20">
                    <td className="py-2.5 px-3 font-mono text-[11px] text-rose-200">{dl.message_id}</td>
                    <td className="py-2.5 px-3 font-mono font-medium text-white">{dl.request_id || '—'}</td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-rose-500/20 text-rose-300 border border-rose-500/30">
                        {dl.event_type}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">{dl.consumer_name}</td>
                    <td className="py-2.5 px-3 font-semibold text-rose-400">{dl.processing_status}</td>
                    <td className="py-2.5 px-3 max-w-xs truncate text-slate-400" title={dl.error_message}>
                      {dl.error_message || 'Exhausted retry threshold'}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={() => handleRetryMessage(dl.message_id)}
                        disabled={retryingId === dl.message_id}
                        className="inline-flex items-center px-2.5 py-1 text-xs font-medium text-white bg-rose-600 hover:bg-rose-500 rounded border border-rose-400/30 transition-colors disabled:opacity-50"
                      >
                        <RotateCcw
                          className={`w-3 h-3 mr-1 ${retryingId === dl.message_id ? 'animate-spin' : ''}`}
                        />
                        {retryingId === dl.message_id ? 'Replaying...' : 'Replay'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Section 4: Agent Communication Throughput & Workload */}
      <div className="p-5 rounded-2xl bg-slate-900/40 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-semibold text-white tracking-wide">Multi-Agent Communication & Task Activity</h3>
          </div>
          <span className="text-xs text-slate-500">{agentMetrics.length} Active System Agents</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-2.5 px-3">Agent Code</th>
                <th className="py-2.5 px-3">Agent Role</th>
                <th className="py-2.5 px-3">Availability</th>
                <th className="py-2.5 px-3">Operational State</th>
                <th className="py-2.5 px-3 text-center">Events Published</th>
                <th className="py-2.5 px-3 text-center">Tasks Consumed</th>
                <th className="py-2.5 px-3 text-right">Last Active</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {agentMetrics.map((agt) => (
                <tr key={agt.agent_code} className="hover:bg-slate-800/40">
                  <td className="py-2.5 px-3 font-mono font-medium text-emerald-400">{agt.agent_code}</td>
                  <td className="py-2.5 px-3">{agt.agent_type.replace('_', ' ')}</td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium border ${
                        agt.availability_status === 'AVAILABLE'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                          : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                      }`}
                    >
                      {agt.availability_status}
                    </span>
                  </td>
                  <td className="py-2.5 px-3">
                    <span className="text-slate-400 font-mono text-[11px]">{agt.processing_status}</span>
                  </td>
                  <td className="py-2.5 px-3 text-center font-semibold text-white">{agt.messages_published}</td>
                  <td className="py-2.5 px-3 text-center font-semibold text-blue-400">{agt.tasks_consumed}</td>
                  <td className="py-2.5 px-3 text-right text-slate-500 text-[11px]">
                    {agt.last_active_at ? new Date(agt.last_active_at).toLocaleTimeString() : 'Active'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Section 5: Real-time Agent Event Feed */}
      <div className="p-5 rounded-2xl bg-slate-900/40 border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-semibold text-white tracking-wide">Exchanged Event History</h3>
            <p className="text-xs text-slate-400">
              Audit log of all structured JSON events exchanged through RabbitMQ exchanges
            </p>
          </div>

          {/* Search & Filter Controls */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                placeholder="Search Request ID..."
                value={searchRequestId}
                onChange={(e) => {
                  setSearchRequestId(e.target.value);
                  setCurrentPage(1);
                }}
                className="pl-8 pr-3 py-1.5 text-xs bg-slate-900 border border-slate-800 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 w-44"
              />
            </div>

            <select
              value={selectedEventType}
              onChange={(e) => {
                setSelectedEventType(e.target.value);
                setCurrentPage(1);
              }}
              className="px-2.5 py-1.5 text-xs bg-slate-900 border border-slate-800 rounded-lg text-slate-300 focus:outline-none focus:border-emerald-500"
            >
              <option value="">All Event Types</option>
              <option value="REQUEST_CREATED">REQUEST_CREATED</option>
              <option value="REQUEST_CLASSIFIED">REQUEST_CLASSIFIED</option>
              <option value="REQUEST_ASSIGNED">REQUEST_ASSIGNED</option>
              <option value="REQUEST_ACCEPTED">REQUEST_ACCEPTED</option>
              <option value="VERIFICATION_COMPLETED">VERIFICATION_COMPLETED</option>
              <option value="SERVICE_COMPLETED">SERVICE_COMPLETED</option>
              <option value="HUMAN_REVIEW_REQUIRED">HUMAN_REVIEW_REQUIRED</option>
              <option value="REQUEST_NEEDS_CORRECTION">REQUEST_NEEDS_CORRECTION</option>
              <option value="AGENT_HEARTBEAT">AGENT_HEARTBEAT</option>
            </select>
          </div>
        </div>

        {events.length === 0 ? (
          <div className="py-12 text-center text-slate-500 text-xs">
            No agent communication events matching filter criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-2.5 px-3">Event ID</th>
                  <th className="py-2.5 px-3">Timestamp</th>
                  <th className="py-2.5 px-3">Request ID</th>
                  <th className="py-2.5 px-3">Agent</th>
                  <th className="py-2.5 px-3">Event Type</th>
                  <th className="py-2.5 px-3">State Transition</th>
                  <th className="py-2.5 px-3 text-right">Exchange Timeline</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {events.map((ev) => (
                  <tr key={ev.id} className="hover:bg-slate-800/40">
                    <td className="py-2.5 px-3 font-mono text-[11px] text-slate-400">{ev.event_id}</td>
                    <td className="py-2.5 px-3 text-slate-500 text-[11px]">
                      {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : '—'}
                    </td>
                    <td className="py-2.5 px-3 font-mono font-medium text-emerald-400">{ev.request_id}</td>
                    <td className="py-2.5 px-3 font-mono text-slate-300">{ev.agent_id}</td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono border ${getEventTypeBadge(
                          ev.event_type
                        )}`}
                      >
                        {ev.event_type}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-[11px] font-mono text-slate-400">
                      {ev.previous_state ? (
                        <span className="flex items-center space-x-1">
                          <span>{ev.previous_state}</span>
                          <ArrowRight className="w-3 h-3 text-slate-600 inline" />
                          <span className="text-slate-200">{ev.new_state}</span>
                        </span>
                      ) : (
                        <span className="text-slate-200">{ev.new_state || '—'}</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={() => handleOpenTimeline(ev.request_id)}
                        className="inline-flex items-center px-2 py-1 text-[11px] font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded transition-colors"
                      >
                        <Eye className="w-3 h-3 mr-1 text-emerald-400" />
                        Timeline
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {eventTotal > pageSize && (
          <div className="flex items-center justify-between pt-3 border-t border-slate-800 text-xs text-slate-400">
            <span>
              Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, eventTotal)} of {eventTotal} events
            </span>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
                disabled={currentPage === 1}
                className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded text-slate-200 disabled:opacity-50"
              >
                Previous
              </button>
              <span className="px-2 font-mono text-white">{currentPage}</span>
              <button
                onClick={() => setCurrentPage((p) => p + 1)}
                disabled={currentPage * pageSize >= eventTotal}
                className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded text-slate-200 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Timeline Modal */}
      {timelineRequestId && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400">
                  <Activity className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Agent Exchange Timeline</h3>
                  <p className="text-xs text-slate-400 font-mono">Request ID: {timelineRequestId}</p>
                </div>
              </div>
              <button
                onClick={() => {
                  setTimelineRequestId(null);
                  setTimelineEvents([]);
                }}
                className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4">
              {timelineLoading ? (
                <div className="py-12 flex flex-col items-center justify-center text-slate-400 text-xs">
                  <RefreshCw className="w-6 h-6 animate-spin text-emerald-500 mb-2" />
                  Loading chronological message trace...
                </div>
              ) : timelineEvents.length === 0 ? (
                <div className="py-12 text-center text-slate-500 text-xs">
                  No communication trace recorded for this request.
                </div>
              ) : (
                <div className="relative border-l-2 border-slate-800 ml-4 pl-6 space-y-6">
                  {timelineEvents.map((evt, idx) => (
                    <div key={evt.id || idx} className="relative">
                      {/* Node point */}
                      <span className="absolute -left-[31px] top-1 w-3.5 h-3.5 rounded-full bg-slate-900 border-2 border-emerald-500" />
                      <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-800 space-y-2">
                        <div className="flex items-center justify-between">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono border ${getEventTypeBadge(
                              evt.event_type
                            )}`}
                          >
                            {evt.event_type}
                          </span>
                          <span className="text-[11px] text-slate-400">
                            {evt.timestamp ? new Date(evt.timestamp).toLocaleString() : '—'}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-300">
                            Agent: <strong className="text-emerald-400 font-mono">{evt.agent_id}</strong>
                          </span>
                          <span className="text-slate-400 font-mono text-[11px]">
                            {evt.previous_state || 'START'} → <strong className="text-white">{evt.new_state}</strong>
                          </span>
                        </div>
                        {evt.reason_code && (
                          <p className="text-xs text-amber-400 bg-amber-500/10 p-2 rounded border border-amber-500/20">
                            Reason: {evt.reason_code}
                          </p>
                        )}
                        {evt.payload && Object.keys(evt.payload).length > 0 && (
                          <pre className="text-[11px] font-mono text-slate-400 bg-slate-900/90 p-2.5 rounded border border-slate-800 overflow-x-auto">
                            {JSON.stringify(evt.payload, null, 2)}
                          </pre>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="p-4 border-t border-slate-800 bg-slate-900/90 flex justify-end space-x-3">
              {onSelectRequest && (
                <button
                  onClick={() => {
                    const reqId = timelineRequestId;
                    setTimelineRequestId(null);
                    onSelectRequest(reqId);
                  }}
                  className="px-4 py-2 text-xs font-medium text-emerald-300 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 rounded-lg transition-colors"
                >
                  Inspect Full Request
                </button>
              )}
              <button
                onClick={() => {
                  setTimelineRequestId(null);
                  setTimelineEvents([]);
                }}
                className="px-4 py-2 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
