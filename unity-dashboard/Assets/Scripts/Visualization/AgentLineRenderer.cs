using System.Collections;
using UnityEngine;
using UnityEngine.UI;

namespace BankFlowAI.Visualization
{
    public class AgentLineRenderer : MonoBehaviour
    {
        [Header("Line Components")]
        public Image lineImage;
        public RectTransform lineRect;

        [Header("Appearance")]
        public Color activeColor = new Color(0.24f, 0.60f, 0.96f, 0.8f); // #3B82F6
        public Color idleColor = new Color(0.2f, 0.25f, 0.35f, 0.25f);

        private void Awake()
        {
            if (lineRect == null) lineRect = GetComponent<RectTransform>();
            if (lineImage == null) lineImage = GetComponent<Image>();
        }

        public void Connect(Vector2 startPos, Vector2 endPos, bool isActive = false)
        {
            if (lineRect == null) return;

            Vector2 diff = endPos - startPos;
            float distance = diff.magnitude;
            float angle = Mathf.Atan2(diff.y, diff.x) * Mathf.Rad2Deg;

            lineRect.pivot = new Vector2(0f, 0.5f);
            lineRect.anchoredPosition = startPos;
            lineRect.sizeDelta = new Vector2(distance, isActive ? 4f : 1.5f);
            lineRect.rotation = Quaternion.Euler(0f, 0f, angle);

            if (lineImage != null)
            {
                lineImage.color = isActive ? activeColor : idleColor;
            }
        }

        public void PulseActive()
        {
            StartCoroutine(PulseEffect());
        }

        private IEnumerator PulseEffect()
        {
            if (lineImage == null) yield break;

            float duration = 0.4f;
            float elapsed = 0f;

            while (elapsed < duration)
            {
                elapsed += Time.deltaTime;
                float alpha = Mathf.Sin((elapsed / duration) * Mathf.PI);
                lineImage.color = Color.Lerp(idleColor, activeColor, alpha);
                yield return null;
            }

            lineImage.color = idleColor;
        }
    }
}
