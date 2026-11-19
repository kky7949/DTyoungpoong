using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using Newtonsoft.Json;
using UnityEngine;
using UnityEngine.Networking;

namespace Youngpoong.Integration
{
    // HTTP transport only. The bridge owns the illustrative factory animation.
    [DisallowMultipleComponent]
    public sealed class FastApiFactoryClient : MonoBehaviour
    {
        [SerializeField] private string baseUrl = "";
        [SerializeField, Min(0.2f)] private float intervalSeconds = 1f;
        [SerializeField, Range(1, 5)] private int timeoutSeconds = 5;

        public event Action<FactoryCommandDto> CommandReceived;
        public bool HasActiveCommand => active != null;
        public string ConnectionMessage { get; private set; } = "서버 주소 미설정 · 로컬 시연 가능";
        public bool IsHalted => halted;

        private readonly HashSet<string> receivedIds = new HashSet<string>();
        private FactoryCommandDto active;
        private string state;
        private float progress;
        private string message;
        private bool halted;
        private bool hasStarted;
        private UnityWebRequest pendingRequest;
        private static FastApiFactoryClient instance;

        private void OnEnable()
        {
            if (instance != null && instance != this)
            {
                Halt("통신 컴포넌트는 실행 중인 씬 전체에 하나만 두세요.");
                enabled = false;
                return;
            }
            instance = this;

            // Re-enabling cannot safely reconstruct a consumed command or server state.
            if (hasStarted)
                Halt("통신 컴포넌트가 재활성화됐습니다. B 실행 상태를 확인한 뒤 Play를 다시 시작하세요.");
        }

        private void Start()
        {
            hasStarted = true;
            if (halted || instance != this) return;
            if (string.IsNullOrWhiteSpace(baseUrl))
            {
                ConnectionMessage = "서버 주소 미설정 · 로컬 시연 가능";
                return;
            }

            Uri uri;
            if (!Uri.TryCreate(baseUrl.Trim(), UriKind.Absolute, out uri) ||
                (uri.Scheme != "http" && uri.Scheme != "https") ||
                !string.IsNullOrEmpty(uri.UserInfo) || !string.IsNullOrEmpty(uri.Query) || !string.IsNullOrEmpty(uri.Fragment))
            {
                Halt("Base URL에 http://서버주소:8001 형식의 주소를 입력하세요.");
                return;
            }
            baseUrl = baseUrl.Trim().TrimEnd('/');
            if (!HasExecutionHandler()) return;
            ConnectionMessage = "서버 연결 확인 중";
            StartCoroutine(Communicate());
        }

        private void OnDisable()
        {
            if (instance == this) instance = null;
            StopAllCoroutines();
            if (pendingRequest != null)
            {
                UnityWebRequest request = pendingRequest;
                request.Abort();
                ReleaseRequest(request);
            }
            if (hasStarted)
            {
                halted = true;
                ConnectionMessage = active == null
                    ? "통신 중지 · 재개 전 B 상태 확인 필요"
                    : "통신 중지 · 진행 중 명령의 B 상태 확인 필요";
            }
        }

        private IEnumerator Communicate()
        {
            while (isActiveAndEnabled && !halted)
            {
                if (active == null)
                {
                    // Never consume a command if the bridge is absent or disabled.
                    if (!HasExecutionHandler()) yield break;
                    yield return PollCommand();
                }
                else yield return SendStatus();
                yield return new WaitForSecondsRealtime(Mathf.Max(0.2f, intervalSeconds));
            }
        }

        private bool HasExecutionHandler()
        {
            if (CommandReceived != null) return true;
            Halt("실제 공정 연결이 없어 명령 조회를 시작하지 않습니다.");
            return false;
        }

        private IEnumerator PollCommand()
        {
            UnityWebRequest request = UnityWebRequest.Get(baseUrl + "/api/v1/factory/commands/next");
            request.timeout = Mathf.Clamp(timeoutSeconds, 1, 5);
            pendingRequest = request;
            try
            {
                UnityWebRequestAsyncOperation operation = FactoryRequestIssuance.TrySend(
                    request.SendWebRequest, Halt, "명령 조회");
                if (operation == null) yield break;
                yield return operation;
                if (request.result != UnityWebRequest.Result.Success)
                {
                    LogFailure(request);
                    if (IsProtocolRejection(request.responseCode)) Halt("명령 조회가 거부됐습니다. B 서버 응답을 확인하세요.");
                    yield break;
                }
                if (request.responseCode == 204)
                {
                    ConnectionMessage = "연결됨 · 명령 대기";
                    yield break;
                }
                if (request.responseCode != 200)
                {
                    Halt("예상하지 못한 명령 응답: HTTP " + request.responseCode);
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
                    Halt("명령 해석 실패 · B 담당자 확인 필요: " + exception.Message);
                    yield break;
                }
                if (!receivedIds.Add(command.command_id))
                {
                    Halt("중복 명령은 실행하지 않습니다: " + command.command_id);
                    yield break;
                }
                active = command;
                state = "running";
                progress = 0f;
                message = "명령 수신 · 시연 실행 준비";
                ConnectionMessage = "연결됨 · 실행 명령 수신";
                Debug.Log("[B 명령 수신] " + command.command_id, this);
                try
                {
                    if (CommandReceived == null) ReportError(command.command_id, "실제 공정 연결이 해제되어 시작하지 못했습니다.");
                    else CommandReceived(command);
                }
                catch (Exception exception)
                {
                    ReportError(command.command_id, "Unity 실행 오류: " + exception.Message);
                }
            }
            finally { ReleaseRequest(request); }
        }

        private IEnumerator SendStatus()
        {
            string sentId = active.command_id;
            string sentState = state;
            float sentProgress = progress;
            string json = JsonConvert.SerializeObject(new {
                command_id = sentId, state = sentState, progress_pct = sentProgress, message = message
            });
            UnityWebRequest request = new UnityWebRequest(baseUrl + "/api/v1/factory/status", "POST");
            request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json; charset=utf-8");
            request.timeout = Mathf.Clamp(timeoutSeconds, 1, 5);
            pendingRequest = request;
            try
            {
                UnityWebRequestAsyncOperation operation = FactoryRequestIssuance.TrySend(
                    request.SendWebRequest, Halt, "상태 보고");
                if (operation == null) yield break;
                yield return operation;
                if (request.result != UnityWebRequest.Result.Success)
                {
                    LogFailure(request);
                    if (IsProtocolRejection(request.responseCode))
                        Halt("상태 보고가 거부됐습니다. 공정을 재실행하지 말고 명령 ID와 B 상태를 확인하세요.");
                    // Retain the latest terminal state for retry; never restart the animation.
                    yield break;
                }
                if (request.responseCode != 200)
                {
                    Halt("상태 접수 확인 실패: HTTP " + request.responseCode);
                    yield break;
                }
                try
                {
                    FactoryStatusProtocol.ValidateAcknowledgement(request.downloadHandler.text, sentId, sentState, sentProgress);
                }
                catch (Exception exception)
                {
                    Halt("상태 접수 응답 확인 실패: " + exception.Message);
                    yield break;
                }
                ConnectionMessage = "연결됨 · 상태 보고 접수";
                if (sentState == "completed" || sentState == "error")
                {
                    Debug.Log("[B 상태 접수] " + sentId + " / " + sentState, this);
                    active = null;
                }
            }
            finally { ReleaseRequest(request); }
        }

        public void ReportProgress(string commandId, float percentage, string detail = "공정 시연 실행 중")
        {
            if (!MatchesRunning(commandId)) return;
            if (float.IsNaN(percentage) || float.IsInfinity(percentage) || percentage < 0f || percentage < progress || percentage > 100f)
            {
                Debug.LogWarning("[B 연결] 진행률은 감소하지 않는 0~100 값이어야 합니다.", this);
                return;
            }
            progress = percentage;
            message = detail ?? "공정 시연 실행 중";
        }

        public void ReportCompleted(string commandId, string detail = "공정 시연 완료")
        {
            if (!MatchesRunning(commandId)) return;
            state = "completed";
            progress = 100f;
            message = detail ?? "공정 시연 완료";
        }

        public void ReportError(string commandId, string detail)
        {
            if (!MatchesRunning(commandId)) return;
            state = "error";
            message = detail ?? "공정 시연 오류";
        }

        private bool MatchesRunning(string id)
        {
            return !halted && active != null && active.command_id == id && state == "running";
        }

        private static bool IsProtocolRejection(long code) { return code == 400 || code == 409 || code == 422; }

        private void Halt(string detail)
        {
            halted = true;
            ConnectionMessage = "연동 중지 · " + detail;
            Debug.LogError("[B 연결] " + detail, this);
        }

        private void LogFailure(UnityWebRequest request)
        {
            ConnectionMessage = "통신 실패 · 재시도 중 (HTTP " + request.responseCode + ")";
            Debug.LogWarning("[B HTTP 오류] " + request.responseCode + " / " + request.error +
                " / " + (request.downloadHandler == null ? "" : request.downloadHandler.text), this);
        }

        private void ReleaseRequest(UnityWebRequest request)
        {
            if (!ReferenceEquals(pendingRequest, request)) return;
            pendingRequest = null;
            request.Dispose();
        }
    }

    // Some Unity policies reject SendWebRequest synchronously, before an operation exists.
    internal static class FactoryRequestIssuance
    {
        internal static T TrySend<T>(Func<T> send, Action<string> halt, string requestName) where T : class
        {
            try { return send(); }
            catch (Exception exception)
            {
                halt(requestName + " 요청 시작 실패 · Unity HTTP 허용 설정과 서버 주소를 확인하세요: " + exception.Message);
                return null;
            }
        }
    }
}
