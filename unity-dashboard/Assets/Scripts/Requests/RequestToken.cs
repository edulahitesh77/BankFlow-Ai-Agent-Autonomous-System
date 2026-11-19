using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using BankFlowAI.Data;
using BankFlowAI.Managers;

namespace BankFlowAI.Requests
{
    public class RequestToken : MonoBehaviour
    {
        [Header("UI Card Elements")]
        public Text requestIdText;
        public Text serviceTypeText;
        public Image serviceTypeBadgeBg;
        public Text priorityText;
        public Image priorityBadgeBg;
        public Text assignedAgentText;
        public Text retryCountText;
        public Button clickButton;

        [Header("Runtime State")]
        public RequestData currentData;
        public Vector3 targetPosition;
        public float moveSpeed = 6.0f;

        // Service Type Colors
        private static readonly Color ColorChequeBook = new Color(0.39f, 0.40f, 0.95f);     // #6366F1 Indigo
        private static readonly Color ColorDebitCard = new Color(0.08f, 0.72f, 0.65f);      // #14B8A6 Teal
        private static readonly Color ColorAddress = new Color(0.23f, 0.51f, 0.96f);        // #3B82F6 Blue
        private static readonly Color ColorApplication = new Color(0.55f, 0.36f, 0.96f);    // #8B5CF6 Purple

        private Coroutine moveCoroutine;

        private void Awake()
        {
            if (clickButton != null)
            {
                clickButton.onClick.AddListener(OnClickToken);
            }
        }

        public void UpdateData(RequestData data, Vector3 newTargetPosition)
        {
            currentData = data;
            targetPosition = newTargetPosition;

            if (requestIdText != null)
                requestIdText.text = data.request_id;

            if (serviceTypeText != null)
            {
                string shortSvc = data.service_type.Replace("_", " ");
                serviceTypeText.text = shortSvc;
            }

            if (serviceTypeBadgeBg != null)
                serviceTypeBadgeBg.color = GetServiceColor(data.service_type);

            if (priorityText != null)
                priorityText.text = data.priority;

            if (priorityBadgeBg != null)
            {
                priorityBadgeBg.color = data.priority == "HIGH" 
                    ? new Color(0.94f, 0.27f, 0.27f) // Red
                    : new Color(0.24f, 0.60f, 0.96f); // Blue
            }

            if (assignedAgentText != null)
            {
                assignedAgentText.text = string.IsNullOrEmpty(data.assigned_agent)
                    ? "UNASSIGNED"
                    : data.assigned_agent;
            }

            if (retryCountText != null)
            {
                retryCountText.gameObject.SetActive(data.retry_count > 0);
                retryCountText.text = $"Retries: {data.retry_count}";
            }

            // Smooth movement to target stage slot
            if (moveCoroutine != null)
                StopCoroutine(moveCoroutine);

            moveCoroutine = StartCoroutine(SmoothMoveTo(targetPosition));
        }

        private IEnumerator SmoothMoveTo(Vector3 destination)
        {
            RectTransform rect = transform as RectTransform;
            if (rect == null)
            {
                transform.position = destination;
                yield break;
            }

            float duration = 0.35f;
            float elapsed = 0f;
            Vector3 startPos = rect.localPosition;

            while (elapsed < duration)
            {
                elapsed += Time.deltaTime;
                float t = Mathf.SmoothStep(0f, 1f, elapsed / duration);
                rect.localPosition = Vector3.Lerp(startPos, destination, t);
                yield return null;
            }

            rect.localPosition = destination;
        }

        private void OnClickToken()
        {
            if (currentData != null && UIManager.Instance != null)
            {
                UIManager.Instance.InspectRequest(currentData.request_id);
            }
        }

        private Color GetServiceColor(string serviceType)
        {
            switch (serviceType)
            {
                case "CHEQUE_BOOK": return ColorChequeBook;
                case "DEBIT_CARD_REPLACEMENT": return ColorDebitCard;
                case "ADDRESS_UPDATE": return ColorAddress;
                case "ACCOUNT_APPLICATION": return ColorApplication;
                default: return ColorAddress;
            }
        }
    }
}
