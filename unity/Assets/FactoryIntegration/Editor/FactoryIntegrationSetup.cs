using UnityEditor;
using UnityEngine;

namespace Youngpoong.Integration
{
    internal static class FactoryIntegrationSetup
    {
        // Explicit menu action; never changes network policy automatically on import or Play.
        [MenuItem("Youngpoong/Integration/Use Development Only HTTP")]
        private static void UseDevelopmentOnlyHttp()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
            {
                Debug.LogError("[Factory setup] Stop Play before changing the development HTTP setting.");
                return;
            }
            PlayerSettings.insecureHttpOption = InsecureHttpOption.DevelopmentOnly;
            AssetDatabase.SaveAssets();
            Debug.Log("[Factory setup] HTTP mode: " + PlayerSettings.insecureHttpOption);
        }
    }
}
