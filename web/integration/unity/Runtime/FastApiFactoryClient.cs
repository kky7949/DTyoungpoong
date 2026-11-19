using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using Newtonsoft.Json;
using UnityEngine;
using UnityEngine.Networking;

namespace Youngpoong.Integration
{
    // 통신만 담당합니다. 실제 설비 동작은 CommandReceived에 연결합니다.
    [DisallowMultipleComponent]
    public sealed class FastApiFactoryClient : MonoBehaviour
    {
        [SerializeField] private string baseUrl = "http://127.0.0.1:8001";
        [SerializeField, Min(0.2f)] private float intervalSeconds = 1f;
        [SerializeField, Range(1, 5)] private int timeoutSeconds = 5;

        public event Action<FactoryCommandDto> CommandReceived;
        public FactoryCommandDto CurrentCommand { get; private set; }
        public bool HasActiveCommand { get { return active != null; } }
        private readonly HashSet<string> receivedIds = new HashSet<string>();
        private FactoryCommandDto active;
        private string state;
        private float progress;
        private string message;
        private bool halted;
        private UnityWebRequest pendingRequest;
        private static FastApiFactoryClient instance;

        private void OnEnable()
        {
            if (instance != null && instance != this)
            {
                Debug.LogError("[B 연결] 통신 컴포넌트는 실행 중인 씬 전체에 하나만 두세요.", this);
                enabled = false;
                return;
            }
            Uri uri;
            if (!Uri.TryCreate(baseUrl, UriKind.Absolute, out uri) ||
                (uri.Scheme != "http" && uri.Scheme != "https"))
            {
                Debug.LogError("[B 연결] Base URL에 http://IP:8001 형식의 주소를 입력하세요.", this);
                return;
            }
            baseUrl = baseUrl.TrimEnd('/');
            instance = this;
            StartCoroutine(Communicate());
        }

        private void OnDisable()
        {
            if (instance == this) instance = null;
            if (pendingRequest != null) pendingRequest.Abort();
            StopAllCoroutines();
            pendingRequest = null;
        }

        private IEnumerator Communicate()
        {
            while (isActiveAndEnabled && !halted)
            {
                // 실행 중에는 상태 POST가 연결 유지 역할도 하므로 새 명령을 가져오지 않습니다.
                if (active == null) yield return PollCommand();
                else yield return SendStatus();
                yield return new WaitForSecondsRealtime(Mathf.Max(0.2f, intervalSeconds));
            }
        }

        private IEnumerator PollCommand()
        {
            using (UnityWebRequest request = UnityWebRequest.Get(baseUrl + "/api/v1/factory/commands/next"))
            {
                request.timeout = timeoutSeconds;
                pendingRequest = request;
                yield return request.SendWebRequest();
                pendingRequest = null;
                if (request.result != UnityWebRequest.Result.Success)
                {
                    LogFailure(request);
                    yield break;
                }
                if (request.responseCode == 204) yield break;
                if (request.responseCode != 200)
                {
                    Debug.LogError("[B 연결] 예상하지 못한 명령 응답: " + request.responseCode, this);
                    yield break;
                }
                FactoryCommandDto command;
                try
                {
                    command = JsonConvert.DeserializeObject<FactoryCommandDto>(request.downloadHandler.text);
                    if (command == null) throw new ArgumentException("빈 명령입니다.");
                    command.Validate();
                }
                catch (Exception exception)
                {
                    halted = true;
                    Debug.LogError("[B 연결] 명령 해석 실패. 재시작 전 B 담당자에게 확인하세요: " + exception.Message, this);
                    yield break;
                }
                if (!receivedIds.Add(command.command_id))
                {
                    halted = true;
                    Debug.LogError("[B 연결] 중복 명령입니다. 실행하지 않습니다: " + command.command_id, this);
                    yield break;
                }
                active = command;
                CurrentCommand = command;
                state = "running";
                progress = 0;
                message = "명령 수신 · Unity 동작 연결 대기";
                Debug.Log("[B 명령 수신] " + request.downloadHandler.text, this);
                try
                {
                    if (CommandReceived != null) CommandReceived(command);
                    else Debug.LogWarning("[B 연결] 실제 공정 실행 코드를 CommandReceived에 연결해야 합니다.", this);
                }
                catch (Exception exception)
                {
                    ReportError(command.command_id, "Unity 실행 오류: " + exception.Message);
                }
            }
        }

        private IEnumerator SendStatus()
        {
            string sentId = active.command_id;
            string sentState = state;
            float sentProgress = progress;
            string json = JsonConvert.SerializeObject(new {
                command_id = sentId, state = sentState, progress_pct = sentProgress, message = message
            });
            using (UnityWebRequest request = new UnityWebRequest(baseUrl + "/api/v1/factory/status", "POST"))
            {
                request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
                request.downloadHandler = new DownloadHandlerBuffer();
                request.SetRequestHeader("Content-Type", "application/json; charset=utf-8");
                request.timeout = timeoutSeconds;
                pendingRequest = request;
                yield return request.SendWebRequest();
                pendingRequest = null;
                if (request.result != UnityWebRequest.Result.Success)
                {
                    LogFailure(request);
                    if (request.responseCode == 400 || request.responseCode == 409 || request.responseCode == 422)
                    {
                        halted = true;
                        Debug.LogError("[B 연결] 상태 보고가 거부됐습니다. 공정을 다시 실행하지 말고 명령 ID와 B 서버 상태를 확인하세요.", this);
                    }
                    // 통신 실패는 다음 주기에 보고를 재시도하며 공정을 재시작하지 않습니다.
                    yield break;
                }
                if (sentState == "completed" || sentState == "error")
                {
                    Debug.Log("[B 상태 접수] " + sentId + " / " + sentState, this);
                    active = null;
                }
            }
        }

        public void ReportProgress(string commandId, float percentage, string detail = "Unity 공정 실행 중")
        {
            if (!MatchesRunning(commandId)) return;
            if (float.IsNaN(percentage) || float.IsInfinity(percentage) || percentage < progress || percentage > 100)
            {
                Debug.LogWarning("[B 연결] 진행률은 감소하지 않는 0~100 값이어야 합니다.", this);
                return;
            }
            progress = percentage;
            message = detail ?? "Unity 공정 실행 중";
        }

        public void ReportCompleted(string commandId, string detail = "Unity 공정 완료")
        {
            if (!MatchesRunning(commandId)) return;
            state = "completed";
            progress = 100;
            message = detail ?? "Unity 공정 완료";
        }

        public void ReportError(string commandId, string detail)
        {
            if (!MatchesRunning(commandId)) return;
            state = "error";
            message = detail ?? "Unity 공정 오류";
        }

        private bool MatchesRunning(string id)
        {
            return !halted && active != null && active.command_id == id && state == "running";
        }

        private void LogFailure(UnityWebRequest request)
        {
            Debug.LogWarning("[B HTTP 오류] " + request.responseCode + " / " + request.error +
                " / " + (request.downloadHandler == null ? "" : request.downloadHandler.text), this);
        }

        [ContextMenu("통신 시험/현재 명령 수동 완료")]
        private void ManualComplete()
        {
            if (active != null) ReportCompleted(active.command_id, "통신 시험용 수동 완료 · 실제 공정 완료 아님");
        }
        [ContextMenu("통신 시험/현재 명령 수동 오류")]
        private void ManualError()
        {
            if (active != null) ReportError(active.command_id, "통신 시험용 수동 오류");
        }
    }
}
