using UnityEngine;

namespace Youngpoong.Integration
{
    [DisallowMultipleComponent]
    public sealed class FactoryProcessCameras : MonoBehaviour
    {
        [SerializeField] private IntegratedFactoryProcessController process;
        [SerializeField] private Camera renderCamera;
        [SerializeField] private Camera inletCamera;
        [SerializeField] private Camera tankCamera;
        [SerializeField, Min(0.01f)] private float blendSeconds = 0.8f;

        private enum View { Overview, Inlet, Tank }

        private View desiredView;
        private Shot overview, from, to;
        private float elapsed;
        private bool blending;

        private void Awake()
        {
            if (process == null || renderCamera == null || inletCamera == null || tankCamera == null ||
                renderCamera == inletCamera || renderCamera == tankCamera || inletCamera == tankCamera)
            {
                Debug.LogError("[공정 카메라] 공정 컨트롤러와 세 카메라를 연결하세요.", this);
                enabled = false;
                return;
            }

            // Keep HDRP and the audio listener on the rendering camera throughout each blend.
            inletCamera.enabled = false;
            tankCamera.enabled = false;
            overview = new Shot(renderCamera);
        }

        private void LateUpdate()
        {
            View next = SelectView(process.Phase);
            if (next != desiredView)
            {
                desiredView = next;
                from = new Shot(renderCamera);
                to = next == View.Overview ? overview : new Shot(next == View.Inlet ? inletCamera : tankCamera);
                elapsed = 0f;
                blending = true;
            }

            if (!blending) return;

            elapsed += Time.deltaTime;
            float progress = Mathf.Clamp01(elapsed / Mathf.Max(0.01f, blendSeconds));
            float eased = Mathf.SmoothStep(0f, 1f, progress);
            renderCamera.transform.SetPositionAndRotation(Vector3.Lerp(from.Position, to.Position, eased),
                Quaternion.Slerp(from.Rotation, to.Rotation, eased));
            renderCamera.fieldOfView = Mathf.Lerp(from.FieldOfView, to.FieldOfView, eased);
            blending = progress < 1f;
        }

        private static View SelectView(FactoryProcessPhase phase)
        {
            switch (phase)
            {
                case FactoryProcessPhase.Filling:
                case FactoryProcessPhase.Settling:
                case FactoryProcessPhase.Feeding:
                    return View.Inlet;
                case FactoryProcessPhase.Mixing:
                case FactoryProcessPhase.Draining:
                    return View.Tank;
                default:
                    return View.Overview;
            }
        }

        private readonly struct Shot
        {
            public readonly Vector3 Position;
            public readonly Quaternion Rotation;
            public readonly float FieldOfView;

            public Shot(Camera camera)
            {
                Position = camera.transform.position;
                Rotation = camera.transform.rotation;
                FieldOfView = camera.fieldOfView;
            }
        }
    }
}
