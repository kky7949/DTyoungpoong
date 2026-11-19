using System;
using UnityEditor;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace Youngpoong.Integration
{
    [InitializeOnLoad]
    internal static class FactoryIntegrationOfflineCheck
    {
        private const string Key = "Youngpoong.FactoryOfflineQA.";
        private static IntegratedFactoryProcessController process;
        private static Button start, reset;
        private static int completed, failed, resetFrame;
        private static int Stage { get => SessionState.GetInt(Key + "stage", 0); set => SessionState.SetInt(Key + "stage", value); }
        private static bool Active => SessionState.GetBool(Key + "active", false);

        static FactoryIntegrationOfflineCheck()
        {
            if (!Active) return;
            Attach();
            if (Stage > 0) EditorApplication.delayCall += ReloadInterrupted;
        }

        [MenuItem("Youngpoong/Integration/Run Offline Lifecycle Check")]
        private static void Run()
        {
            try
            {
                Require(!EditorApplication.isPlayingOrWillChangePlaymode, "Start this check outside Play mode.");
                Require(!Active, "An offline check is already pending.");
                CheckScene();
                Stage = 0;
                completed = failed = resetFrame = 0;
                SessionState.SetBool(Key + "active", true);
                Deadline(15);
                Attach();
                EditorApplication.isPlaying = true;
            }
            catch (Exception exception) { Debug.LogError("[Factory offline QA] FAIL " + exception.Message); }
        }

        private static void Attach()
        {
            EditorApplication.update -= Tick;
            EditorApplication.playModeStateChanged -= PlayChanged;
            EditorApplication.update += Tick;
            EditorApplication.playModeStateChanged += PlayChanged;
        }

        private static void PlayChanged(PlayModeStateChange state)
        {
            if (!Active) return;
            if (state == PlayModeStateChange.EnteredPlayMode) Deadline(10);
            if (state == PlayModeStateChange.ExitingPlayMode) Finish(false, "Play stopped before the check finished.");
        }

        private static void CheckScene()
        {
            Require(SceneManager.GetActiveScene().name == "FactoryDemoExhibitionApi", "Open FactoryDemoExhibitionApi first.");
            var clients = UnityEngine.Object.FindObjectsByType<FastApiFactoryClient>(FindObjectsInactive.Include, FindObjectsSortMode.None);
            Require(clients.Length == 1, "Exactly one factory HTTP client is required.");
            Require(string.IsNullOrWhiteSpace(new SerializedObject(clients[0]).FindProperty("baseUrl").stringValue), "Base URL must be blank; this check must remain offline.");
            var controllers = UnityEngine.Object.FindObjectsByType<IntegratedFactoryProcessController>(FindObjectsInactive.Include, FindObjectsSortMode.None);
            Require(controllers.Length == 1, "Exactly one integrated process controller is required.");
            Require(controllers[0].gameObject.scene == SceneManager.GetActiveScene(), "The controller must belong to the API scene.");
            process = controllers[0];
        }

        private static void Tick()
        {
            if (!Active) return;
            try
            {
                Require(EditorApplication.timeSinceStartup <= SessionState.GetFloat(Key + "deadline", 0), "Timed out at stage " + Stage + ".");
                if (!EditorApplication.isPlaying) return;
                if (Stage == 0)
                {
                    CheckScene();
                    if (!process.IsInitialized) return;
                    var serialized = new SerializedObject(process);
                    start = serialized.FindProperty("startButton").objectReferenceValue as Button;
                    reset = serialized.FindProperty("resetButton").objectReferenceValue as Button;
                    Require(start != null && reset != null, "Start and Reset references are required.");
                    process.ProcessCompleted += OnCompleted;
                    process.ProcessFailed += OnFailed;
                    Stage = 1; Deadline(35);
                    start.onClick.Invoke();
                    Require(process.IsRunning, "Local Start did not start the visual process.");
                }
                else if (Stage == 1)
                {
                    Require(failed == 0, "The local run failed.");
                    if (!process.IsComplete) return;
                    Require(completed == 1 && Mathf.Approximately(process.OverallProgress, 100), "Completion count or final progress is incorrect.");
                    reset.onClick.Invoke();
                    resetFrame = Time.frameCount;
                    Stage = 2; Deadline(5);
                }
                else if (Stage == 2)
                {
                    if (Time.frameCount <= resetFrame) return;
                    Require(process.IsInitialized && !process.IsRunning && !process.IsComplete && Mathf.Approximately(process.OverallProgress, 0), "Reset did not remain Ready at zero progress.");
                    Require(start.interactable && !reset.interactable, "Reset did not restore Ready button states.");
                    process.SetApiControl(true);
                    string reason;
                    Require(process.TryStartApiProcess(out reason), "API-owned start failed: " + reason);
                    Require(!start.interactable && !reset.interactable, "API ownership did not disable both local buttons.");
                    reset.onClick.Invoke();
                    Require(process.IsRunning, "A local Reset interrupted the API-owned run.");
                    Stage = 3; Deadline(5);
                    process.enabled = false; // Deliberate interruption: the controller logs an expected error.
                    Require(failed == 1 && !process.IsRunning, "Disable did not emit exactly one failure and stop the run.");
                }
                else
                {
                    Require(failed == 1 && completed == 1 && !process.IsRunning && !process.IsComplete, "Interrupted run produced a duplicate or false terminal event.");
                    Finish(true, "local Start/completion/Reset, API control lock, and one-shot interruption verified in Unity; no HTTP round trip.");
                }
            }
            catch (Exception exception) { Finish(false, exception.Message); }
        }

        private static void OnCompleted() { completed++; }
        private static void OnFailed(string reason) { failed++; }
        private static void ReloadInterrupted() { if (Active) Finish(false, "Scripts reloaded during execution; rerun the check."); }
        private static void Deadline(float seconds) { SessionState.SetFloat(Key + "deadline", (float)(EditorApplication.timeSinceStartup + seconds)); }
        private static void Require(bool condition, string reason) { if (!condition) throw new InvalidOperationException(reason); }

        private static void Finish(bool pass, string message)
        {
            SessionState.SetBool(Key + "active", false);
            EditorApplication.update -= Tick;
            EditorApplication.playModeStateChanged -= PlayChanged;
            EditorApplication.delayCall -= ReloadInterrupted;
            if (process != null) { process.ProcessCompleted -= OnCompleted; process.ProcessFailed -= OnFailed; }
            if (pass) Debug.Log("[Factory offline QA] PASS " + message);
            else Debug.LogError("[Factory offline QA] FAIL " + message);
            if (EditorApplication.isPlayingOrWillChangePlaymode) EditorApplication.isPlaying = false;
        }
    }
}
