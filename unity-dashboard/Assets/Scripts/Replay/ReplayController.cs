using UnityEngine;
using BankFlowAI.Managers;

namespace BankFlowAI.Replay
{
    public class ReplayController : MonoBehaviour
    {
        public static ReplayController Instance { get; private set; }

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
        }

        public void Play() => SimulationManager.Instance?.Play();
        public void Pause() => SimulationManager.Instance?.Pause();
        public void StepForward() => SimulationManager.Instance?.StepForward();
        public void StepBackward() => SimulationManager.Instance?.StepBackward();
        public void Reset() => SimulationManager.Instance?.ResetToStart();
        public void SetSpeed(float speed) => SimulationManager.Instance?.SetPlaybackSpeed(speed);
        public void JumpToTick(int tick) => SimulationManager.Instance?.SetTick(tick);
    }
}
