using System;
using System.IO;
using System.Text;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Youngpoong.Integration
{
    internal static class FactoryMacDevelopmentBuild
    {
        private const string ScenePath = "Assets/Scenes/FactoryDemoExhibitionApi.unity";
        private const string NaturalScenePath = "Assets/Scenes/FactoryDemoExhibitionApiNatural.unity";
        private static bool queued;
        private static double stopDeadline;

        private static string OutputDirectory => Path.GetFullPath(
            Path.Combine(Application.dataPath, "..", "..", "Builds", "macOS"));

        // Explicit local build request, useful when the Editor is already open and owns the project lock.
        // No request file means no automatic setting changes or build on script import.
        [InitializeOnLoadMethod]
        private static void AcceptLocalBuildRequest()
        {
            string request = Path.Combine(OutputDirectory, "build-request.txt");
            if (!File.Exists(request) || File.ReadAllText(request).Trim() != "macOS Development") return;
            File.Move(request, Path.Combine(OutputDirectory,
                "build-request-accepted-" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmssfff") + ".txt"));
            queued = true;
            stopDeadline = EditorApplication.timeSinceStartup + 30;
            EditorApplication.update += WaitForStoppedEditor;
        }

        private static void WaitForStoppedEditor()
        {
            if (EditorApplication.isCompiling) return;
            if (EditorApplication.timeSinceStartup > stopDeadline)
            {
                EditorApplication.update -= WaitForStoppedEditor;
                queued = false;
                Debug.LogError("[Factory macOS build] Timed out waiting for Editor Play to stop.");
                return;
            }
            if (EditorApplication.isPlayingOrWillChangePlaymode)
            {
                EditorApplication.isPlaying = false;
                return;
            }
            EditorApplication.update -= WaitForStoppedEditor;
            Build();
        }

        [MenuItem("Youngpoong/Integration/Build macOS Development App")]
        private static void QueueBuild()
        {
            if (queued || EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling)
            {
                Debug.LogError("[Factory macOS build] Stop Play and wait for compilation before building.");
                return;
            }
            queued = true;
            EditorApplication.delayCall += Build;
        }

        private static void Build()
        {
            Build(ScenePath, OutputDirectory, "YoungpoongFactoryDemo.app");
        }

        public static void BuildNaturalBatch()
        {
            string output = Path.Combine(OutputDirectory, "Natural");
            if (!Build(NaturalScenePath, output, "YoungpoongFactoryNatural.app"))
                throw new InvalidOperationException("Natural macOS build failed. Read " + Path.Combine(output, "build-report.json"));
        }

        private static bool Build(string scenePath, string output, string appName)
        {
            var record = new BuildRecord { unityVersion = Application.unityVersion, scene = scenePath,
                appPath = Path.Combine(output, appName), startedAtUtc = DateTime.UtcNow.ToString("o") };
            try
            {
                if (EditorApplication.isPlayingOrWillChangePlaymode)
                    throw new InvalidOperationException("Editor Play must remain stopped during the standalone handoff.");
                for (int i = 0; i < SceneManager.sceneCount; i++)
                    if (SceneManager.GetSceneAt(i).isDirty)
                        throw new InvalidOperationException("Save the open scene changes before building.");
                if (!File.Exists(scenePath)) throw new FileNotFoundException("API scene is missing.", scenePath);
                if (!BuildPipeline.IsBuildTargetSupported(BuildTargetGroup.Standalone, BuildTarget.StandaloneOSX))
                    throw new InvalidOperationException("macOS Build Support is not installed.");
                if (EditorUserBuildSettings.activeBuildTarget != BuildTarget.StandaloneOSX)
                    throw new InvalidOperationException("Switch the active platform to macOS before using this build menu.");

                if (scenePath == ScenePath)
                    UseLegacySceneInBuildSettings();
                PlayerSettings.runInBackground = true;
                PlayerSettings.insecureHttpOption = InsecureHttpOption.DevelopmentOnly;
                PlayerSettings.SetScriptingBackend(NamedBuildTarget.Standalone, ScriptingImplementation.Mono2x);
                PlayerSettings.SetManagedStrippingLevel(NamedBuildTarget.Standalone, ManagedStrippingLevel.Disabled);
                PlayerSettings.SetArchitecture(NamedBuildTarget.Standalone, 2); // Intel + Apple Silicon universal.
                EditorUserBuildSettings.development = true;
                AssetDatabase.SaveAssets();

                Directory.CreateDirectory(output);
                record.development = true;
                record.runInBackground = PlayerSettings.runInBackground;
                record.httpMode = PlayerSettings.insecureHttpOption.ToString();
                record.architecture = PlayerSettings.GetArchitecture(NamedBuildTarget.Standalone);
                record.scriptingBackend = PlayerSettings.GetScriptingBackend(NamedBuildTarget.Standalone).ToString();
                record.managedStripping = PlayerSettings.GetManagedStrippingLevel(NamedBuildTarget.Standalone).ToString();
                Debug.Log("[Factory macOS build] START " + record.appPath);
                BuildReport report = BuildPipeline.BuildPlayer(new BuildPlayerOptions {
                    scenes = new[] { scenePath }, locationPathName = record.appPath,
                    target = BuildTarget.StandaloneOSX, targetGroup = BuildTargetGroup.Standalone,
                    options = BuildOptions.Development
                });
                record.result = record.unityBuildResult = report.summary.result.ToString();
                record.totalSizeBytes = report.summary.totalSize.ToString();
                record.elapsedSeconds = report.summary.totalTime.TotalSeconds;
                record.errorCount = (int)report.summary.totalErrors;
                record.warningCount = (int)report.summary.totalWarnings;
                var details = new StringBuilder();
                foreach (var step in report.steps)
                    foreach (var message in step.messages)
                        if (message.type == LogType.Error || message.type == LogType.Exception || message.type == LogType.Warning)
                            details.AppendLine(step.name + " / " + message.type + ": " + message.content);
                File.WriteAllText(Path.Combine(output, "build-messages.log"), details.ToString());
                if (report.summary.result == BuildResult.Succeeded)
                {
                    // Alembic adds StreamingAssets after Unity's native signing step. Seal the final bundle.
                    // Sign generated plugin bundles locally without retaining vendor certificate requirements.
                    string pluginsDirectory = Path.Combine(record.appPath, "Contents", "PlugIns");
                    string alembicPlugin = Path.Combine(pluginsDirectory, "abci.bundle");
                    if (!Directory.Exists(alembicPlugin))
                        throw new DirectoryNotFoundException("Bundled Alembic plugin is missing: " + alembicPlugin);
                    string signing = "";
                    foreach (string plugin in Directory.GetDirectories(pluginsDirectory, "*.bundle"))
                        signing += RunCodesign("--force --sign - --preserve-metadata=entitlements,flags --timestamp=none ", plugin);
                    signing += RunCodesign("--force --sign - --preserve-metadata=entitlements,requirements,flags --timestamp=none ", record.appPath);
                    signing += RunCodesign("--verify --deep --strict --verbose=2 ", record.appPath);
                    signing += RunCodesign("--verify --deep --strict --all-architectures ", record.appPath);
                    File.WriteAllText(Path.Combine(output, "build-signing.log"), signing);
                    record.signatureVerified = true;
                }
                Debug.Log("[Factory macOS build] RESULT " + record.result + " / errors=" + record.errorCount +
                    " / warnings=" + record.warningCount + " / seconds=" + record.elapsedSeconds);
                if (report.summary.result != BuildResult.Succeeded)
                    Debug.LogError("[Factory macOS build] Build failed. Read build-report.json and build-messages.log.");
            }
            catch (Exception exception)
            {
                record.result = "Failed";
                record.failure = exception.ToString();
                Debug.LogException(exception);
            }
            finally
            {
                Directory.CreateDirectory(output);
                record.finishedAtUtc = DateTime.UtcNow.ToString("o");
                File.WriteAllText(Path.Combine(output, "build-report.json"), JsonUtility.ToJson(record, true));
                queued = false;
            }
            return record.result == BuildResult.Succeeded.ToString() && record.signatureVerified;
        }

        private static void UseLegacySceneInBuildSettings()
        {
            var scenes = EditorBuildSettings.scenes;
            bool found = false;
            for (int i = 0; i < scenes.Length; i++)
            {
                bool isApi = scenes[i].path == ScenePath;
                scenes[i] = new EditorBuildSettingsScene(scenes[i].path, isApi);
                found |= isApi;
            }
            if (!found)
            {
                Array.Resize(ref scenes, scenes.Length + 1);
                scenes[scenes.Length - 1] = new EditorBuildSettingsScene(ScenePath, true);
            }
            EditorBuildSettings.scenes = scenes;
        }

        private static string RunCodesign(string arguments, string appPath)
        {
            var info = new System.Diagnostics.ProcessStartInfo("/usr/bin/codesign",
                arguments + "\"" + appPath.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\"") {
                UseShellExecute = false, RedirectStandardOutput = true, RedirectStandardError = true
            };
            using (var process = System.Diagnostics.Process.Start(info))
            {
                string output = process.StandardOutput.ReadToEnd() + process.StandardError.ReadToEnd();
                process.WaitForExit();
                if (process.ExitCode != 0) throw new InvalidOperationException("macOS local signing failed: " + output);
                return output;
            }
        }

        [Serializable]
        private sealed class BuildRecord
        {
            public string unityVersion, scene, appPath, startedAtUtc, finishedAtUtc, result, unityBuildResult, failure;
            public bool development, runInBackground, signatureVerified;
            public string httpMode, scriptingBackend, managedStripping, totalSizeBytes;
            public int architecture, errorCount, warningCount;
            public double elapsedSeconds;
        }
    }
}
