# Unity 공정 시연과 웹 연동

`unity/`는 Unity Hub에서 여는 프로젝트 루트입니다. 기본 씬 `FactoryDemoExhibitionApiNatural`은 시작 화면에서 B 서버에 연결하거나 로컬 시연을 선택할 수 있습니다. 연결 시 웹 명령을 받아 공정을 재생하고, 원료 성분과 예상 회수율을 표시하며, 진행률과 완료를 서버로 보고합니다. [Unity 진행 이력](CHANGELOG.md)

씬 실행에는 아래 회사 제공 패키지 4개와 로컬 유리 재질 복원이 필요합니다. 실제 웹 연결에는 팀이 운영하는 B 서버 주소를 사용합니다.

## 환경

| 항목 | 고정 버전 |
| --- | --- |
| Unity Editor | 6000.0.68f1 |
| High Definition RP | 17.0.4 |
| Universal RP | 17.0.4 |
| Alembic | 2.4.7 |
| Input System | 1.18.0 |
| Unity UI 및 TMP | com.unity.ugui 2.0.0 및 포함한 TMP 리소스 |
| Newtonsoft JSON | 3.2.1 |

HDRP를 활성 렌더러로 사용합니다. Color Space는 Linear, Active Input Handling은 Input System입니다. URP 패키지는 원본 카메라 컴포넌트 참조를 충족합니다. 패키지 버전은 `Packages/manifest.json`과 잠금 파일에 고정했습니다.

## 포함 범위

```text
unity/
├── Assets/
│   ├── Scripts/                  # 수위 제어 및 이전 데모 공정
│   ├── FactoryIntegration/       # API, 공정 실행, 카메라, Editor 검증·빌드 메뉴
│   ├── Scenes/                   # 시연 씬 6개
│   ├── Exhibition/               # 한글 폰트·OFL, 전시 조명 설정
│   ├── HDRPDefaultResources/     # 파이프라인·전역 설정·기본 Volume Profile
│   ├── TextMesh Pro/             # 소형 UI 리소스와 원래의 라이선스·출처 안내
│   └── InputSystem_Actions.inputactions
├── Packages/                     # manifest.json, packages-lock.json
├── ProjectSettings/              # HDRP·입력·씬 빌드 목록 등
├── EXTERNAL_ASSETS.json           # 외부 패키지의 SHA-256·크기·경로·GUID
├── tools/                        # 씬 내장 메시 검사, 서버 주소 테스트, 로컬 유리 재질 복원
├── CHANGELOG.md                   # 날짜별 구현·검증 이력
├── .gitignore
└── README.md
```

Build Settings는 `FactoryDemoExhibitionApiNatural`을 활성화합니다. 제공 패키지의 `water.abc`를 불러와 재생할 때 물 메시가 생성됩니다. 서버 주소는 시작 화면에서 입력합니다.

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
3. Project 창에서 아래 프리팹과 물 캐시를 확인합니다. Unity를 닫고 `unity/`에서 `python3 tools/restore_exhibition_glass.py`를 실행하면 제공 패키지의 유리를 바탕으로 전시용 재질이 기존 GUID로 생성됩니다.
4. Unity를 다시 열고 `Assets/Scenes/FactoryDemoExhibitionApiNatural.unity`의 프리팹, 폰트, 물 캐시, 유리 참조를 확인합니다. TMP Essential Resources와 나눔고딕 리소스는 포함되어 있습니다.

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
| `FactoryDemoProcessSample` | 물 주입부터 배출까지 이어지는 로컬 시연 |
| `FactoryDemoExhibition` | 전시용 한글 패널과 조명을 적용한 로컬 시연 |
| `FactoryDemoExhibitionApi` | 11월 20일 전시 UI를 적용한 기존 API 씬. Inspector에서 B 서버 주소 설정 |
| `FactoryDemoExhibitionApiNatural` | 밝은 전시 UI와 앱 시작 시 서버 설정. 기본 실행 씬 |

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

`FactoryProcessDemoController`는 이전 데모를 담당합니다. API 씬에서는 `IntegratedFactoryProcessController`가 공정 단계와 실제 애니메이션 진행률을 관리하고, `FactoryApiSimulationBridge`가 조건 패널과 완료 화면을 갱신합니다. `FactoryProcessCameras`가 전체·주입구·탱크 근접 구도를 0.8초에 걸쳐 전환합니다.

### 복원 후 Play 확인

- Ready에서 Start를 누르면 물 주입→수면 안정화→부속물 투입 순서로 진행되는지 확인합니다.
- Mixing에서 교반이 점차 빨라지고 물색이 바뀌며 마지막 2초에 조각이 사라지는지 확인합니다.
- 배출로 넘어갈 때 다른 물 표면으로 교체되지 않는지 확인합니다.
- 진행 중 및 완료 후 Reset을 누르면 Ready·초기 수면·물색·부속물·교반 상태가 복원되는지 확인합니다.
- 두 번째 Start도 같은 순서로 진행되고, 실행 중 Start 중복 입력이 막히는지 확인합니다.

## 웹 연결과 개발용 앱

1. Natural 씬을 Play하거나 앱을 열면 나오는 시작 화면에 팀에서 받은 B 서버 주소를 입력하고 **연결**을 누릅니다. 주소에는 HTTP 또는 HTTPS와 필요한 포트까지 포함합니다. 연결에 성공한 주소는 다음 실행 때 채워집니다. 주소 변경은 앱을 다시 열어 화면에서 입력하면 됩니다. A 서버 주소는 B 서버의 분석 서비스 설정에서 관리합니다. 서버 없이 진행하려면 **로컬 시연**을 선택합니다.
2. 시작 화면은 `/api/v1/factory/state`를 조회하여 B 서버를 확인합니다. `GET /api/v1/factory/commands/next`는 명령을 소비하므로 Unity 소비자 하나만 실행합니다. Mock Unity 소비자는 종료합니다. [웹·서버 실행 안내](../web/README.md)
3. 명령 대기 표시를 확인합니다. HMI에서 조건을 확정하고 가상 공장 적용을 누르면 Unity가 명령을 받아 공정을 실행합니다.
4. 원료명·투입량과 Ni/Co/Li/Mn/Cu/Fe/Al 성분, 공정 조건 세 가지, 예상 Ni·Co 회수율을 비교합니다. 성분 값 0은 `0%`, null이나 누락은 `미입력`입니다.
5. 배출 뒤 전체 구도와 확대된 예상 회수율이 표시되는지 확인합니다. Unity는 `POST /api/v1/factory/status`로 진행률과 상태를 보고합니다. HMI 또는 상태 조회에서 같은 명령 ID의 `completed`와 100%를 확인합니다. 다음 공정이 시작될 때 완료 화면이 바뀝니다.

개발 서버의 HTTP는 Editor 및 개발용 빌드에서 허용합니다. Natural 앱을 만들려면 macOS Build Support를 설치하고 Unity를 닫은 뒤 프로젝트 폴더 `unity/`에서 실행합니다.

```sh
"/Applications/Unity/Hub/Editor/6000.0.68f1/Unity.app/Contents/MacOS/Unity" \
  -batchmode -quit -projectPath "$PWD" -buildTarget StandaloneOSX \
  -executeMethod Youngpoong.Integration.FactoryMacDevelopmentBuild.BuildNaturalBatch
```

Unity 프로젝트 옆 `Builds/macOS/Natural/YoungpoongFactoryNatural.app`에 Intel·Apple Silicon Universal 개발 앱이 생성됩니다. 메뉴의 **Build macOS Development App**은 기존 API 씬을 빌드합니다. 앱에는 제공 물 캐시가 포함되므로 팀이 허용한 환경에서 사용합니다.

## 검증과 파일 관리

11월 24일 같은 Mac에서 모델·웹·Unity Editor의 완료 왕복을, 25일에는 macOS 앱에서 로컬 B 서버 두 주소의 명령 실행과 완료 보고를 확인했습니다. 실제 전시 네트워크와 Windows 빌드·실행은 추가 확인이 필요합니다. [날짜별 시험 이력](CHANGELOG.md)

씬을 Unity에서 다시 저장한 뒤에는 `python3 tools/check_scene_payloads.py`로 내장 메시를 점검합니다. 커밋할 복사본은 확인된 임시 메시만 분리하고 Base URL을 공란으로 유지합니다. 빌드, 원본 에셋, 로컬 로그와 내부 서버 주소는 로컬에서 관리합니다.
