using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using BankFlowAI.Agents;
using BankFlowAI.Managers;

namespace BankFlowAI.Visualization
{
    public class MessageTrajectory : MonoBehaviour
    {
        public static MessageTrajectory Instance { get; private set; }

        [Header("Packet Visual Prefab")]
        public GameObject messagePacketPrefab;
        public Transform packetParent;

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
                SimulationManager.Instance.OnTickChanged += HandleTickEvents;
            }
        }

        private void OnDestroy()
        {
            if (SimulationManager.Instance != null)
            {
                SimulationManager.Instance.OnTickChanged -= HandleTickEvents;
            }
        }

        private void HandleTickEvents(int tick, Data.SimulationSnapshot snapshot)
        {
            if (SimulationManager.Instance.activeManifest == null) return;

            // Find events for this tick
            var events = SimulationManager.Instance.activeManifest.events.FindAll(e => e.tick == tick);
            foreach (var ev in events)
            {
                if (!string.IsNullOrEmpty(ev.sender_agent) && !string.IsNullOrEmpty(ev.receiver_agent))
                {
                    DispatchPacket(ev.sender_agent, ev.receiver_agent, ev.event_type);
                }
            }
        }

        public void DispatchPacket(string senderCode, string receiverCode, string eventType)
        {
            if (AgentManager.Instance == null) return;

            AgentController sender = AgentManager.Instance.GetAgent(senderCode);
            AgentController receiver = AgentManager.Instance.GetAgent(receiverCode);

            if (sender == null || receiver == null) return;

            StartCoroutine(AnimatePacket(sender.transform.position, receiver.transform.position, receiver));
        }

        private IEnumerator AnimatePacket(Vector3 fromPos, Vector3 toPos, AgentController targetAgent)
        {
            GameObject packet;
            if (messagePacketPrefab != null)
            {
                packet = Instantiate(messagePacketPrefab, packetParent != null ? packetParent : transform);
            }
            else
            {
                packet = new GameObject("MessagePacket", typeof(RectTransform), typeof(Image));
                if (packetParent != null) packet.transform.SetParent(packetParent, false);
                Image img = packet.GetComponent<Image>();
                img.color = new Color(0.24f, 0.60f, 0.96f); // Cyan/Blue
                (packet.transform as RectTransform).sizeDelta = new Vector2(12f, 12f);
            }

            packet.transform.position = fromPos;

            float duration = 0.45f;
            float elapsed = 0f;

            while (elapsed < duration)
            {
                elapsed += Time.deltaTime;
                float t = elapsed / duration;
                // Add gentle arc height in Y
                Vector3 currentPos = Vector3.Lerp(fromPos, toPos, t);
                currentPos.y += Mathf.Sin(t * Mathf.PI) * 20f;
                packet.transform.position = currentPos;
                yield return null;
            }

            Destroy(packet);

            if (targetAgent != null)
            {
                targetAgent.TriggerMessagePulse();
            }
        }
    }
}
