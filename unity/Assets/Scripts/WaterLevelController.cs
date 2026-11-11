using UnityEngine;
using UnityEngine.UI;

[DisallowMultipleComponent]
[RequireComponent(typeof(SkinnedMeshRenderer))]
public sealed class WaterLevelController : MonoBehaviour
{
    [SerializeField] private Slider waterLevelSlider = null;
    [SerializeField, Range(0f, 100f)] private float waterLevelPercent = 50f;

    private SkinnedMeshRenderer waterRenderer;
    private int endShapeIndex = -1;

    private void Awake()
    {
        waterRenderer = GetComponent<SkinnedMeshRenderer>();
        Mesh mesh = waterRenderer.sharedMesh;
        if (mesh != null)
            endShapeIndex = mesh.GetBlendShapeIndex("End");

        if (endShapeIndex < 0)
        {
            Debug.LogError(
                "WaterLevelController: attach this component to the Water_2 renderer " +
                "whose mesh contains the End blend shape.", this);
            enabled = false;
        }
    }

    private void OnEnable()
    {
        if (waterLevelSlider != null)
        {
            waterLevelSlider.minValue = 0f;
            waterLevelSlider.maxValue = 100f;
            waterLevelSlider.wholeNumbers = false;
            waterLevelSlider.onValueChanged.AddListener(SetWaterLevel);
        }

        SetWaterLevel(waterLevelPercent);
    }

    private void OnDisable()
    {
        if (waterLevelSlider != null)
            waterLevelSlider.onValueChanged.RemoveListener(SetWaterLevel);
    }

    public void SetWaterLevel(float percent)
    {
        if (float.IsNaN(percent) || float.IsInfinity(percent))
            return;

        waterLevelPercent = Mathf.Clamp(percent, 0f, 100f);

        if (waterRenderer != null && endShapeIndex >= 0)
            waterRenderer.SetBlendShapeWeight(endShapeIndex, 100f - waterLevelPercent);

        if (waterLevelSlider != null)
            waterLevelSlider.SetValueWithoutNotify(waterLevelPercent);
    }
}
