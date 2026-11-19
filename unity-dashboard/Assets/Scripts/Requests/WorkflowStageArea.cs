using UnityEngine;
using UnityEngine.UI;

namespace BankFlowAI.Requests
{
    public class WorkflowStageArea : MonoBehaviour
    {
        [Header("Stage Metadata")]
        public string stageKey; // e.g. "STAGE_1_CUSTOMER"
        public int stageNumber = 1;
        public string stageTitle = "Customer";

        [Header("UI Elements")]
        public Text stageNumberText;
        public Text stageTitleText;
        public Image stageBackground;
        public RectTransform slotsContainer;

        [Header("Layout Parameters")]
        public float startOffsetY = -40f;
        public float slotSpacingY = -75f;
        public float slotOffsetX = 0f;

        private void Awake()
        {
            if (stageNumberText != null)
                stageNumberText.text = $"STAGE {stageNumber}";

            if (stageTitleText != null)
                stageTitleText.text = stageTitle;
        }

        /// <summary>
        /// Calculates the local position for a request token occupying slotIndex.
        /// </summary>
        public Vector3 GetSlotPosition(int slotIndex)
        {
            RectTransform targetContainer = slotsContainer != null ? slotsContainer : (transform as RectTransform);
            if (targetContainer == null) return transform.position;

            Vector3 basePos = targetContainer.localPosition;
            float yPos = basePos.y + startOffsetY + (slotIndex * slotSpacingY);
            float xPos = basePos.x + slotOffsetX;

            return new Vector3(xPos, yPos, 0f);
        }
    }
}
