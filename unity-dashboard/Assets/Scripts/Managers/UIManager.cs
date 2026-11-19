using UnityEngine;
using BankFlowAI.Data;
using BankFlowAI.UI;

namespace BankFlowAI.Managers
{
    public class UIManager : MonoBehaviour
    {
        public static UIManager Instance { get; private set; }

        [Header("UI Panels")]
        public TopNavBar topNavBar;
        public AgentMonitorPanel agentMonitorPanel;
        public SupervisorPanel supervisorPanel;
        public MetricsPanel metricsPanel;
        public EventInspectionPanel eventInspectionPanel;

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
        }

        private void Start()
        {
            if (SimulationManager.Instance != null)
            {
                SimulationManager.Instance.OnManifestLoaded += HandleManifestLoaded;
                SimulationManager.Instance.OnTickChanged += HandleTickChanged;
            }
        }

        private void OnDestroy()
        {
            if (SimulationManager.Instance != null)
            {
                SimulationManager.Instance.OnManifestLoaded -= HandleManifestLoaded;
                SimulationManager.Instance.OnTickChanged -= HandleTickChanged;
            }
        }

        private void HandleManifestLoaded(SimulationManifest manifest)
        {
            if (metricsPanel != null && manifest.metrics != null)
            {
                metricsPanel.UpdateMetrics(manifest.metrics);
            }
            if (supervisorPanel != null)
            {
                supervisorPanel.InitializeWithManifest(manifest);
            }
        }

        private void HandleTickChanged(int tick, SimulationSnapshot snapshot)
        {
            if (topNavBar != null)
            {
                int total = SimulationManager.Instance != null ? SimulationManager.Instance.totalTicks : 0;
                topNavBar.UpdateTickDisplay(tick, total);
            }
            if (supervisorPanel != null)
            {
                supervisorPanel.UpdateTick(tick, snapshot);
            }
        }

        /// <summary>
        /// Opens the event inspection panel for a selected request token or agent.
        /// </summary>
        public void InspectRequest(string requestId)
        {
            if (eventInspectionPanel != null)
            {
                eventInspectionPanel.ShowRequestHistory(requestId);
            }
        }

        public void InspectAgent(string agentCode)
        {
            if (eventInspectionPanel != null)
            {
                eventInspectionPanel.ShowAgentHistory(agentCode);
            }
        }
    }
}
