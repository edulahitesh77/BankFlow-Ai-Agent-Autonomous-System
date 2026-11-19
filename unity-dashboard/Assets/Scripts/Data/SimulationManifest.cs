using System;
using System.Collections.Generic;
using UnityEngine;

namespace BankFlowAI.Data
{
    [Serializable]
    public class RequestData
    {
        public string request_id;
        public string service_type;
        public string status;
        public string stage;
        public string priority;
        public string assigned_agent;
        public int assignment_version;
        public int retry_count;
        public int customer_id;
        public int account_id;
        public string created_at;
        public string updated_at;
    }

    [Serializable]
    public class AgentData
    {
        public string agent_code;
        public string agent_type;
        public string availability_status;
        public string processing_status;
        public string health_status;
        public string current_request_id;
        public int completed_count;
        public int failed_count;
        public int retry_count;
        public bool is_paused;
        public string last_heartbeat_at;
    }

    [Serializable]
    public class SimulationEvent
    {
        public string event_id;
        public int tick;
        public string timestamp;
        public string event_type;
        public string request_id;
        public string sender_agent;
        public string receiver_agent;
        public string previous_state;
        public string new_state;
        public int assignment_version;
        public string reason_code;
    }

    [Serializable]
    public class QueueCounts
    {
        public int NEW;
        public int CLASSIFIED;
        public int QUEUED;
        public int VERIFIED;
        public int IN_SERVICE;
        public int COMPLETED;
        public int NEEDS_CORRECTION;
        public int HUMAN_REVIEW;
        public int REJECTED_INPUT;
        public int FAILED;
    }

    [Serializable]
    public class SimulationSnapshot
    {
        public int tick;
        public string timestamp;
        public List<RequestData> active_requests = new List<RequestData>();
        public List<AgentData> agents = new List<AgentData>();
    }

    [Serializable]
    public class SimulationMetrics
    {
        public int total_requests;
        public int completed_requests;
        public int failed_requests;
        public int pending_requests;
        public int human_review_requests;
        public int recovered_requests;
        public float avg_waiting_time_ticks;
        public float avg_completion_time_ticks;
        public float throughput_per_minute;
        public float request_agent_utilization;
        public float message_integrity_rate;
    }

    [Serializable]
    public class BranchData
    {
        public string branch_id;
        public string branch_name;
        public string location;
        public string status;
        public int active_agents;
        public int pending_requests;
        public int completed_requests;
    }

    [Serializable]
    public class FederationEventData
    {
        public string federation_event_id;
        public string source_branch_id;
        public string destination_branch_id;
        public string request_id;
        public string event_type;
        public string requested_scope;
        public string authorization_result;
        public string correlation_id;
        public string event_status;
        public string timestamp;
        public string error_message;
    }

    [Serializable]
    public class SimulationManifest
    {
        public string schema_version;
        public string simulation_id;
        public string scenario_name;
        public string exported_at;
        public int total_ticks;
        public int total_events;
        public SimulationMetrics metrics;
        public List<SimulationSnapshot> snapshots = new List<SimulationSnapshot>();
        public List<SimulationEvent> events = new List<SimulationEvent>();
        public List<BranchData> branches = new List<BranchData>();
        public List<FederationEventData> federation_events = new List<FederationEventData>();

        /// <summary>
        /// Validates manifest schema compliance and data integrity.
        /// </summary>
        public bool IsValid(out string error)
        {
            if (string.IsNullOrEmpty(schema_version))
            {
                error = "Missing schema_version.";
                return false;
            }
            if (schema_version != "1.0.0")
            {
                error = $"Unsupported schema version '{schema_version}'. Expected '1.0.0'.";
                return false;
            }
            if (snapshots == null || snapshots.Count == 0)
            {
                error = "Simulation manifest contains no snapshots.";
                return false;
            }
            if (metrics == null)
            {
                error = "Simulation manifest is missing authoritative metrics.";
                return false;
            }
            error = null;
            return true;
        }
    }
}
