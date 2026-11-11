# Unity 공정 시연 체크포인트

`unity/`는 Unity Hub에서 여는 프로젝트 루트입니다. 공장·수조·맵 배치와 공정 시연을 사용자가 Play에서 확인한 2026년 11월 11일 체크포인트입니다.

**회사 제공 에셋은 저장소에 없습니다.** 아래 원본 패키지 4개를 복원해야 씬이 완성됩니다. Git 체크아웃만으로 모델이 표시되는 프로젝트는 아닙니다. 실제 웹/API/AI 연결도 아직 없습니다.

## 환경

| 항목 | 고정 버전 |
| --- | --- |
| Unity Editor | 6000.0.68f1 |
| High Definition RP | 17.0.4 |
| Universal RP | 17.0.4 |
| Alembic | 2.4.7 |
| Input System | 1.18.0 |
| Unity UI 및 TMP | com.unity.ugui 2.0.0 및 포함한 TMP 리소스 |

HDRP가 활성 렌더러이고 Color Space는 Linear, Active Input Handling은 Input System입니다. URP는 세 원본 씬에 남아 있는 카메라 컴포넌트 참조와 TMP 리소스 호환성을 위해 유지합니다. 사용하지 않는 URP 템플릿 파이프라인 에셋은 복사하지 않았습니다.

`Packages/manifest.json`과 `packages-lock.json`은 필요한 패키지와 기존에 해결된 버전을 기록합니다. AI Assistant·에디터 개인 설정 등 시연에 필요하지 않은 항목은 제외했습니다. 이것은 AI 기능을 추가한 프로젝트가 아닙니다.

## 포함 범위

```text
unity/
├── Assets/
│   ├── Scripts/                  # WaterLevelController, FactoryProcessDemoController
│   ├── Scenes/                   # FactoryDemo, FactoryDemoProcess, FactoryDemoProcessSample
│   ├── HDRPDefaultResources/     # 파이프라인·전역 설정·기본 Volume Profile
│   ├── TextMesh Pro/             # 소형 UI 리소스와 원래의 라이선스·출처 안내
│   └── InputSystem_Actions.inputactions
├── Packages/                     # manifest.json, packages-lock.json
├── ProjectSettings/              # HDRP·입력·씬 빌드 목록 등
├── EXTERNAL_ASSETS.json           # 외부 패키지의 SHA-256·크기·경로·GUID
├── tools/check_scene_payloads.py  # 씬 내부의 메시 데이터 공개 방지 검사
├── .gitignore
└── README.md
```

스크립트와 .meta, Assets의 필요한 폴더 .meta를 원본 그대로 보존했습니다. 세 씬의 통합용 복사본에서는 Alembic이 임시 생성한 `dyn: Cylinder_001` 메시 1개와 이를 가리키는 MeshFilter 프리팹 오버라이드 1개씩만 제거했습니다. 모델의 정점·인덱스가 씬에 내장되어 공개되는 것을 막고, 외부 프리팹의 기본값과 Alembic 플레이어가 `water.abc`에서 메시를 다시 생성하도록 했습니다. 다른 씬 객체·GUID·Inspector 값은 보존했습니다.

Build Settings는 최신 `FactoryDemoProcessSample`만 활성화하고, 나머지 두 씬은 비활성 항목으로 보관합니다. 원본 프로젝트의 씬과 설정은 수정하지 않았습니다.

## 외부 에셋 복원

권한이 있는 팀원이 전달받은 원본 패키지를 준비합니다. 기존 제공 자료의 상대 위치는 `Youngpoong/Modeling/{object,map,effect}/`입니다. 패키지와 회사 모델·재질·프리팹·텍스처·Alembic은 저장소에 업로드하지 않습니다.

다음 순서로 Unity의 **Assets > Import Package > Custom Package**에서 임포트합니다. 각 패키지의 에셋과 .meta를 함께 유지하고, 경로를 옮기거나 .meta를 새로 생성하지 않습니다.

| 순서 | 원본 상대 경로 | 파일 크기 |
| --- | --- | ---: |
| 1 | `object/fac_watertank.unitypackage` | 984,377,637 bytes |
| 2 | `object/waste_battery.unitypackage` | 19,268,378 bytes |
| 3 | `map/factory_inner_2.unitypackage` | 25,569,173 bytes |
| 4 | `effect/MapSetting_3.unitypackage` | 592,347 bytes |

`EXTERNAL_ASSETS.json`의 SHA-256과 패키지 크기를 먼저 비교합니다. 예를 들어 macOS에서는 `shasum -a 256 <패키지 경로>`로 확인할 수 있습니다. JSON에는 원본 패키지 4개 안의 48개 에셋 항목이 기록되어 있습니다. 공유 재질·텍스처 4개가 중복되어 고유 경로는 44개입니다.

### 복원 순서

1. 저장소를 받은 뒤 Unity Hub에서 **이 `unity/` 폴더**를 추가하고 Unity 6000.0.68f1로 엽니다. Unity Registry에 접근할 수 있는 환경에서 패키지 복원을 기다립니다.
2. 위 4개 패키지를 순서대로 임포트합니다. 공통 에셋이 같은 GUID로 겹치는 경우 원래 패키지의 참조를 유지합니다. 기존 Git 파일인 씬·스크립트·HDRP·TMP 리소스를 다른 템플릿으로 덮어쓰지 않습니다.
3. Project 창에서 다음 프리팹과 물 캐시가 생겼는지 확인합니다. 프리팹 GUID는 표와 일치해야 합니다.
4. `Assets/Scenes/FactoryDemoProcessSample.unity`를 열고 Missing Prefab·Missing Script·폰트 또는 물 캐시 누락 오류가 없는지 확인합니다. TMP Essential Resources는 이미 포함되어 있으므로 다시 임포트할 필요가 없습니다.
5. HDRP 전역/기본 파이프라인 참조, Input System, 아래 Inspector 값과 연결을 확인하고 Play 검증을 진행합니다. Unity가 패키지 에셋을 현재 HDRP 버전으로 재직렬화하는 경우 제공 에셋 폴더는 계속 Git 제외 상태로 둡니다.

| 외부 프리팹 | GUID |
| --- | --- |
| `Assets/object/fac_watertank_1.prefab` | `ab61126e00f01a34a91c4e05f338017d` |
| `Assets/object/waste_battery_1.prefab` | `13efd63a59ccd0a49ad17912219d96d5` |
| `Assets/Map/factory_inner_2.prefab` | `ce50249b99628c641bcd71b64b93eda7` |
| `Assets/effect/Koreazinc_MapSetting.prefab` | `bd3c0086ae524de46a5ed9b9b7099fb5` |

물 캐시는 `Assets/00_Model/03_Koreazinc/02_Model/water.abc`이며 크기는 **1,578,106,917 bytes**입니다. `fac_watertank.unitypackage`에 포함됩니다. 이 파일을 빈 파일이나 다른 물 모델로 대체하면 최신 시연이 재현되지 않습니다.

제공 에셋은 `Assets/00_Model/`, `Assets/object/`, `Assets/Map/`, `Assets/effect/`에 복원됩니다. 이 폴더와 .meta는 `.gitignore`로 제외됩니다. Library·Temp·Logs·Obj·UserSettings·빌드와 녹화 파일도 커밋하지 않습니다.

### 원본에서 확인한 참조 한계

`factory_inner_2`의 `Assets/00_Model/03_Koreazinc/02_Model/wall_all.fbx.meta`에는 `Wall_01` 재질을 GUID `a3ac9ed7b7747954685f1e82f491c7fa`로 연결한 항목이 있습니다. 이 재질은 제공 패키지 4개와 현재 원본 프로젝트 모두에 없습니다. 이번 통합이 만든 누락은 아니며, 원본과 씬을 유지한 채 `EXTERNAL_ASSETS.json`의 `known_source_issues`에 기록했습니다. 복원 후 해당 재질 슬롯과 공장 외관을 확인하고, 필요하면 제공처에 원본 재질을 확인합니다. 임의의 대체 재질을 지정해 해결한 것으로 보고하지 않습니다.

## 실행 씬과 확인된 동작

| 씬 | 용도 |
| --- | --- |
| `FactoryDemo` | 기존 공장·수조 배치와 수위 슬라이더 |
| `FactoryDemoProcess` | 기존 Start/Reset, 부속물 투입과 수위 변화 시연 |
| `FactoryDemoProcessSample` | 최신 단계별 시연. 현재 체크포인트의 기본 씬 |

최신 씬의 상태 흐름은 다음과 같습니다.

```text
Ready → Filling → Settling → Feeding → Mixing → Draining → Complete
                         Reset → Ready
```

| Inspector 항목 | 저장된 값 | 동작 |
| --- | ---: | --- |
| Sample Fill Seconds | 4초 | 위에서 물 주입 |
| Sample Feed Seconds | 2.5초 | 수면 안정화 후 부속물 투입 |
| Sample Mix Seconds | 6초 | 교반 점진 가속과 물색 변화 |
| Sample Dissolve Seconds | 2초 | 교반 마지막 2초와 겹쳐 조각 소실 |
| Sample Drain Seconds | 5.5초 | 같은 Alembic 표면을 유지한 배출 |

Settling은 캐시 시간 12초에서 16초까지 재생 속도를 완만하게 낮추는 단계입니다. 소요 시간은 코드가 계산하며, 현재 주입 설정에서는 약 2초입니다. 위 5개 Inspector 파라미터와 별개입니다. Reset은 수위·물색·조각·교반각과 상태를 처음으로 복원합니다.

`FactoryProcessDemoController`는 기존 수위 컨트롤러, 서로 다른 Start/Reset 버튼, TMP 상태 텍스트와 샘플 Alembic·Battery 참조가 필요합니다. 최신 씬은 `Use Sample Sequence`가 켜져 있습니다. `WaterLevelController`는 `End` Blend Shape가 있는 `Water_2`의 SkinnedMeshRenderer를 사용합니다.

### 복원 후 Play 확인

- Ready에서 Start를 누르면 물 주입→수면 안정화→부속물 투입 순서로 진행되는지 확인합니다.
- Mixing에서 교반이 점차 빨라지고 물색이 바뀌며 마지막 2초에 조각이 사라지는지 확인합니다.
- 배출로 넘어갈 때 다른 물 표면으로 교체되지 않는지 확인합니다.
- 진행 중 및 완료 후 Reset을 누르면 Ready·초기 수면·물색·부속물·교반 상태가 복원되는지 확인합니다.
- 두 번째 Start도 같은 순서로 진행되고, 실행 중 Start 중복 입력이 막히는지 확인합니다.

## 검증 범위와 다음 연결 작업

사용자가 원본 프로젝트의 최신 효과를 Play에서 확인했습니다. 저장소 통합 때는 C# 두 파일을 실제 Unity Core/uGUI/TMP/Alembic/HDRP 어셈블리로 경고를 오류로 처리하여 컴파일했습니다. 원본 미변경·코드와 .meta 해시·씬의 임시 메시 제거 외 변경 없음·GUID 의존성·패키지 버전과 원본 해시·포함 파일 크기도 검사했습니다. 위 원본 재질 참조 1건은 기존 한계로 구분하며, 통합으로 새로 발생한 미해결 GUID 참조는 없습니다.

임시 메시를 제거한 통합 씬을 새 체크아웃에서 전체 Unity 임포트·Play·빌드 시험한 것은 아닙니다. 외부 에셋을 복원한 환경에서는 위 Play 항목을 다시 확인해야 합니다.

Unity에서 씬을 다시 저장하면 Alembic의 임시 메시가 다시 직렬화될 수 있습니다. 업로드 전 `unity/`에서 `python3 tools/check_scene_payloads.py`를 실행합니다. 이 도구는 읽기 전용이며, 실패하면 내장 메시를 포함한 씬을 그대로 커밋하지 않고 통합용 복사본을 검토합니다. 파일 확장자나 크기 검사만으로는 내장 지오메트리를 찾을 수 없습니다.

현재 구현은 시연용 시각 효과입니다. 원본 영상과 완전히 동일한 물리 시뮬레이션이 아니며, 색 변화나 조각 소실이 AI 회수율 예측 결과를 나타내지도 않습니다. 실제 웹/API 명령 수신·상태 보고, AI 결과에 따른 표현과 시연 파라미터 변경은 후속 작업입니다.
