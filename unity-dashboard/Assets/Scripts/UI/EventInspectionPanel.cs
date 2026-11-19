using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using BankFlowAI.Data;
using BankFlowAI.Managers;

namespace BankFlowAI.UI
{
    public class EventInspectionPanel : MonoBehaviour
    {
        [Header("UI Structure")]
        public GameObject panelRoot;
        public Text headerTitleText;
        public Text eventDetailsText;
        public Button closeButton;

        private void Start()
        {
            if (closeButton != null)
            {
                closeButton.onClick.AddListener(Hide);
            }
            Hide();
        }

        public void ShowRequestHistory(string requestId)
        {
            if (panelRoot != null) panelRoot.SetActive(true);

            if (headerTitleText != null)
                headerTitleText.text = $"Request Audit: {requestId}";

            if (SimulationManager.Instance?.activeManifest == null)
            {
                if (eventDetailsText != null) eventDetailsText.text = "No simulation manifest loaded.";
                return;
            }

            var matchingEvents = SimulationManager.Instance.activeManifest.events.FindAll(
                e => e.request_id == requestId
            );

            if (matchingEvents.Count == 0)
            {
                if (eventDetailsText != null)
                    eventDetailsText.text = $"No historical events recorded for {requestId}.";
                return;
            }

            List<string> lines = new List<string>();
            foreach (var ev in matchingEvents)
            {
                lines.Add($"[Tick {ev.tick:D2}] {ev.event_type}");
                lines.Add($"   Sender: {ev.sender_agent} -> Receiver: {ev.receiver_agent}");
                lines.Add($"   State: {ev.previous_state} -> {ev.new_state} (Reason: {ev.reason_code ?? "N/A"})");
                lines.Add("   -------------------------------------------------");
            }

            if (eventDetailsText != null)
                eventDetailsText.text = string.Join("\n", lines);
        }

        public void ShowAgentHistory(string agentCode)
        {
            if (panelRoot != null) panelRoot.SetActive(true);

            if (headerTitleText != null)
                headerTitleText.text = $"Agent Telemetry: {agentCode}";

            if (SimulationManager.Instance?.activeManifest == null)
            {
                if (eventDetailsText != null) eventDetailsText.text = "No simulation manifest loaded.";
                return;
            }

            var matchingEvents = SimulationManager.Instance.activeManifest.events.FindAll(
                e => e.sender_agent == agentCode || e.receiver_agent == agentCode
            );

            List<string> lines = new List<string>();
            lines.Add($"Agent Code: {agentCode}");
            lines.Add($"Participated in {matchingEvents.Count} simulation events.");
            lines.Add("-------------------------------------------------");

            foreach (var ev in matchingEvents)
            {
                lines.Add($"[Tick {ev.tick:D2}] {ev.event_type} (Req: {ev.request_id})");
                lines.Add($"   Direction: {ev.sender_agent} -> {ev.receiver_agent}");
                lines.Add($"   Reason: {ev.reason_code ?? "OK"}");
            }

            if (eventDetailsText != null)
                eventDetailsText.text = string.Join("\n", lines);
        }

        public void Hide()
        {
            if (panelRoot != null)
                panelRoot.SetActive(false);
        }
    }
}
