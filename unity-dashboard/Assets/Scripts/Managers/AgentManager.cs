using System.Collections.Generic;
using UnityEngine;
using BankFlowAI.Data;
using BankFlowAI.Agents;

namespace BankFlowAI.Managers
{
    public class AgentManager : MonoBehaviour
    {
        public static AgentManager Instance { get; private set; }

        [Header("Agent Prefab & Container")]
        public GameObject agentActorPrefab;
        public Transform agentsContainer;

        [Header("Tracked Agents")]
        private readonly Dictionary<string, AgentController> agentControllers = new Dictionary<string, AgentController>();

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
                SimulationManager.Instance.OnTickChanged += HandleTickChanged;
            }
        }

        private void OnDestroy()
        {
            if (SimulationManager.Instance != null)
            {
                SimulationManager.Instance.OnTickChanged -= HandleTickChanged;
            }
        }

        private void HandleTickChanged(int tick, SimulationSnapshot snapshot)
        {
            if (snapshot == null || snapshot.agents == null) return;

            foreach (var agentData in snapshot.agents)
            {
                AgentController controller = GetOrCreateAgentController(agentData.agent_code);
                controller.UpdateAgentState(agentData);
            }
        }

        public AgentController GetOrCreateAgentController(string agentCode)
        {
            if (agentControllers.TryGetValue(agentCode, out AgentController controller))
            {
                return controller;
            }

            GameObject go;
            if (agentActorPrefab != null)
            {
                go = Instantiate(agentActorPrefab, agentsContainer);
            }
            else
            {
                go = new GameObject($"Agent_{agentCode}", typeof(RectTransform));
                if (agentsContainer != null) go.transform.SetParent(agentsContainer, false);
            }

            controller = go.GetComponent<AgentController>() ?? go.AddComponent<AgentController>();
            agentControllers[agentCode] = controller;
            return controller;
        }

        public AgentController GetAgent(string agentCode)
        {
            if (agentControllers.TryGetValue(agentCode, out AgentController controller))
            {
                return controller;
            }
            return null;
        }

        public IEnumerable<AgentController> GetAllAgents()
        {
            return agentControllers.Values;
        }
    }
}
