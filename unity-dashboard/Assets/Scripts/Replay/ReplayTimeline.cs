using UnityEngine;
using UnityEngine.UI;
using BankFlowAI.Data;
using BankFlowAI.Managers;

namespace BankFlowAI.Replay
{
    public class ReplayTimeline : MonoBehaviour
    {
        [Header("UI Slider")]
        public Slider timelineSlider;
        public Text currentTickText;
        public Text maxTickText;

        private bool isDragging = false;

        private void Start()
        {
            if (timelineSlider != null)
            {
                timelineSlider.onValueChanged.AddListener(OnSliderValueChanged);
            }

            if (SimulationManager.Instance != null)
            {
                SimulationManager.Instance.OnManifestLoaded += HandleManifestLoaded;
                SimulationManager.Instance.OnTickChanged += HandleTickChanged;
            }
        }

        private void OnDestroy()
        {
            if (SimulationManager.Instance != null)
            {
                SimulationManager.Instance.OnManifestLoaded -= HandleManifestLoaded;
                SimulationManager.Instance.OnTickChanged -= HandleTickChanged;
            }
        }

        private void HandleManifestLoaded(SimulationManifest manifest)
        {
            if (timelineSlider != null && manifest != null)
            {
                timelineSlider.minValue = 0;
                timelineSlider.maxValue = Mathf.Max(0, manifest.snapshots.Count - 1);
                timelineSlider.value = 0;

                if (maxTickText != null)
                {
                    maxTickText.text = $"Tick {manifest.snapshots.Count - 1}";
                }
            }
        }

        private void HandleTickChanged(int tick, SimulationSnapshot snapshot)
        {
            if (!isDragging && timelineSlider != null)
            {
                timelineSlider.SetValueWithoutNotify(tick);
                if (currentTickText != null)
                {
                    currentTickText.text = $"Tick {tick}";
                }
            }
        }

        private void OnSliderValueChanged(float val)
        {
            int targetTick = Mathf.RoundToInt(val);
            if (currentTickText != null)
            {
                currentTickText.text = $"Tick {targetTick}";
            }
            SimulationManager.Instance?.SetTick(targetTick);
        }
    }
}
