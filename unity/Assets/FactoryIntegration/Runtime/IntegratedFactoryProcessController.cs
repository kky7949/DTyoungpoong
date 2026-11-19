using System;
using TMPro;
using UnityEngine;
using UnityEngine.Formats.Alembic.Importer;
using UnityEngine.Rendering.HighDefinition;
using UnityEngine.Serialization;
using UnityEngine.UI;

namespace Youngpoong.Integration
{
    [DisallowMultipleComponent]
    public sealed class IntegratedFactoryProcessController : MonoBehaviour
    {
        private const float SampleFillEndTime = 12f;
        private const float SampleSettledTime = 16f;
        private const float SampleMixAngle = 720f;
        private const float SampleMixCoastSeconds = 1f;
        private static readonly int WaterBaseColorId = Shader.PropertyToID("_BaseColor");

        [SerializeField] private WaterLevelController waterLevelController = null;
        [SerializeField] private Button startButton = null;
        [SerializeField] private Button resetButton = null;
        [SerializeField] private TMP_Text statusText = null;
        [Header("Sample Process")]
        [SerializeField] private AlembicStreamPlayer sampleWaterStream = null;
        [SerializeField] private SkinnedMeshRenderer sampleBatteryParts = null;
        [SerializeField, Range(0f, 100f)] private float targetWaterLevel = 70f;
        [SerializeField, Min(0.1f)] private float sampleFillSeconds = 4f;
        [SerializeField, Min(0.1f)] private float sampleFeedSeconds = 2.5f;
        [SerializeField, Min(0.1f)] private float sampleMixSeconds = 6f;
        [FormerlySerializedAs("sampleColorSeconds")]
        [SerializeField, Min(0.1f)] private float sampleDissolveSeconds = 2f;
        [SerializeField, Min(0.1f)] private float sampleDrainSeconds = 5.5f;
        [SerializeField] private Color sampleDischargeColor = new Color32(96, 32, 24, 174);

        private FactoryProcessPhase state;
        private bool apiControl;
        private bool hasStarted;
        private bool completionReported;
        private bool failureReported;
        private float overallProgress;
        private string failureMessage;

        public bool IsInitialized { get; private set; }
        public bool IsRunning => !failureReported && state != FactoryProcessPhase.Ready &&
            state != FactoryProcessPhase.Complete && state != FactoryProcessPhase.Failed;
        public bool IsComplete => state == FactoryProcessPhase.Complete;
        internal FactoryProcessPhase Phase => state;
        public float OverallProgress => overallProgress;
        public string PhaseMessage => state == FactoryProcessPhase.Failed ? failureMessage : GetExhibitionStatus(state);

        internal event Action ProcessStarted;
        public event Action ProcessCompleted;
        public event Action<string> ProcessFailed;

        private float elapsed;
        private Transform sampleRollBone;
        private Quaternion sampleRollRestRotation;
        private int sampleDropShape;
        private int sampleEndShape;
        private SkinnedMeshRenderer sampleStaticWater;
        private MeshRenderer[] sampleStreamRenderers;
        private MaterialPropertyBlock sampleWaterTintBlock;
        private Vector3 sampleWaterRestPosition;
        private Vector3 sampleWaterRestScale;
        private Vector3 sampleDrainPivotLocal;
        private Vector3 sampleDrainPivotWorld;
        private float sampleDrainCacheStart;
        private Material samplePartsOriginalMaterial;
        private Material samplePartsFadeMaterial;
        private Color samplePartsOriginalColor;

        private void OnEnable()
        {
            try
            {
                if (waterLevelController == null || startButton == null || resetButton == null ||
                    startButton == resetButton || statusText == null)
                    throw new InvalidOperationException("Factory integration requires a water controller, two distinct buttons, and a TMP status text.");

                if (!ResolveSampleRig())
                    throw new InvalidOperationException("Assign the water Alembic stream and Battery_All_01 renderer with Drop, End, and Roll_Bone.");

                startButton.onClick.AddListener(StartProcess);
                resetButton.onClick.AddListener(ResetProcess);
                if (hasStarted && !failureReported)
                    IsInitialized = true;
                UpdateButtons();
            }
            catch (Exception exception)
            {
                FailProcess("Process initialization failed: " + exception.Message, exception);
                enabled = false;
            }
        }

        // Start runs after the water controller has set its own initial level in OnEnable.
        private void Start()
        {
            hasStarted = true;
            try
            {
                sampleRollRestRotation = sampleRollBone.localRotation;
                sampleWaterTintBlock = new MaterialPropertyBlock();
                sampleWaterRestPosition = sampleWaterStream.transform.localPosition;
                sampleWaterRestScale = sampleWaterStream.transform.localScale;
                PrepareSamplePartsFade();

                ResetProcessCore();
                IsInitialized = true;
                UpdateButtons();
            }
            catch (Exception exception)
            {
                FailProcess("Process initialization failed: " + exception.Message, exception);
            }
        }

        private void OnDisable()
        {
            bool interrupted = IsRunning;
            IsInitialized = false;
            if (startButton != null)
                startButton.onClick.RemoveListener(StartProcess);
            if (resetButton != null)
                resetButton.onClick.RemoveListener(ResetProcess);
            if (interrupted)
                FailProcess("Process interrupted because the integrated visual controller was disabled.");
            UpdateButtons();
        }

        private void OnDestroy()
        {
            if (samplePartsFadeMaterial == null)
                return;

            if (sampleBatteryParts != null && sampleBatteryParts.sharedMaterial == samplePartsFadeMaterial)
                sampleBatteryParts.sharedMaterial = samplePartsOriginalMaterial;
            Destroy(samplePartsFadeMaterial);
        }

        private void Update()
        {
            if (!IsInitialized || failureReported)
                return;

            try
            {
                UpdateSampleSequence();
                UpdateOverallProgress();
            }
            catch (Exception exception)
            {
                FailProcess("Visual process failed: " + exception.Message, exception);
            }
        }

        private bool ResolveSampleRig()
        {
            if (sampleWaterStream == null || sampleWaterStream.Duration < SampleSettledTime || sampleBatteryParts == null)
                return false;

            Mesh mesh = sampleBatteryParts.sharedMesh;
            Transform batteryBone = sampleBatteryParts.rootBone;
            if (mesh == null || batteryBone == null)
                return false;

            sampleRollBone = batteryBone.parent;
            sampleStaticWater = waterLevelController.GetComponent<SkinnedMeshRenderer>();
            sampleDropShape = mesh.GetBlendShapeIndex("Drop");
            sampleEndShape = mesh.GetBlendShapeIndex("End");
            return sampleRollBone != null && sampleRollBone.name == "Roll_Bone" &&
                sampleStaticWater != null && sampleDropShape >= 0 && sampleEndShape >= 0;
        }

        private void UpdateSampleSequence()
        {
            switch (state)
            {
                case FactoryProcessPhase.Filling:
                {
                    float progress = AdvanceSamplePhase(sampleFillSeconds);
                    sampleWaterStream.CurrentTime = SampleFillEndTime * progress;
                    waterLevelController.SetWaterLevel(targetWaterLevel * Mathf.InverseLerp(0.15f, 1f, progress));
                    if (progress >= 1f)
                    {
                        elapsed = 0f;
                        SetState(FactoryProcessPhase.Settling);
                    }
                    break;
                }
                case FactoryProcessPhase.Settling:
                {
                    // Integrate a linear speed ramp from the fill speed to 1x, covering cache seconds 12–16.
                    float fillRate = SampleFillEndTime / PhaseDuration(sampleFillSeconds);
                    float seconds = FactoryProcessProgress.SettlingSeconds(sampleFillSeconds);
                    float progress = AdvanceSamplePhase(seconds);
                    float cacheElapsed = seconds * (fillRate * progress + 0.5f * (1f - fillRate) * progress * progress);
                    sampleWaterStream.CurrentTime = progress >= 1f ? SampleSettledTime : SampleFillEndTime + cacheElapsed;
                    if (progress >= 1f)
                    {
                        sampleBatteryParts.enabled = true;
                        elapsed = 0f;
                        SetState(FactoryProcessPhase.Feeding);
                    }
                    break;
                }
                case FactoryProcessPhase.Feeding:
                {
                    float progress = AdvanceSamplePhase(sampleFeedSeconds);
                    sampleWaterStream.CurrentTime = SampleSettledTime + PhaseDuration(sampleFeedSeconds) * progress;
                    sampleBatteryParts.SetBlendShapeWeight(sampleDropShape, Mathf.SmoothStep(0f, 100f, progress));
                    if (progress >= 1f)
                    {
                        sampleStreamRenderers = sampleWaterStream.GetComponentsInChildren<MeshRenderer>(true);
                        elapsed = 0f;
                        SetState(FactoryProcessPhase.Mixing);
                    }
                    break;
                }
                case FactoryProcessPhase.Mixing:
                {
                    float mixDuration = PhaseDuration(sampleMixSeconds);
                    float progress = AdvanceSamplePhase(mixDuration);
                    float mixElapsed = mixDuration * progress;
                    sampleWaterStream.CurrentTime = SampleSettledTime + PhaseDuration(sampleFeedSeconds) +
                        mixElapsed;
                    SetSampleShaftAngle(SampleMixAngle * progress * progress);

                    float tintProgress = Mathf.SmoothStep(0f, 1f, progress);
                    foreach (MeshRenderer renderer in sampleStreamRenderers)
                        TintWater(renderer, tintProgress);

                    float dissolveDuration = Mathf.Min(PhaseDuration(sampleDissolveSeconds), mixDuration);
                    float dissolveProgress = Mathf.InverseLerp(mixDuration - dissolveDuration, mixDuration, mixElapsed);
                    if (dissolveProgress > 0f)
                        SetSamplePartsDissolve(Mathf.SmoothStep(0f, 1f, dissolveProgress));

                    if (progress >= 1f)
                        BeginSampleDrain();
                    break;
                }
                case FactoryProcessPhase.Draining:
                {
                    float progress = AdvanceSamplePhase(sampleDrainSeconds);
                    float remaining = 1f - Mathf.SmoothStep(0f, 1f, progress);
                    CoastSampleShaftToStop();
                    UpdateDrainWater(progress, remaining);
                    waterLevelController.SetWaterLevel(targetWaterLevel * remaining);
                    if (progress >= 1f)
                    {
                        foreach (MeshRenderer renderer in sampleStreamRenderers)
                        {
                            if (renderer != null)
                                renderer.forceRenderingOff = true;
                        }
                        SetState(FactoryProcessPhase.Complete);
                    }
                    break;
                }
            }
        }

        private float AdvanceSamplePhase(float seconds)
        {
            elapsed += Time.deltaTime;
            return Mathf.Clamp01(elapsed / PhaseDuration(seconds));
        }

        private static float PhaseDuration(float seconds) => FactoryProcessProgress.Duration(seconds);

        private void SetSampleShaftAngle(float angle)
        {
            sampleRollBone.localRotation = sampleRollRestRotation * Quaternion.AngleAxis(angle, Vector3.up);
        }

        private void CoastSampleShaftToStop()
        {
            float seconds = Mathf.Min(SampleMixCoastSeconds, PhaseDuration(sampleDrainSeconds));
            float progress = Mathf.Clamp01(elapsed / seconds);
            float finalMixSpeed = 2f * SampleMixAngle / PhaseDuration(sampleMixSeconds);
            float coastAngle = finalMixSpeed * seconds * (progress - 0.5f * progress * progress);
            SetSampleShaftAngle(SampleMixAngle + coastAngle);
        }

        private void ResetSampleSequence()
        {
            // Keep the existing controller alive to update the slider, but show only the baked water.
            sampleStaticWater.enabled = false;
            waterLevelController.SetWaterLevel(0f);

            sampleBatteryParts.enabled = false;
            if (samplePartsFadeMaterial != null)
                sampleBatteryParts.sharedMaterial = samplePartsOriginalMaterial;
            sampleBatteryParts.transform.localScale = Vector3.one;
            sampleBatteryParts.SetBlendShapeWeight(sampleDropShape, 0f);
            sampleBatteryParts.SetBlendShapeWeight(sampleEndShape, 0f);
            sampleRollBone.localRotation = sampleRollRestRotation;

            RestoreSampleWaterTransform();
            sampleWaterStream.CurrentTime = 0f;
            sampleWaterStream.gameObject.SetActive(true);
            sampleWaterStream.UpdateImmediately(0f);
            sampleStreamRenderers = sampleWaterStream.GetComponentsInChildren<MeshRenderer>(true);
            foreach (MeshRenderer renderer in sampleStreamRenderers)
            {
                renderer.forceRenderingOff = false;
                TintWater(renderer, 0f);
            }
        }

        private void PrepareSamplePartsFade()
        {
            samplePartsOriginalMaterial = sampleBatteryParts.sharedMaterial;
            if (samplePartsOriginalMaterial == null || !samplePartsOriginalMaterial.HasProperty(WaterBaseColorId))
                return;

            samplePartsOriginalColor = samplePartsOriginalMaterial.GetColor(WaterBaseColorId);
            samplePartsFadeMaterial = new Material(samplePartsOriginalMaterial) { hideFlags = HideFlags.DontSave };
            samplePartsFadeMaterial.SetFloat("_EnableBlendModePreserveSpecularLighting", 0f);
            // Render the dissolving fragments before the transparent liquid and glass.
            samplePartsFadeMaterial.SetFloat("_TransparentSortPriority", -5f);
            HDMaterial.SetSurfaceType(samplePartsFadeMaterial, true);
            HDMaterial.SetRenderingPass(samplePartsFadeMaterial, HDMaterial.RenderingPass.Default);
        }

        private void SetSamplePartsDissolve(float progress)
        {
            sampleBatteryParts.SetBlendShapeWeight(sampleEndShape, 100f * progress);
            if (samplePartsFadeMaterial == null)
                return;

            Color color = samplePartsOriginalColor;
            color.a *= 1f - progress;
            samplePartsFadeMaterial.SetColor(WaterBaseColorId, color);
            if (sampleBatteryParts.sharedMaterial != samplePartsFadeMaterial)
                sampleBatteryParts.sharedMaterial = samplePartsFadeMaterial;
        }

        private void BeginSampleDrain()
        {
            // Keep the same rendered mesh and lower it about the liquid's bottom, not the stream object's pivot.
            Transform streamTransform = sampleWaterStream.transform;
            float bottom = float.PositiveInfinity;
            foreach (MeshRenderer renderer in sampleStreamRenderers)
            {
                if (renderer != null && renderer.gameObject.activeInHierarchy && renderer.enabled)
                    bottom = Mathf.Min(bottom, renderer.bounds.min.y);
            }

            sampleDrainPivotWorld = streamTransform.position;
            if (!float.IsPositiveInfinity(bottom))
                sampleDrainPivotWorld.y = bottom;
            sampleDrainPivotLocal = streamTransform.InverseTransformPoint(sampleDrainPivotWorld);
            sampleDrainCacheStart = sampleWaterStream.CurrentTime;
            sampleBatteryParts.enabled = false;
            elapsed = 0f;
            SetState(FactoryProcessPhase.Draining);
        }

        private void UpdateDrainWater(float progress, float remaining)
        {
            float duration = PhaseDuration(sampleDrainSeconds);
            float available = Mathf.Max(0f, sampleWaterStream.Duration - sampleDrainCacheStart);
            float rateBudget = 2f * available / duration;
            float firstRate = Mathf.Min(1f, rateBudget);
            float lastRate = Mathf.Clamp(rateBudget - firstRate, 0f, firstRate);
            sampleWaterStream.CurrentTime = sampleDrainCacheStart + duration *
                (firstRate * progress + 0.5f * (lastRate - firstRate) * progress * progress);

            Transform streamTransform = sampleWaterStream.transform;
            RestoreSampleWaterTransform();
            Vector3 scale = sampleWaterRestScale;
            scale.y *= Mathf.Max(0.005f, remaining);
            streamTransform.localScale = scale;
            streamTransform.position += sampleDrainPivotWorld - streamTransform.TransformPoint(sampleDrainPivotLocal);

            float opacity = Mathf.Clamp01(remaining / 0.08f);
            foreach (MeshRenderer renderer in sampleStreamRenderers)
                TintWater(renderer, 1f, opacity);
        }

        private void RestoreSampleWaterTransform()
        {
            Transform streamTransform = sampleWaterStream.transform;
            streamTransform.localPosition = sampleWaterRestPosition;
            streamTransform.localScale = sampleWaterRestScale;
        }

        private void TintWater(Renderer renderer, float progress, float opacity = 1f)
        {
            if (renderer == null)
                return;

            Material material = renderer.sharedMaterial;
            if (material == null || !material.HasProperty(WaterBaseColorId))
                return;

            renderer.GetPropertyBlock(sampleWaterTintBlock);
            Color tint = Color.Lerp(material.GetColor(WaterBaseColorId), sampleDischargeColor, progress);
            tint.a *= opacity;
            sampleWaterTintBlock.SetColor(WaterBaseColorId, tint);
            renderer.SetPropertyBlock(sampleWaterTintBlock);
        }

        /// <summary>Claim local controls before accepting a command; release after its terminal acknowledgement.</summary>
        public void SetApiControl(bool active)
        {
            apiControl = active;
            UpdateButtons();
        }

        /// <summary>Start the sample sequence under API control.</summary>
        public bool TryStartApiProcess(out string reason)
        {
            if (!apiControl)
                reason = "API control has not been acquired.";
            else if (!isActiveAndEnabled || !IsInitialized)
                reason = "The visual process is not initialized and active.";
            else if (IsRunning)
                reason = "A visual process is already running.";
            else if (state != FactoryProcessPhase.Ready && state != FactoryProcessPhase.Complete)
                reason = "The visual process must be reset before accepting a command.";
            else
            {
                try
                {
                    if (IsComplete)
                        ResetProcessCore();
                    StartProcessCore();
                    reason = null;
                    return true;
                }
                catch (Exception exception)
                {
                    reason = "Visual process could not start: " + exception.Message;
                    FailProcess(reason, exception);
                    return false;
                }
            }
            return false;
        }

        private void StartProcess()
        {
            if (apiControl || !IsInitialized || state != FactoryProcessPhase.Ready)
                return;
            try
            {
                StartProcessCore();
            }
            catch (Exception exception)
            {
                FailProcess("Visual process could not start: " + exception.Message, exception);
            }
        }

        private void StartProcessCore()
        {
            ValidatePhaseDurations();
            elapsed = 0f;
            SetState(FactoryProcessPhase.Filling);
            NotifyProcessEvent(ProcessStarted);
        }

        private void ResetProcess()
        {
            if (apiControl || !hasStarted || !isActiveAndEnabled)
                return;
            try
            {
                ResetProcessCore();
                IsInitialized = true;
                UpdateButtons();
            }
            catch (Exception exception)
            {
                FailProcess("Visual process reset failed: " + exception.Message, exception);
            }
        }

        private void ResetProcessCore()
        {
            ValidatePhaseDurations();
            elapsed = 0f;
            overallProgress = 0f;
            completionReported = false;
            failureReported = false;
            failureMessage = null;
            ResetSampleSequence();
            SetState(FactoryProcessPhase.Ready);
        }

        private void SetState(FactoryProcessPhase next)
        {
            FactoryProcessPhase previous = state;
            state = next;
            UpdateOverallProgress();
            UpdateButtons();
            statusText.text = PhaseMessage;

            // Completion is emitted only by the real visual phase transition after draining.
            if (next == FactoryProcessPhase.Complete && previous != next && !completionReported)
            {
                completionReported = true;
                NotifyProcessEvent(ProcessCompleted);
            }
        }

        private void UpdateButtons()
        {
            if (startButton != null)
                startButton.interactable = isActiveAndEnabled && IsInitialized && !apiControl && state == FactoryProcessPhase.Ready;
            if (resetButton != null)
                resetButton.interactable = isActiveAndEnabled && hasStarted && !apiControl && state != FactoryProcessPhase.Ready;
        }

        private void ValidatePhaseDurations()
        {
            PhaseDuration(sampleFillSeconds);
            PhaseDuration(sampleFeedSeconds);
            PhaseDuration(sampleMixSeconds);
            PhaseDuration(sampleDissolveSeconds);
            PhaseDuration(sampleDrainSeconds);
        }

        private void UpdateOverallProgress()
        {
            if (state == FactoryProcessPhase.Ready)
            {
                overallProgress = 0f;
                return;
            }
            if (state == FactoryProcessPhase.Failed)
                return;

            float next = FactoryProcessProgress.SamplePercent(state, elapsed, sampleFillSeconds,
                sampleFeedSeconds, sampleMixSeconds, sampleDrainSeconds);
            overallProgress = Mathf.Max(overallProgress, Mathf.Clamp(next, 0f, 100f));
        }

        private void FailProcess(string reason, Exception exception = null)
        {
            if (failureReported)
                return;
            failureReported = true;
            IsInitialized = false;
            state = FactoryProcessPhase.Failed;
            failureMessage = reason;
            UpdateButtons();
            if (statusText != null)
                statusText.text = reason;
            if (exception != null)
                Debug.LogException(exception, this);
            else
                Debug.LogError(reason, this);

            Action<string> handlers = ProcessFailed;
            if (handlers == null)
                return;
            foreach (Action<string> handler in handlers.GetInvocationList())
            {
                try { handler(reason); }
                catch (Exception subscriberException) { Debug.LogException(subscriberException, this); }
            }
        }

        private void NotifyProcessEvent(Action handlers)
        {
            if (handlers == null)
                return;
            foreach (Action handler in handlers.GetInvocationList())
            {
                try { handler(); }
                catch (Exception subscriberException) { Debug.LogException(subscriberException, this); }
            }
        }

        private static string GetExhibitionStatus(FactoryProcessPhase current)
        {
            switch (current)
            {
                case FactoryProcessPhase.Ready:
                    return "대기 | 공정 시작을 눌러주세요";
                case FactoryProcessPhase.Filling:
                    return "1/5 | 액체 주입 중";
                case FactoryProcessPhase.Settling:
                    return "2/5 | 수면 안정화 중";
                case FactoryProcessPhase.Feeding:
                    return "3/5 | 원료 투입 중";
                case FactoryProcessPhase.Mixing:
                    return "4/5 | 교반 중";
                case FactoryProcessPhase.Draining:
                    return "5/5 | 배출 중";
                case FactoryProcessPhase.Complete:
                    return "공정 시연 완료";
                default:
                    return current.ToString();
            }
        }
    }

    internal enum FactoryProcessPhase { Ready, Filling, Settling, Feeding, Mixing, Draining, Complete, Failed }

    // Uses the same phase durations and settling speed ramp as the visual state machine.
    // No separate wall clock or water-level percentage is used for command progress.
    internal static class FactoryProcessProgress
    {
        internal static float Duration(float seconds)
        {
            if (float.IsNaN(seconds) || float.IsInfinity(seconds))
                throw new ArgumentOutOfRangeException(nameof(seconds), "Phase duration must be finite.");
            return Math.Max(0.1f, seconds);
        }

        internal static float SettlingSeconds(float fillSeconds)
        {
            float fillRate = 12f / Duration(fillSeconds);
            return 2f * (16f - 12f) / (fillRate + 1f);
        }

        internal static float SamplePercent(FactoryProcessPhase phase, float elapsed,
            float fillSeconds, float feedSeconds, float mixSeconds, float drainSeconds)
        {
            if (phase == FactoryProcessPhase.Ready)
                return 0f;
            if (phase == FactoryProcessPhase.Complete)
                return 100f;

            float fill = Duration(fillSeconds);
            float settling = Duration(SettlingSeconds(fillSeconds));
            float feed = Duration(feedSeconds);
            float mix = Duration(mixSeconds);
            float drain = Duration(drainSeconds);
            float before;
            float current;
            switch (phase)
            {
                case FactoryProcessPhase.Filling: before = 0f; current = fill; break;
                case FactoryProcessPhase.Settling: before = fill; current = settling; break;
                case FactoryProcessPhase.Feeding: before = fill + settling; current = feed; break;
                case FactoryProcessPhase.Mixing: before = fill + settling + feed; current = mix; break;
                case FactoryProcessPhase.Draining: before = fill + settling + feed + mix; current = drain; break;
                default: throw new ArgumentOutOfRangeException(nameof(phase), "Expected a sample process phase.");
            }
            if (float.IsNaN(elapsed) || float.IsInfinity(elapsed))
                throw new ArgumentOutOfRangeException(nameof(elapsed), "Phase elapsed time must be finite.");
            float passed = before + Math.Max(0f, Math.Min(current, elapsed));
            return 100f * passed / (fill + settling + feed + mix + drain);
        }
    }
}
