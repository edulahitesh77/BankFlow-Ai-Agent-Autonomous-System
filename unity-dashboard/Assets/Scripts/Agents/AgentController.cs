using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using BankFlowAI.Data;
using BankFlowAI.Managers;

namespace BankFlowAI.Agents
{
    public class AgentController : MonoBehaviour
    {
        [Header("UI References")]
        public Text agentCodeText;
        public Text agentTypeText;
        public Text statusBadgeText;
        public Image statusBadgeBg;
        public Text completedCountText;
        public Text currentRequestText;
        public Image pulseRing;
        public Button clickButton;

        [Header("State Data")]
        public AgentData currentData;

        // Status Colors matching BankFlow AI backend specification
        private static readonly Color ColorHealthy = new Color(0.06f, 0.73f, 0.51f);      // #10B981 Emerald
        private static readonly Color ColorBusy = new Color(0.02f, 0.71f, 0.83f);         // #06B6D4 Cyan
        private static readonly Color ColorIdle = new Color(0.39f, 0.45f, 0.55f);         // #64748B Slate
        private static readonly Color ColorUnresponsive = new Color(0.96f, 0.62f, 0.04f); // #F59E0B Amber
        private static readonly Color ColorFailed = new Color(0.94f, 0.27f, 0.27f);       // #EF4444 Red
        private static readonly Color ColorRecovering = new Color(0.98f, 0.45f, 0.09f);   // #F97316 Orange

        private void Awake()
        {
            if (clickButton != null)
            {
                clickButton.onClick.AddListener(OnClickAgent);
            }
        }

        public void UpdateAgentState(AgentData data)
        {
            currentData = data;

            if (agentCodeText != null)
                agentCodeText.text = data.agent_code;

            if (agentTypeText != null)
                agentTypeText.text = data.agent_type.Replace("_AGENT", "");

            if (completedCountText != null)
                completedCountText.text = $"Done: {data.completed_count}";

            if (currentRequestText != null)
            {
                currentRequestText.text = string.IsNullOrEmpty(data.current_request_id)
                    ? "IDLE"
                    : $"Task: {data.current_request_id}";
            }

            // Determine badge color and label
            string displayStatus = data.processing_status == "BUSY" ? "BUSY" : data.health_status;
            Color badgeColor = GetStatusColor(displayStatus);

            if (statusBadgeText != null)
                statusBadgeText.text = displayStatus;

            if (statusBadgeBg != null)
                statusBadgeBg.color = badgeColor;
        }

        public void TriggerMessagePulse()
        {
            StartCoroutine(PulseAnimation());
        }

        private IEnumerator PulseAnimation()
        {
            if (pulseRing == null) yield break;

            pulseRing.gameObject.SetActive(true);
            Transform ringTransform = pulseRing.transform;
            Color ringColor = pulseRing.color;

            float duration = 0.5f;
            float elapsed = 0f;

            while (elapsed < duration)
            {
                elapsed += Time.deltaTime;
                float progress = elapsed / duration;
                float scale = Mathf.Lerp(1.0f, 1.8f, progress);
                float alpha = Mathf.Lerp(1.0f, 0.0f, progress);

                ringTransform.localScale = new Vector3(scale, scale, 1f);
                pulseRing.color = new Color(ringColor.r, ringColor.g, ringColor.b, alpha);
                yield return null;
            }

            pulseRing.gameObject.SetActive(false);
        }

        private void OnClickAgent()
        {
            if (currentData != null && UIManager.Instance != null)
            {
                UIManager.Instance.InspectAgent(currentData.agent_code);
            }
        }

        private Color GetStatusColor(string status)
        {
            switch (status)
            {
                case "BUSY": return ColorBusy;
                case "HEALTHY": return ColorHealthy;
                case "IDLE": return ColorIdle;
                case "UNRESPONSIVE": return ColorUnresponsive;
                case "FAILED": return ColorFailed;
                case "RECOVERING": return ColorRecovering;
                default: return ColorIdle;
            }
        }
    }
}
