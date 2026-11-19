using System;
using System.IO;
using TMPro;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Youngpoong.Integration
{
    internal static class FactoryMaterialPanelSetup
    {
        private const string ScenePath = "Assets/Scenes/FactoryDemoExhibitionApi.unity";

        [MenuItem("Youngpoong/Integration/Update Material Conditions Panel")]
        private static void Apply()
        {
            try
            {
                Require(!EditorApplication.isPlayingOrWillChangePlaymode && !EditorApplication.isCompiling,
                    "Stop Play and wait for compilation before updating the material panel.");
                for (int i = 0; i < SceneManager.sceneCount; i++)
                    Require(!SceneManager.GetSceneAt(i).isDirty, "Save open scene changes before updating the material panel.");
                Scene scene = SceneManager.GetActiveScene();
                if (scene.path != ScenePath) scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
                Transform panel = FindInScene<Canvas>(scene).transform.Find("ConditionsPanel");
                Require(panel != null, "ConditionsPanel is missing from the API canvas.");
                var conditions = panel.Find("ConditionsText").GetComponent<TextMeshProUGUI>();
                Transform materialTransform = panel.Find("MaterialConditionsText");
                var material = materialTransform != null ? materialTransform.GetComponent<TextMeshProUGUI>() :
                    UnityEngine.Object.Instantiate(conditions.gameObject, panel, false).GetComponent<TextMeshProUGUI>();
                material.name = "MaterialConditionsText";
                Configure(conditions, new Vector2(0, -24), new Vector2(312, 210), 26);
                Configure(material, new Vector2(0, -246), new Vector2(312, 390), 22);
                conditions.text = FactoryPanelText.Conditions(null);
                material.text = FactoryPanelText.Material(null);
                var bridge = new SerializedObject(FindInScene<FactoryApiSimulationBridge>(scene));
                bridge.FindProperty("conditionsText").objectReferenceValue = conditions;
                bridge.FindProperty("materialConditionsText").objectReferenceValue = material;
                bridge.ApplyModifiedPropertiesWithoutUndo();
                EditorUtility.SetDirty(conditions);
                EditorUtility.SetDirty(material);
                EditorSceneManager.MarkSceneDirty(scene);
                Require(EditorSceneManager.SaveScene(scene), "Could not save the API scene.");
                Verify(conditions, material);
                Debug.Log("[Factory material panel] PASS API scene updated, references wired, text bounds verified; no real B request.");
            }
            catch (Exception exception) { Debug.LogException(exception); }
        }

        private static void Configure(TextMeshProUGUI text, Vector2 position, Vector2 size, int fontSize)
        {
            Require(text != null && text.font != null, "Existing Korean TMP font is required.");
            RectTransform rect = text.rectTransform;
            rect.anchorMin = rect.anchorMax = rect.pivot = new Vector2(0.5f, 1);
            rect.anchoredPosition = position;
            rect.sizeDelta = size;
            text.fontSize = fontSize;
            text.enableAutoSizing = false;
            text.alignment = TextAlignmentOptions.TopLeft;
            text.textWrappingMode = TextWrappingModes.Normal;
            text.raycastTarget = false;
        }

        private static void Verify(TextMeshProUGUI conditions, TextMeshProUGUI material)
        {
            Canvas.ForceUpdateCanvases();
            var sample = new FactoryCommandDto {
                command_id = "local-material-layout-only", command = "apply_and_start",
                material = new MaterialDto { name = "로컬 표시 검증", feed_amount_kg = 750,
                    ni_content_pct = 12.17, li_content_pct = 0, fe_content_pct = null },
                process_conditions = new ProcessConditionsDto { sulfuric_acid_l = 1050, leaching_temperature_c = 66, leaching_time_hr = 5.5 },
                expected_recovery = new RecoveryDto { ni_recovery_pct = 85.65, co_recovery_pct = 78.45 }
            };
            sample.Validate();
            float waiting = PreferredHeight(material, FactoryPanelText.Material(null));
            float mixed = PreferredHeight(material, FactoryPanelText.Material(sample));
            sample.material.name = new string('가', 60);
            float longName = PreferredHeight(material, FactoryPanelText.Material(sample));
            float process = PreferredHeight(conditions, FactoryPanelText.Conditions(sample));
            string directory = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "Library", "FactoryIntegration"));
            Directory.CreateDirectory(directory);
            File.WriteAllText(Path.Combine(directory, "material-layout-check.json"),
                JsonUtility.ToJson(new LayoutRecord { scene = ScenePath, checkedAtUtc = DateTime.UtcNow.ToString("o"),
                    waitingHeight = waiting, sampleHeight = mixed, longNameHeight = longName, processHeight = process,
                    materialBoxHeight = material.rectTransform.rect.height, processBoxHeight = conditions.rectTransform.rect.height,
                    materialReferenceWired = true, liveServerTest = false }, true));
        }

        private static float PreferredHeight(TextMeshProUGUI text, string value)
        {
            Vector2 preferred = text.GetPreferredValues(value, text.rectTransform.rect.width, Mathf.Infinity);
            Require(preferred.y <= text.rectTransform.rect.height + 0.1f, "Text exceeds panel height: " + text.name + " " + preferred.y);
            return preferred.y;
        }

        private static T FindInScene<T>(Scene scene) where T : Component
        {
            T found = null;
            foreach (GameObject root in scene.GetRootGameObjects())
                foreach (T candidate in root.GetComponentsInChildren<T>(true))
                {
                    Require(found == null, "Expected exactly one " + typeof(T).Name + " in the API scene.");
                    found = candidate;
                }
            Require(found != null, "Missing " + typeof(T).Name + " in the API scene.");
            return found;
        }

        private static void Require(bool condition, string message)
        {
            if (!condition) throw new InvalidOperationException(message);
        }

        [Serializable]
        private sealed class LayoutRecord
        {
            public string scene, checkedAtUtc;
            public float waitingHeight, sampleHeight, longNameHeight, processHeight, materialBoxHeight, processBoxHeight;
            public bool materialReferenceWired, liveServerTest;
        }
    }
}
