using UnityEngine;
using UnityEngine.UI;
using BankFlowAI.Data;

namespace BankFlowAI.UI
{
    public class MetricsPanel : MonoBehaviour
    {
        [Header("Authoritative Metrics Display")]
        public Text totalRequestsText;
        public Text completedRequestsText;
        public Text failedRequestsText;
        public Text pendingRequestsText;
        public Text humanReviewRequestsText;
        public Text recoveredRequestsText;

        [Header("Performance Telemetry")]
        public Text avgWaitingTimeText;
        public Text avgCompletionTimeText;
        public Text throughputText;
        public Text agentUtilizationText;
        public Text messageIntegrityText;

        public void UpdateMetrics(SimulationMetrics metrics)
        {
            if (metrics == null) return;

            if (totalRequestsText != null)
                totalRequestsText.text = metrics.total_requests.ToString();

            if (completedRequestsText != null)
                completedRequestsText.text = metrics.completed_requests.ToString();

            if (failedRequestsText != null)
                failedRequestsText.text = metrics.failed_requests.ToString();

            if (pendingRequestsText != null)
                pendingRequestsText.text = metrics.pending_requests.ToString();

            if (humanReviewRequestsText != null)
                humanReviewRequestsText.text = metrics.human_review_requests.ToString();

            if (recoveredRequestsText != null)
                recoveredRequestsText.text = metrics.recovered_requests.ToString();

            if (avgWaitingTimeText != null)
                avgWaitingTimeText.text = $"{metrics.avg_waiting_time_ticks:F2} ticks";

            if (avgCompletionTimeText != null)
                avgCompletionTimeText.text = $"{metrics.avg_completion_time_ticks:F2} ticks";

            if (throughputText != null)
                throughputText.text = $"{metrics.throughput_per_minute:F1} req/min";

            if (agentUtilizationText != null)
                agentUtilizationText.text = $"{metrics.request_agent_utilization * 100f:F1}%";

            if (messageIntegrityText != null)
                messageIntegrityText.text = $"{metrics.message_integrity_rate:F1}%";
        }
    }
}
