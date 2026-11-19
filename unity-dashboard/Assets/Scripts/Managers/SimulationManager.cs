using System;
using System.IO;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using BankFlowAI.Data;

namespace BankFlowAI.Managers
{
    public enum VisualizationMode
    {
        RecordedReplay,
        LiveMonitoring
    }

    public enum PlaybackState
    {
        Playing,
        Paused,
        Stopped
    }

    public class SimulationManager : MonoBehaviour
    {
        public static SimulationManager Instance { get; private set; }

        [Header("Visualization Mode")]
        public VisualizationMode currentMode = VisualizationMode.RecordedReplay;
        public PlaybackState playbackState = PlaybackState.Paused;

        [Header("Replay Settings")]
        [Tooltip("Path relative to Application.streamingAssetsPath or Assets/Data")]
        public string replayFileName = "sample_simulation.json";
        public float baseTickDuration = 1.0f; // Seconds per tick at 1x
        public float playbackSpeed = 1.0f; // 0.5x, 1x, 2x, 5x

        [Header("Runtime State")]
        public int currentTickIndex = 0;
        public int totalTicks = 0;
        public SimulationManifest activeManifest;
        public SimulationSnapshot currentSnapshot;

        // Events for UI and components
        public event Action<int, SimulationSnapshot> OnTickChanged;
        public event Action<SimulationManifest> OnManifestLoaded;
        public event Action<VisualizationMode> OnModeChanged;
        public event Action<PlaybackState> OnPlaybackStateChanged;
        public event Action<float> OnSpeedChanged;

        private Coroutine replayCoroutine;

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
            // Initial load of recorded benchmark data
            LoadReplayFile(replayFileName);
        }

        /// <summary>
        /// Loads and parses simulation manifest JSON from disk.
        /// </summary>
        public bool LoadReplayFile(string fileName)
        {
            string filePath = Path.Combine(Application.dataPath, "Data", fileName);
            if (!File.Exists(filePath))
            {
                filePath = Path.Combine(Application.streamingAssetsPath, fileName);
            }

            if (!File.Exists(filePath))
            {
                Debug.LogWarning($"[SimulationManager] File not found: {filePath}. Attempting fallback path.");
                // Direct relative fallback
                filePath = Path.Combine(Directory.GetCurrentDirectory(), "Assets", "Data", fileName);
            }

            if (!File.Exists(filePath))
            {
                Debug.LogError($"[SimulationManager] Unable to locate simulation replay file at {filePath}");
                return false;
            }

            try
            {
                string jsonText = File.ReadAllText(filePath);
                SimulationManifest manifest = JsonUtility.FromJson<SimulationManifest>(jsonText);

                if (!manifest.IsValid(out string error))
                {
                    Debug.LogError($"[SimulationManager] JSON Manifest validation error: {error}");
                    return false;
                }

                activeManifest = manifest;
                totalTicks = manifest.snapshots.Count;
                currentTickIndex = 0;

                Debug.Log($"[SimulationManager] Successfully loaded manifest '{manifest.scenario_name}' ({totalTicks} ticks, {manifest.events.Count} events, schema {manifest.schema_version})");

                OnManifestLoaded?.Invoke(activeManifest);
                SetTick(0);
                return true;
            }
            catch (Exception ex)
            {
                Debug.LogError($"[SimulationManager] Exception parsing replay JSON: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Updates the current simulation tick and broadcasts snapshot data.
        /// Purely client-side visualization; never mutates database.
        /// </summary>
        public void SetTick(int tick)
        {
            if (activeManifest == null || activeManifest.snapshots.Count == 0)
                return;

            currentTickIndex = Mathf.Clamp(tick, 0, activeManifest.snapshots.Count - 1);
            currentSnapshot = activeManifest.snapshots[currentTickIndex];

            OnTickChanged?.Invoke(currentTickIndex, currentSnapshot);
        }

        public void Play()
        {
            if (playbackState == PlaybackState.Playing)
                return;

            playbackState = PlaybackState.Playing;
            OnPlaybackStateChanged?.Invoke(playbackState);

            if (replayCoroutine != null)
                StopCoroutine(replayCoroutine);

            replayCoroutine = StartCoroutine(PlaybackLoop());
        }

        public void Pause()
        {
            playbackState = PlaybackState.Paused;
            OnPlaybackStateChanged?.Invoke(playbackState);

            if (replayCoroutine != null)
            {
                StopCoroutine(replayCoroutine);
                replayCoroutine = null;
            }
        }

        public void StepForward()
        {
            Pause();
            if (activeManifest != null && currentTickIndex < activeManifest.snapshots.Count - 1)
            {
                SetTick(currentTickIndex + 1);
            }
        }

        public void StepBackward()
        {
            Pause();
            if (currentTickIndex > 0)
            {
                SetTick(currentTickIndex - 1);
            }
        }

        public void ResetToStart()
        {
            Pause();
            SetTick(0);
        }

        public void SetPlaybackSpeed(float speed)
        {
            playbackSpeed = Mathf.Clamp(speed, 0.25f, 5.0f);
            OnSpeedChanged?.Invoke(playbackSpeed);
        }

        public void SetMode(VisualizationMode mode)
        {
            currentMode = mode;
            Pause();
            OnModeChanged?.Invoke(currentMode);

            if (currentMode == VisualizationMode.LiveMonitoring)
            {
                Debug.Log("[SimulationManager] Switched to LIVE MONITORING mode (FastAPI sync).");
            }
            else
            {
                Debug.Log("[SimulationManager] Switched to RECORDED REPLAY mode.");
            }
        }

        private IEnumerator PlaybackLoop()
        {
            while (playbackState == PlaybackState.Playing)
            {
                float delay = baseTickDuration / Mathf.Max(0.1f, playbackSpeed);
                yield return new WaitForSeconds(delay);

                if (activeManifest == null || activeManifest.snapshots.Count == 0)
                    yield break;

                if (currentTickIndex >= activeManifest.snapshots.Count - 1)
                {
                    // Reached end of replay
                    Pause();
                    yield break;
                }

                SetTick(currentTickIndex + 1);
            }
        }
    }
}
