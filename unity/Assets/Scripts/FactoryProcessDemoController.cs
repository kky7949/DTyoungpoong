using TMPro;
using UnityEngine;
using UnityEngine.Formats.Alembic.Importer;
using UnityEngine.Rendering.HighDefinition;
using UnityEngine.Serialization;
using UnityEngine.UI;

[DisallowMultipleComponent]
public sealed class FactoryProcessDemoController : MonoBehaviour
{
    private enum ProcessState { Ready, Filling, Settling, Feeding, Mixing, Draining, Processing, Complete }

    private const float SampleFillEndTime = 12f;
    private const float SampleSettledTime = 16f;
    private const float SampleMixAngle = 720f;
    private const float SampleMixCoastSeconds = 1f;
    private static readonly int WaterBaseColorId = Shader.PropertyToID("_BaseColor");

    [SerializeField] private WaterLevelController waterLevelController = null;
    [SerializeField] private Button startButton = null;
    [SerializeField] private Button resetButton = null;
    [SerializeField] private TMP_Text statusText = null;
    [SerializeField] private bool useExhibitionLabels = false;

    [Header("Battery Feed")]
    [SerializeField] private Transform batteryObject = null;
    [SerializeField] private Transform batteryEntryPoint = null;
    [SerializeField] private Transform batteryDropPoint = null;
    [SerializeField, Min(0.1f)] private float approachSeconds = 1.5f;
    [SerializeField, Min(0.1f)] private float dropSeconds = 0.5f;

    [Header("Water Level")]
    [SerializeField, Range(0f, 100f)] private float initialWaterLevel = 30f;
    [SerializeField, Range(0f, 100f)] private float targetWaterLevel = 70f;
    [SerializeField, Min(0.1f)] private float durationSeconds = 3f;

    [Header("Sample Video Sequence")]
    [SerializeField] private bool useSampleSequence = false;
    [SerializeField] private AlembicStreamPlayer sampleWaterStream = null;
    [SerializeField] private SkinnedMeshRenderer sampleBatteryParts = null;
    [SerializeField, Min(0.1f)] private float sampleFillSeconds = 4f;
    [SerializeField, Min(0.1f)] private float sampleFeedSeconds = 2.5f;
    [SerializeField, Min(0.1f)] private float sampleMixSeconds = 6f;
    [FormerlySerializedAs("sampleColorSeconds")]
    [SerializeField, Min(0.1f)] private float sampleDissolveSeconds = 2f;
    [SerializeField, Min(0.1f)] private float sampleDrainSeconds = 5.5f;
    [SerializeField] private Color sampleDischargeColor = new Color32(96, 32, 24, 174);

    private ProcessState state;
    private float elapsed;
    private Vector3 batteryStartLocalPosition;
    private Vector3 batteryFeedOrigin;
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
        if (waterLevelController == null || startButton == null || resetButton == null ||
            startButton == resetButton || statusText == null)
        {
            Debug.LogError("Factory process demo requires a water controller, two distinct buttons, and a TMP status text.", this);
            enabled = false;
            return;
        }

        bool anyFeedReference = batteryObject != null || batteryEntryPoint != null || batteryDropPoint != null;
        if (!useSampleSequence && anyFeedReference && (batteryObject == null || batteryEntryPoint == null || batteryDropPoint == null ||
            batteryEntryPoint.IsChildOf(batteryObject) || batteryDropPoint.IsChildOf(batteryObject) ||
            transform.IsChildOf(batteryObject)))
        {
            Debug.LogError("Assign the battery and both feed points. Keep the feed points and ProcessDemo outside the battery hierarchy.", this);
            enabled = false;
            return;
        }

        if (useSampleSequence && !ResolveSampleRig())
        {
            Debug.LogError("Sample video mode needs the original water Alembic Stream Player and Battery_All_01 renderer with Drop, End, and Roll_Bone.", this);
            enabled = false;
            return;
        }

        startButton.onClick.AddListener(StartProcess);
        resetButton.onClick.AddListener(ResetProcess);
    }

    // Start runs after the water controller has set its own initial level in OnEnable.
    private void Start()
    {
        if (batteryObject != null)
            batteryStartLocalPosition = batteryObject.localPosition;

        if (useSampleSequence)
        {
            sampleRollRestRotation = sampleRollBone.localRotation;
            sampleWaterTintBlock = new MaterialPropertyBlock();
            sampleWaterRestPosition = sampleWaterStream.transform.localPosition;
            sampleWaterRestScale = sampleWaterStream.transform.localScale;
            PrepareSamplePartsFade();
        }

        ResetProcess();
    }

    private void OnDisable()
    {
        if (startButton != null)
            startButton.onClick.RemoveListener(StartProcess);
        if (resetButton != null)
            resetButton.onClick.RemoveListener(ResetProcess);
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
        if (useSampleSequence)
        {
            UpdateSampleSequence();
            return;
        }

        if (state == ProcessState.Feeding)
        {
            UpdateBatteryFeed();
            return;
        }

        if (state != ProcessState.Processing)
            return;

        elapsed += Time.deltaTime;
        float progress = Mathf.Clamp01(elapsed / Mathf.Max(0.1f, durationSeconds));
        waterLevelController.SetWaterLevel(Mathf.SmoothStep(initialWaterLevel, targetWaterLevel, progress));

        if (progress >= 1f)
            SetState(ProcessState.Complete);
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
            case ProcessState.Filling:
            {
                float progress = AdvanceSamplePhase(sampleFillSeconds);
                sampleWaterStream.CurrentTime = SampleFillEndTime * progress;
                waterLevelController.SetWaterLevel(targetWaterLevel * Mathf.InverseLerp(0.15f, 1f, progress));
                if (progress >= 1f)
                {
                    elapsed = 0f;
                    SetState(ProcessState.Settling);
                }
                break;
            }
            case ProcessState.Settling:
            {
                // Integrate a linear speed ramp from the fill speed to 1x, covering cache seconds 12–16.
                float fillRate = SampleFillEndTime / PhaseDuration(sampleFillSeconds);
                float seconds = 2f * (SampleSettledTime - SampleFillEndTime) / (fillRate + 1f);
                float progress = AdvanceSamplePhase(seconds);
                float cacheElapsed = seconds * (fillRate * progress + 0.5f * (1f - fillRate) * progress * progress);
                sampleWaterStream.CurrentTime = progress >= 1f ? SampleSettledTime : SampleFillEndTime + cacheElapsed;
                if (progress >= 1f)
                {
                    sampleBatteryParts.enabled = true;
                    elapsed = 0f;
                    SetState(ProcessState.Feeding);
                }
                break;
            }
            case ProcessState.Feeding:
            {
                float progress = AdvanceSamplePhase(sampleFeedSeconds);
                sampleWaterStream.CurrentTime = SampleSettledTime + PhaseDuration(sampleFeedSeconds) * progress;
                sampleBatteryParts.SetBlendShapeWeight(sampleDropShape, Mathf.SmoothStep(0f, 100f, progress));
                if (progress >= 1f)
                {
                    sampleStreamRenderers = sampleWaterStream.GetComponentsInChildren<MeshRenderer>(true);
                    elapsed = 0f;
                    SetState(ProcessState.Mixing);
                }
                break;
            }
            case ProcessState.Mixing:
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
            case ProcessState.Draining:
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
                    SetState(ProcessState.Complete);
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

    private static float PhaseDuration(float seconds) => Mathf.Max(0.1f, seconds);

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
        SetState(ProcessState.Draining);
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

    private void UpdateBatteryFeed()
    {
        elapsed += Time.deltaTime;
        float approachDuration = Mathf.Max(0.1f, approachSeconds);
        if (elapsed < approachDuration)
        {
            float approachProgress = Mathf.SmoothStep(0f, 1f, elapsed / approachDuration);
            batteryObject.position = Vector3.Lerp(batteryFeedOrigin, batteryEntryPoint.position, approachProgress);
            return;
        }

        float dropProgress = Mathf.Clamp01((elapsed - approachDuration) / Mathf.Max(0.1f, dropSeconds));
        batteryObject.position = Vector3.Lerp(batteryEntryPoint.position, batteryDropPoint.position, dropProgress * dropProgress);
        if (dropProgress < 1f)
            return;

        batteryObject.gameObject.SetActive(false);
        elapsed = 0f;
        SetState(ProcessState.Processing);
    }

    private void StartProcess()
    {
        if (state != ProcessState.Ready)
            return;

        elapsed = 0f;
        if (useSampleSequence)
        {
            SetState(ProcessState.Filling);
        }
        else if (batteryObject != null)
        {
            batteryFeedOrigin = batteryObject.position;
            SetState(ProcessState.Feeding);
        }
        else
        {
            SetState(ProcessState.Processing);
        }
    }

    private void ResetProcess()
    {
        elapsed = 0f;
        if (useSampleSequence)
        {
            ResetSampleSequence();
            SetState(ProcessState.Ready);
            return;
        }

        if (batteryObject != null)
        {
            batteryObject.localPosition = batteryStartLocalPosition;
            batteryObject.gameObject.SetActive(true);
        }

        waterLevelController.SetWaterLevel(initialWaterLevel);
        SetState(ProcessState.Ready);
    }

    private void SetState(ProcessState next)
{
    state = next;
    startButton.interactable = next == ProcessState.Ready;
    resetButton.interactable = next != ProcessState.Ready;

    statusText.text = useExhibitionLabels
        ? GetExhibitionStatus(next)
        : next.ToString();
}

private static string GetExhibitionStatus(ProcessState current)
    {
    switch (current)
        {
        case ProcessState.Ready:
            return "대기 | 공정 시작을 눌러주세요";
        case ProcessState.Filling:
            return "1/5 | 액체 주입 중";
        case ProcessState.Settling:
            return "2/5 | 수면 안정화 중";
        case ProcessState.Feeding:
            return "3/5 | 원료 투입 중";
        case ProcessState.Mixing:
            return "4/5 | 교반 중";
        case ProcessState.Draining:
            return "5/5 | 배출 중";
        case ProcessState.Processing:
            return "공정 진행 중";
        case ProcessState.Complete:
            return "공정 시연 완료";
        default:
            return current.ToString();
        }
    }
}
