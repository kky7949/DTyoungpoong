using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Youngpoong.Integration
{
    [DisallowMultipleComponent]
    public sealed class FactoryApiSimulationBridge : MonoBehaviour
    {
        [SerializeField] private FastApiFactoryClient client;
        [SerializeField] private IntegratedFactoryProcessController process;
        [SerializeField] private TMP_Text conditionsText;
        [SerializeField] private TMP_Text materialConditionsText;
        [SerializeField] private TMP_Text resultsText;

        public FactoryCommandDto AppliedCommand { get; private set; }
        private string activeId;
        private bool terminalReported;
        private bool showCompletion;
        private FactoryCommandDto completedCommand;
        private RectTransform resultPanel;
        private Image resultBackground;
        private Vector2 resultPanelSize;
        private Vector2 resultPanelPosition;
        private Color resultBackgroundColor;

        private void OnEnable()
        {
            if (client == null || process == null || conditionsText == null || materialConditionsText == null || resultsText == null)
            {
                Debug.LogError("[공정 연동] 통신·공정·공정조건/원료조건/결과 패널을 모두 연결하세요.", this);
                if (client != null) client.enabled = false;
                enabled = false;
                return;
            }
            client.CommandReceived += HandleCommand;
            process.ProcessStarted += OnProcessStarted;
            process.ProcessCompleted += OnProcessCompleted;
            process.ProcessFailed += OnProcessFailed;
            resultPanel = resultsText.rectTransform.parent as RectTransform;
            if (resultPanel != null)
            {
                resultPanelSize = resultPanel.sizeDelta;
                resultPanelPosition = resultPanel.anchoredPosition;
                resultBackground = resultPanel.GetComponent<Image>();
                if (resultBackground != null) resultBackgroundColor = resultBackground.color;
                UpdateResultLayout();
            }
            DisplayCommand(AppliedCommand);
        }

        private void OnDisable()
        {
            if (client != null)
            {
                if (activeId != null && !terminalReported)
                    client.ReportError(activeId, "공정 연결 컴포넌트 중단 · 자동 재실행하지 않습니다.");
                client.CommandReceived -= HandleCommand;
            }
            if (process != null)
            {
                process.ProcessStarted -= OnProcessStarted;
                process.ProcessCompleted -= OnProcessCompleted;
                process.ProcessFailed -= OnProcessFailed;
            }
            if (resultPanel != null)
            {
                resultPanel.sizeDelta = resultPanelSize;
                resultPanel.anchoredPosition = resultPanelPosition;
                if (resultBackground != null) resultBackground.color = resultBackgroundColor;
            }
            // On Play/scene shutdown a final network delivery cannot be guaranteed.
        }

        private void HandleCommand(FactoryCommandDto command)
        {
            activeId = command.command_id;
            terminalReported = false;
            process.SetApiControl(true);
            string reason;
            if (!process.TryStartApiProcess(out reason))
            {
                terminalReported = true;
                client.ReportError(activeId, "공정 시작 불가: " + reason);
                return;
            }
            DisplayCommand(command);
            client.ReportProgress(activeId, process.OverallProgress, process.PhaseMessage);
        }

        private void DisplayCommand(FactoryCommandDto command)
        {
            AppliedCommand = command;
            conditionsText.text = FactoryPanelText.Conditions(command);
            materialConditionsText.text = FactoryPanelText.Material(command);
        }

        private void OnProcessStarted()
        {
            if (showCompletion)
            {
                showCompletion = false;
                completedCommand = null;
                UpdateResultLayout();
            }
            if (AppliedCommand != null && (activeId == null || terminalReported))
                DisplayCommand(null);
        }

        private void LateUpdate()
        {
            if (activeId != null)
            {
                if (!terminalReported && process.IsRunning)
                    client.ReportProgress(activeId, process.OverallProgress, process.PhaseMessage);

                // Keep local controls locked until the terminal POST is acknowledged.
                if (!client.HasActiveCommand && !client.IsHalted)
                {
                    activeId = null;
                    process.SetApiControl(false);
                }
            }
            string text = showCompletion
                ? FactoryPanelText.CompletedResults(completedCommand, client.ConnectionMessage)
                : FactoryPanelText.Results(AppliedCommand, client.ConnectionMessage, process.OverallProgress, activeId != null);
            if (resultsText.text != text) resultsText.text = text;
        }

        private void OnProcessCompleted()
        {
            showCompletion = true;
            completedCommand = activeId != null && !terminalReported ? AppliedCommand : null;
            UpdateResultLayout();
            if (activeId == null || terminalReported) return;
            terminalReported = true;
            client.ReportCompleted(activeId, "배출 완료 · 설명용 공정 시연 종료");
        }

        private void UpdateResultLayout()
        {
            if (resultPanel == null) return;
            float extraWidth = showCompletion ? 96f : 0f;
            resultPanel.sizeDelta = resultPanelSize + new Vector2(extraWidth, 0f);
            resultPanel.anchoredPosition = resultPanelPosition - new Vector2(extraWidth * (1f - resultPanel.pivot.x), 0f);
            if (resultBackground != null)
                resultBackground.color = showCompletion ? (Color)new Color32(17, 29, 43, 230) : resultBackgroundColor;
        }

        private void OnProcessFailed(string reason)
        {
            if (activeId == null || terminalReported) return;
            terminalReported = true;
            client.ReportError(activeId, reason);
        }
    }
}
