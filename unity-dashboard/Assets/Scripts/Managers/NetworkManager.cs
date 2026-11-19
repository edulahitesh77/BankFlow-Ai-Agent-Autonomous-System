using System;
using System.Collections;
using UnityEngine;
using UnityEngine.Networking;
using BankFlowAI.Data;

namespace BankFlowAI.Managers
{
    public class NetworkManager : MonoBehaviour
    {
        public static NetworkManager Instance { get; private set; }

        [Header("FastAPI Connection")]
        public string baseUrl = "http://127.0.0.1:8000";
        public string authToken = "";
        public float pollingInterval = 1.0f;

        [Header("Status")]
        public bool isConnected = false;
        public string lastError = "";

        public event Action<bool, string> OnConnectionStatusChanged;
        public event Action<SimulationSnapshot> OnLiveSnapshotReceived;

        private Coroutine pollingCoroutine;

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
                SimulationManager.Instance.OnModeChanged += HandleModeChanged;
            }
        }

        private void OnDestroy()
        {
            if (SimulationManager.Instance != null)
            {
                SimulationManager.Instance.OnModeChanged -= HandleModeChanged;
            }
        }

        private void HandleModeChanged(VisualizationMode mode)
        {
            if (mode == VisualizationMode.LiveMonitoring)
            {
                StartPolling();
            }
            else
            {
                StopPolling();
            }
        }

        public void StartPolling()
        {
            StopPolling();
            pollingCoroutine = StartCoroutine(PollLiveEndpoint());
        }

        public void StopPolling()
        {
            if (pollingCoroutine != null)
            {
                StopCoroutine(pollingCoroutine);
                pollingCoroutine = null;
            }
        }

        private IEnumerator PollLiveEndpoint()
        {
            string url = $"{baseUrl.TrimEnd('/')}/api/bank/simulation/snapshot";

            while (true)
            {
                using (UnityWebRequest req = UnityWebRequest.Get(url))
                {
                    req.timeout = 3;
                    if (!string.IsNullOrEmpty(authToken))
                    {
                        req.SetRequestHeader("Authorization", $"Bearer {authToken}");
                    }

                    yield return req.SendWebRequest();

                    if (req.result == UnityWebRequest.Result.Success)
                    {
                        if (!isConnected)
                        {
                            isConnected = true;
                            lastError = "";
                            OnConnectionStatusChanged?.Invoke(true, "Connected to BankFlow AI Backend");
                        }

                        try
                        {
                            SimulationSnapshot snapshot = JsonUtility.FromJson<SimulationSnapshot>(req.downloadHandler.text);
                            if (snapshot != null)
                            {
                                OnLiveSnapshotReceived?.Invoke(snapshot);
                            }
                        }
                        catch (Exception ex)
                        {
                            Debug.LogWarning($"[NetworkManager] Snapshot parsing error: {ex.Message}");
                        }
                    }
                    else
                    {
                        isConnected = false;
                        lastError = req.error;
                        OnConnectionStatusChanged?.Invoke(false, req.error);
                    }
                }

                yield return new WaitForSeconds(pollingInterval);
            }
        }
    }
}
