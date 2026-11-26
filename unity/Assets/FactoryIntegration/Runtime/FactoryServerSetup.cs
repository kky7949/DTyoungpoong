using System.Collections;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using TMPro;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;

namespace Youngpoong.Integration
{
    [DisallowMultipleComponent]
    public sealed class FactoryServerSetup : MonoBehaviour
    {
        private const string SavedAddressKey = "FactoryExhibition.BServerAddress";

        [SerializeField] private FastApiFactoryClient client = null;
        [SerializeField] private TMP_InputField addressInput = null;
        [SerializeField] private TMP_Text feedbackText = null;
        [SerializeField] private Button connectButton = null;
        [SerializeField] private Button localButton = null;

        private void OnEnable()
        {
            addressInput.SetTextWithoutNotify(PlayerPrefs.GetString(SavedAddressKey, ""));
            connectButton.onClick.AddListener(Connect);
            localButton.onClick.AddListener(ContinueLocally);
            addressInput.onSubmit.AddListener(Submit);
        }

        private void OnDisable()
        {
            connectButton.onClick.RemoveListener(Connect);
            localButton.onClick.RemoveListener(ContinueLocally);
            addressInput.onSubmit.RemoveListener(Submit);
        }

        private void Submit(string value) { Connect(); }

        private void Connect()
        {
            if (!connectButton.interactable) return;
            string address;
            if (!FactoryServerAddress.TryNormalize(addressInput.text, out address))
            {
                feedbackText.text = "http:// 또는 https://가 포함된 B 서버 주소를 입력하세요.";
                return;
            }

            SetControls(false);
            feedbackText.text = "B 서버 연결 확인 중…";
            StartCoroutine(CheckAndConnect(address));
        }

        private IEnumerator CheckAndConnect(string address)
        {
            // Reading the state never takes a queued command from B.
            using (var request = UnityWebRequest.Get(address + "/api/v1/factory/state"))
            {
                request.timeout = 5;
                request.redirectLimit = 0;
                var operation = FactoryRequestIssuance.TrySend(request.SendWebRequest,
                    _ => ShowFailure("연결을 시작할 수 없습니다. 서버 주소와 HTTP 설정을 확인하세요."), "상태 확인");
                if (operation == null) yield break;
                yield return operation;

                if (request.result != UnityWebRequest.Result.Success || request.responseCode != 200)
                {
                    ShowFailure("B 서버에 접속할 수 없습니다. 주소와 서버 실행 상태를 확인하세요.");
                    yield break;
                }
                if (!HasFactoryState(request.downloadHandler.text))
                {
                    ShowFailure("가상 공장 상태를 받지 못했습니다. B 서버 주소를 확인하세요.");
                    yield break;
                }
            }

            if (!client.TryBeginCommunication(address))
            {
                ShowFailure("공정 연결을 시작할 수 없습니다. 앱을 다시 열어주세요.");
                yield break;
            }

            PlayerPrefs.SetString(SavedAddressKey, address);
            PlayerPrefs.Save();
            gameObject.SetActive(false);
        }

        private static bool HasFactoryState(string json)
        {
            try
            {
                switch ((string)JObject.Parse(json)["state"])
                {
                    case "disconnected":
                    case "idle":
                    case "queued":
                    case "running":
                    case "completed":
                    case "error":
                        return true;
                    default:
                        return false;
                }
            }
            catch (JsonException) { return false; }
            catch (System.ArgumentException) { return false; }
        }

        private void ShowFailure(string message)
        {
            feedbackText.text = message;
            SetControls(true);
        }

        private void SetControls(bool enabled)
        {
            connectButton.interactable = localButton.interactable = addressInput.interactable = enabled;
        }

        private void ContinueLocally() { gameObject.SetActive(false); }
    }
}
