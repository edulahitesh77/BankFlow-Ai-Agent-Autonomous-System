using UnityEngine;
using UnityEngine.UI;
using BankFlowAI.Managers;

namespace BankFlowAI.UI
{
    public class TopNavBar : MonoBehaviour
    {
        [Header("Text Displays")]
        public Text titleText;
        public Text tickDisplayText;
        public Text modeBadgeText;
        public Image modeBadgeBg;
        public Text statusBadgeText;
        public Image statusBadgeBg;

        [Header("Playback Control Buttons")]
        public Button playButton;
        public Button pauseButton;
        public Button stepBackButton;
        public Button stepFwdButton;
        public Button resetButton;

        [Header("Speed Buttons")]
        public Button speedHalfBtn;
        public Button speed1xBtn;
        public Button speed2xBtn;
        public Button speed5xBtn;

        [Header("Mode Switcher")]
        public Button modeToggleBtn;

        private void Start()
        {
            // Wire buttons
            if (playButton != null) playButton.onClick.AddListener(OnPlayClicked);
            if (pauseButton != null) pauseButton.onClick.AddListener(OnPauseClicked);
            if (stepBackButton != null) stepBackButton.onClick.AddListener(OnStepBackClicked);
            if (stepFwdButton != null) stepFwdButton.onClick.AddListener(OnStepFwdClicked);
            if (resetButton != null) resetButton.onClick.AddListener(OnResetClicked);

            if (speedHalfBtn != null) speedHalfBtn.onClick.AddListener(() => SetSpeed(0.5f));
            if (speed1xBtn != null) speed1xBtn.onClick.AddListener(() => SetSpeed(1.0f));
            if (speed2xBtn != null) speed2xBtn.onClick.AddListener(() => SetSpeed(2.0f));
            if (speed5xBtn != null) speed5xBtn.onClick.AddListener(() => SetSpeed(5.0f));

            if (modeToggleBtn != null) modeToggleBtn.onClick.AddListener(ToggleMode);

            if (SimulationManager.Instance != null)
            {
                SimulationManager.Instance.OnPlaybackStateChanged += HandlePlaybackStateChanged;
                SimulationManager.Instance.OnModeChanged += HandleModeChanged;
            }

            UpdateDisplay();
        }

        private void OnDestroy()
        {
            if (SimulationManager.Instance != null)
            {
                SimulationManager.Instance.OnPlaybackStateChanged -= HandlePlaybackStateChanged;
                SimulationManager.Instance.OnModeChanged -= HandleModeChanged;
            }
        }

        public void UpdateTickDisplay(int current, int total)
        {
            if (tickDisplayText != null)
            {
                tickDisplayText.text = $"TICK: {current:D2} / {Mathf.Max(0, total - 1):D2}";
            }
        }

        private void HandlePlaybackStateChanged(PlaybackState state)
        {
            if (statusBadgeText != null)
            {
                statusBadgeText.text = state.ToString().ToUpper();
            }
            if (statusBadgeBg != null)
            {
                statusBadgeBg.color = state == PlaybackState.Playing 
                    ? new Color(0.06f, 0.73f, 0.51f) // Green
                    : new Color(0.96f, 0.62f, 0.04f); // Amber
            }
        }

        private void HandleModeChanged(VisualizationMode mode)
        {
            if (modeBadgeText != null)
            {
                modeBadgeText.text = mode == VisualizationMode.RecordedReplay ? "RECORDED REPLAY" : "LIVE MONITORING";
            }
            if (modeBadgeBg != null)
            {
                modeBadgeBg.color = mode == VisualizationMode.RecordedReplay 
                    ? new Color(0.24f, 0.60f, 0.96f) // Blue
                    : new Color(0.55f, 0.36f, 0.96f); // Purple
            }
        }

        private void UpdateDisplay()
        {
            if (SimulationManager.Instance != null)
            {
                HandlePlaybackStateChanged(SimulationManager.Instance.playbackState);
                HandleModeChanged(SimulationManager.Instance.currentMode);
                UpdateTickDisplay(SimulationManager.Instance.currentTickIndex, SimulationManager.Instance.totalTicks);
            }
        }

        private void OnPlayClicked() => SimulationManager.Instance?.Play();
        private void OnPauseClicked() => SimulationManager.Instance?.Pause();
        private void OnStepBackClicked() => SimulationManager.Instance?.StepBackward();
        private void OnStepFwdClicked() => SimulationManager.Instance?.StepForward();
        private void OnResetClicked() => SimulationManager.Instance?.ResetToStart();

        private void SetSpeed(float spd)
        {
            SimulationManager.Instance?.SetPlaybackSpeed(spd);
        }

        private void ToggleMode()
        {
            if (SimulationManager.Instance == null) return;
            var nextMode = SimulationManager.Instance.currentMode == VisualizationMode.RecordedReplay
                ? VisualizationMode.LiveMonitoring
                : VisualizationMode.RecordedReplay;
            SimulationManager.Instance.SetMode(nextMode);
        }
    }
}
