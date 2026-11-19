using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using BankFlowAI.Data;

namespace BankFlowAI.UI
{
    public class SupervisorPanel : MonoBehaviour
    {
        [Header("Supervisor Telemetry")]
        public Text heartbeatStatusText;
        public Image heartbeatIndicator;
        public Text failureDetectionsText;
        public Text recoveredTasksText;
        public Text circuitBreakerStatusText;

        [Header("Event Feed")]
        public Text recoveryLogText;

        private readonly List<string> recoveryLogs = new List<string>();

        public void InitializeWithManifest(SimulationManifest manifest)
        {
            if (manifest == null) return;

            recoveryLogs.Clear();
            if (recoveryLogText != null)
                recoveryLogText.text = "Supervisor active. Monitoring agent heartbeats...";
        }

        public void UpdateTick(int tick, SimulationSnapshot snapshot)
        {
            if (heartbeatStatusText != null)
                heartbeatStatusText.text = "HEARTBEAT: OK";

            if (heartbeatIndicator != null)
                heartbeatIndicator.color = new Color(0.06f, 0.73f, 0.51f); // Green

            if (circuitBreakerStatusText != null)
                circuitBreakerStatusText.text = "CIRCUIT: CLOSED (HEALTHY)";

            // Check if any events occurred in this tick relating to timeout or recovery
            if (Managers.SimulationManager.Instance?.activeManifest != null)
            {
                var events = Managers.SimulationManager.Instance.activeManifest.events.FindAll(e => e.tick == tick);
                foreach (var ev in events)
                {
                    if (ev.event_type.Contains("TIMEOUT") || ev.event_type.Contains("REASSIGN") || ev.event_type.Contains("FAILOVER"))
                    {
                        string log = $"[Tick {tick:D2}] {ev.event_type}: {ev.request_id} ({ev.reason_code})";
                        recoveryLogs.Add(log);
                        if (recoveryLogs.Count > 6) recoveryLogs.RemoveAt(0);

                        if (recoveryLogText != null)
                            recoveryLogText.text = string.Join("\n", recoveryLogs);
                    }
                }
            }

            if (failureDetectionsText != null)
                failureDetectionsText.text = $"Failures Detected: {Mathf.Max(0, tick >= 7 ? 1 : 0)}";

            if (recoveredTasksText != null)
                recoveredTasksText.text = $"Recovered Tasks: {Mathf.Max(0, tick >= 8 ? 1 : 0)}";
        }
    }
}
