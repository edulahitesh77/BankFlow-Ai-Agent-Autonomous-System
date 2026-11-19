using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using BankFlowAI.Data;

namespace BankFlowAI.Managers
{
    public class FederationManager : MonoBehaviour
    {
        public static FederationManager Instance { get; private set; }

        [Header("Branch UI Containers")]
        public RectTransform blrBranchNode;
        public RectTransform cheBranchNode;
        public RectTransform hydBranchNode;
        public RectTransform gatewayNode;

        [Header("Telemetry Counters")]
        public Text totalExchangesText;
        public Text authorizedExchangesText;
        public Text rejectedExchangesText;
        public Text lastFederationEventText;

        [Header("Inter-Branch Communication Packet")]
        public GameObject federationPacketPrefab;
        public Transform packetParent;

        private int exchangeCount = 0;
        private int authCount = 0;
        private int rejCount = 0;

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
                SimulationManager.Instance.OnTickChanged += HandleTick;
            }
        }

        private void OnDestroy()
        {
            if (SimulationManager.Instance != null)
            {
                SimulationManager.Instance.OnManifestLoaded -= HandleManifestLoaded;
                SimulationManager.Instance.OnTickChanged -= HandleTick;
            }
        }

        private void HandleManifestLoaded(SimulationManifest manifest)
        {
            if (manifest == null) return;
            exchangeCount = manifest.federation_events.Count;
            authCount = manifest.federation_events.FindAll(e => e.authorization_result == "AUTHORIZED").Count;
            rejCount = manifest.federation_events.FindAll(e => e.authorization_result != "AUTHORIZED").Count;

            UpdateUI();
        }

        private void HandleTick(int tick, SimulationSnapshot snapshot)
        {
            if (SimulationManager.Instance?.activeManifest == null) return;

            // Check if any federation events are simulated at this tick
            var fedEvents = SimulationManager.Instance.activeManifest.federation_events;
            foreach (var fe in fedEvents)
            {
                // In benchmark replay:
                // Tick 4: BLR -> CHE
                // Tick 6: BLR -> HYD
                // Tick 10: EXT -> BLR (Probe)
                if ((tick == 4 && fe.source_branch_id == "BLR001" && fe.destination_branch_id == "CHE001") ||
                    (tick == 6 && fe.source_branch_id == "BLR001" && fe.destination_branch_id == "HYD001") ||
                    (tick == 10 && fe.authorization_result != "AUTHORIZED"))
                {
                    AnimateFederationExchange(fe);
                }
            }
        }

        public void AnimateFederationExchange(FederationEventData fe)
        {
            RectTransform srcNode = GetBranchNode(fe.source_branch_id);
            RectTransform destNode = GetBranchNode(fe.destination_branch_id);

            if (lastFederationEventText != null)
            {
                lastFederationEventText.text = $"[{fe.source_branch_id} -> {fe.destination_branch_id}] {fe.requested_scope}: {fe.authorization_result}";
            }

            if (srcNode != null && destNode != null && gatewayNode != null)
            {
                StartCoroutine(TraverseGateway(srcNode.position, gatewayNode.position, destNode.position, fe.authorization_result == "AUTHORIZED"));
            }
        }

        private IEnumerator TraverseGateway(Vector3 fromPos, Vector3 gatePos, Vector3 toPos, bool isAuthorized)
        {
            GameObject packet = federationPacketPrefab != null
                ? Instantiate(federationPacketPrefab, packetParent != null ? packetParent : transform)
                : new GameObject("FedPacket", typeof(RectTransform), typeof(Image));

            if (packetParent != null) packet.transform.SetParent(packetParent, false);

            Image img = packet.GetComponent<Image>() ?? packet.AddComponent<Image>();
            img.color = isAuthorized ? new Color(0.39f, 0.40f, 0.95f) : new Color(0.94f, 0.27f, 0.27f);
            (packet.transform as RectTransform).sizeDelta = new Vector2(16f, 16f);

            // 1. Source -> Gateway
            float dur = 0.35f;
            float elapsed = 0f;
            while (elapsed < dur)
            {
                elapsed += Time.deltaTime;
                packet.transform.position = Vector3.Lerp(fromPos, gatePos, elapsed / dur);
                yield return null;
            }

            // 2. Gateway -> Destination (if authorized)
            if (isAuthorized)
            {
                elapsed = 0f;
                while (elapsed < dur)
                {
                    elapsed += Time.deltaTime;
                    packet.transform.position = Vector3.Lerp(gatePos, toPos, elapsed / dur);
                    yield return null;
                }
            }

            Destroy(packet);
        }

        private RectTransform GetBranchNode(string branchId)
        {
            switch (branchId?.ToUpper())
            {
                case "BLR001": return blrBranchNode;
                case "CHE001": return cheBranchNode;
                case "HYD001": return hydBranchNode;
                default: return gatewayNode;
            }
        }

        private void UpdateUI()
        {
            if (totalExchangesText != null) totalExchangesText.text = $"Total: {exchangeCount}";
            if (authorizedExchangesText != null) authorizedExchangesText.text = $"Authorized: {authCount}";
            if (rejectedExchangesText != null) rejectedExchangesText.text = $"Rejected: {rejCount}";
        }
    }
}
