using System.Collections.Generic;
using UnityEngine;
using BankFlowAI.Data;
using BankFlowAI.Requests;

namespace BankFlowAI.Managers
{
    public class WorkflowManager : MonoBehaviour
    {
        public static WorkflowManager Instance { get; private set; }

        [Header("Stage Areas (8 Stages)")]
        public WorkflowStageArea stageCustomer;
        public WorkflowStageArea stageIntake;
        public WorkflowStageArea stageAssignment;
        public WorkflowStageArea stageVerification;
        public WorkflowStageArea stageService;
        public WorkflowStageArea stageCorrection;
        public WorkflowStageArea stageHumanReview;
        public WorkflowStageArea stageFinished;

        [Header("Token Pooling")]
        public GameObject requestTokenPrefab;
        public Transform tokensParent;

        private readonly Dictionary<string, RequestToken> activeTokens = new Dictionary<string, RequestToken>();
        private readonly List<RequestToken> tokenPool = new List<RequestToken>();

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
            if (snapshot == null) return;

            HashSet<string> currentReqIds = new HashSet<string>();

            // Group requests by stage to calculate vertical slot stacking
            Dictionary<string, List<RequestData>> requestsByStage = new Dictionary<string, List<RequestData>>();

            foreach (var req in snapshot.active_requests)
            {
                currentReqIds.Add(req.request_id);
                string stage = req.stage ?? "STAGE_1_CUSTOMER";
                if (!requestsByStage.ContainsKey(stage))
                {
                    requestsByStage[stage] = new List<RequestData>();
                }
                requestsByStage[stage].Add(req);
            }

            // Position tokens within their corresponding stage zones
            foreach (var kvp in requestsByStage)
            {
                string stageKey = kvp.Key;
                List<RequestData> reqList = kvp.Value;
                WorkflowStageArea stageArea = GetStageArea(stageKey);

                for (int slot = 0; slot < reqList.Count; slot++)
                {
                    RequestData req = reqList[slot];
                    RequestToken token = GetOrCreateToken(req.request_id);

                    Vector3 targetPos = stageArea != null 
                        ? stageArea.GetSlotPosition(slot) 
                        : Vector3.zero;

                    token.UpdateData(req, targetPos);
                }
            }

            // Recycle tokens for requests no longer in active snapshot
            List<string> toRemove = new List<string>();
            foreach (var kvp in activeTokens)
            {
                if (!currentReqIds.Contains(kvp.Key))
                {
                    toRemove.Add(kvp.Key);
                }
            }

            foreach (var id in toRemove)
            {
                RequestToken token = activeTokens[id];
                token.gameObject.SetActive(false);
                tokenPool.Add(token);
                activeTokens.Remove(id);
            }
        }

        private RequestToken GetOrCreateToken(string requestId)
        {
            if (activeTokens.TryGetValue(requestId, out RequestToken token))
            {
                token.gameObject.SetActive(true);
                return token;
            }

            if (tokenPool.Count > 0)
            {
                token = tokenPool[tokenPool.Count - 1];
                tokenPool.RemoveAt(tokenPool.Count - 1);
                token.gameObject.SetActive(true);
                activeTokens[requestId] = token;
                return token;
            }

            GameObject go = requestTokenPrefab != null 
                ? Instantiate(requestTokenPrefab, tokensParent) 
                : new GameObject($"RequestToken_{requestId}", typeof(RectTransform));

            if (tokensParent != null) go.transform.SetParent(tokensParent, false);

            token = go.GetComponent<RequestToken>() ?? go.AddComponent<RequestToken>();
            activeTokens[requestId] = token;
            return token;
        }

        public WorkflowStageArea GetStageArea(string stageName)
        {
            switch (stageName)
            {
                case "STAGE_1_CUSTOMER": return stageCustomer;
                case "STAGE_2_INTAKE": return stageIntake;
                case "STAGE_3_ASSIGNMENT": return stageAssignment;
                case "STAGE_4_VERIFICATION": return stageVerification;
                case "STAGE_5_SERVICE": return stageService;
                case "STAGE_6_CORRECTION": return stageCorrection;
                case "STAGE_7_HUMAN_REVIEW": return stageHumanReview;
                case "STAGE_8_FINISHED": return stageFinished;
                default: return stageCustomer;
            }
        }
    }
}
