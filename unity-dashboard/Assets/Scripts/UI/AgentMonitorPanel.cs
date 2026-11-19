using UnityEngine;
using UnityEngine.UI;
using BankFlowAI.Data;
using BankFlowAI.Managers;

namespace BankFlowAI.UI
{
    public class AgentMonitorPanel : MonoBehaviour
    {
        [Header("Telemetry Counters")]
        public Text totalAgentsText;
        public Text healthyAgentsText;
        public Text busyAgentsText;
        public Text failedAgentsText;

        private void Start()
        {
            if (SimulationManager.Instance != null)
            {
                SimulationManager.Instance.OnTickChanged += HandleTick;
            }
        }

        private void OnDestroy()
        {
            if (SimulationManager.Instance != null)
            {
                SimulationManager.Instance.OnTickChanged -= HandleTick;
            }
        }

        private void HandleTick(int tick, SimulationSnapshot snapshot)
        {
            if (snapshot == null || snapshot.agents == null) return;

            int total = snapshot.agents.Count;
            int healthy = 0;
            int busy = 0;
            int failed = 0;

            foreach (var a in snapshot.agents)
            {
                if (a.health_status == "FAILED" || a.health_status == "UNRESPONSIVE")
                    failed++;
                else if (a.processing_status == "BUSY")
                    busy++;
                else
                    healthy++;
            }

            if (totalAgentsText != null) totalAgentsText.text = $"Total: {total}";
            if (healthyAgentsText != null) healthyAgentsText.text = $"Healthy: {healthy}";
            if (busyAgentsText != null) busyAgentsText.text = $"Busy: {busy}";
            if (failedAgentsText != null) failedAgentsText.text = $"Degraded/Failed: {failed}";
        }
    }
}
