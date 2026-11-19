# B 파트 API 계약 초안

> B의 현재 분석 API를 기록한다. Unity 명령·상태 계약과 갱신 주기는 C 프로젝트와 합동 검증할 초안이다.

기본 경로는 `/api/v1`이며 상태 확인만 `/health`를 사용한다. JSON 식별자는 영어로 유지하고 한국어 의미를 함께 기록한다.

이 문서의 엔드포인트는 B에 구현되어 있다. 분석 응답의 `source`는 실제 A 계산(`live`)과 데모용 모의 분석(`mock`)을 구분한다. Unity 명령과 상태 계약은 C 프로젝트와 검증할 초안이다.

## 분석 응답 정보

| 필드 | 한글 의미 | 비고 |
|---|---|---|
| `schema_version` | 응답 형식 버전 | 초안에서는 `draft-1` |
| `source` | 데이터 출처 | `mock` 또는 `live` |
| `generated_at` | 응답 생성 시각 | ISO 8601 |
| `request_id` | 요청 추적 ID | 오류 및 로그 확인용 |

## `GET /health`

FastAPI 프로세스가 요청을 받을 수 있는지 확인한다.

```json
{
  "status": "ok"
}
```

## `GET /api/v1/system/status`

B의 상태, A 분석 모드 및 지원 기능을 반환한다. 아래는 모의 분석 모드의 예시다.

```json
{
  "backend": "ok",
  "a_adapter": "mock",
  "c_adapter": "mock",
  "capabilities": {
    "prediction": true,
    "optimization": true,
    "xai": false,
    "unity_control": true
  }
}
```

실제 A 모드에서는 `a_adapter`가 `live`이고 `a_ready`로 A 서버의 준비 여부를 반환한다. `c_adapter`는 현재 응답의 고정값이다. C 연결 여부는 `GET /api/v1/factory/state`의 `connection_status`로 판단한다.

## `POST /api/v1/process/analyze`

공정 조건에 따라 회수율 예측 또는 공정 추천을 요청한다. B는 빈 입력을 임의로 대치하지 않는다. 실제 A 모드의 필수 항목과 결과 구조는 [실제 A 분석 공급자](#실제-a-분석-공급자) 절을 참고한다.

대시보드의 `최적 공정 추천`은 원료 성분·투입량을 전달하고 황산량·온도·시간은 모두 null로 보낸다. `회수율 예측`은 세 공정 조건을 포함하고 `current_prediction`을 사용한다. 모의 분석 모드는 두 요청에 고정 예시값을 반환한다.

### 직접 조건 예측 요청 예시

```json
{
  "material": {
    "name": "혼합 원료 A",
    "ni_content_pct": 12.17,
    "co_content_pct": 6.98,
    "li_content_pct": 4.25,
    "mn_content_pct": 10.49,
    "cu_content_pct": 1.9,
    "fe_content_pct": 2.04,
    "al_content_pct": 3.43
  },
  "current_process": {
    "feed_amount_kg": 159.1,
    "sulfuric_acid_l": 1118.0,
    "leaching_temperature_c": 55.6,
    "leaching_time_hr": 6.32
  }
}
```

### 필드와 실제 A 허용 범위

| 필드 | 한글 이름 | 단위 | 실제 A 허용 범위 |
|---|---|---|---|
| `name` | 원료 이름 | 없음 | 선택 표시값 |
| `ni_content_pct` | 원료 내 니켈 함량 | wt% | 8~30 |
| `co_content_pct` | 원료 내 코발트 함량 | wt% | 2~15 |
| `li_content_pct` | 원료 내 리튬 함량 | wt% | 2~6 |
| `mn_content_pct` | 원료 내 망간 함량 | wt% | 5~16 |
| `cu_content_pct` | 원료 내 구리 불순물 함량 | wt% | 0.3~6 |
| `fe_content_pct` | 원료 내 철 불순물 함량 | wt% | 0.2~6 |
| `al_content_pct` | 원료 내 알루미늄 불순물 함량 | wt% | 0.5~7 |
| `feed_amount_kg` | 원료 투입량 | kg | 80~200 |
| `sulfuric_acid_l` | 황산 투입량 | L | 400~1,500 |
| `leaching_temperature_c` | 침출 온도 | °C | 40~95 |
| `leaching_time_hr` | 침출 시간 | 시간 | 1~8 |

**모의 분석**은 원료 성분 각각에 0~100%의 기본 범위를 적용하며, 값의 생략과 `null`을 허용한다. **실제 A 분석**은 원료 성분 7개와 투입량이 모두 필요하며 위 표의 범위를 적용한다. 직접 예측에는 공정 조건 세 값도 필요하다. 빈 입력은 B에서 임의로 채우지 않는다.

### cleaned_data.csv 입력 열 대응

아래는 원본 CSV 열과 B 분석 요청 필드의 대응이다. B는 기본 수치 11개를 전달하고, 실제 A 모델이 벡터 순서와 파생항을 구성한다.

| CSV 열 | B 분석 요청 필드 |
|---|---|
| `Ni_함량_pct` | `material.ni_content_pct` |
| `Co_함량_pct` | `material.co_content_pct` |
| `Li_함량_pct` | `material.li_content_pct` |
| `Mn_함량_pct` | `material.mn_content_pct` |
| `Cu_불순물_pct` | `material.cu_content_pct` |
| `Fe_불순물_pct` | `material.fe_content_pct` |
| `Al_불순물_pct` | `material.al_content_pct` |
| `원료투입량_kg` | `current_process.feed_amount_kg` |
| `황산투입량_L` | `current_process.sulfuric_acid_l` |
| `침출온도_C` | `current_process.leaching_temperature_c` |
| `침출시간_hr` | `current_process.leaching_time_hr` |

현재 A 모델은 이 기본값 11개에 황산량·온도·시간에서 만든 제곱·교차항 6개를 더한다. 원료 이름은 화면 표시용이다. CSV에 기록된 회수율은 예측 대상이며 입력 필드와 구분한다.

### 모의 응답 예시

```json
{
  "schema_version": "draft-1",
  "source": "mock",
  "generated_at": "2026-10-14T21:00:00+09:00",
  "request_id": "example-request-id",
  "material_grade": null,
  "current_prediction": {
    "ni_recovery_pct": 85.65,
    "co_recovery_pct": 78.45
  },
  "recommendation": {
    "process_conditions": {
      "sulfuric_acid_l": 1050.0,
      "leaching_temperature_c": 62.0,
      "leaching_time_hr": 5.5
    },
    "expected_recovery": {
      "ni_recovery_pct": 89.2,
      "co_recovery_pct": 82.1
    }
  }
}
```

`xai`는 MVP 응답에 포함하지 않는다. 형식 합의 후 선택적 필드로 추가한다.

`material_grade`는 A가 Ni/Co 함량 등 합의된 기준으로 판정할 선택 원료 등급이다(DRAFT). 현재 기준·모델이 없어 Mock 응답은 null이며 HMI에서는 등급을 표시하지 않는다. 원료 이름을 등급으로 사용하지 않는다. 이전 클라이언트의 `material.grade` 입력은 호환 목적으로만 유지하고 새 HMI는 보내지 않는다.

### 실제 A 분석 공급자

B는 기존 통합 분석 경로를 유지한다. 공정 조건 3개가 모두 비어 있으면 A의 `/api/v1/recommend`를 호출하고, 모두 있으면 `/api/v1/predict`를 호출한다. 일부만 있는 공정 조건은 필드 오류로 반환한다. 추천의 선택 필드 `options.mode`는 `joint`, `ni`, `co`를 허용하며 생략하면 A의 기본 공동 목표가 적용된다.

실제 A에서는 원료 성분 7개와 투입량이 필수다. 투입량은 80~200 kg, 원료 성분 합계는 최대 100 wt%다. 원료 미입력은 필드별 오류로 알려 주며 B는 값을 대치하지 않는다.

예측 응답의 `recommendation`과 추천 응답의 `current_prediction`은 null이다. `status`, `warnings`, `mode`, `model_version`, `closest_alternative`가 결과를 설명한다. 추천이 비어 있고 `closest_alternative`가 있으면 대시보드는 그 조건과 회수율을 AI 추천칸에 표시한다. API 응답에서는 원래 추천과 대안을 구분한다. 예측값을 사용할 수 없으면 해당 조건을 Unity에 적용할 수 없다.

## `POST /api/v1/factory/apply`

사용자가 선택한 공정 조건을 다음 Unity 명령으로 등록한다.

대시보드에서 추천값 또는 대안을 반영하면 그 조건에 대응하는 예상 회수율과 분석 ID를 함께 사용한다. 조건을 수정하면 다시 예측한 `current_prediction`과 해당 요청 ID를 사용한다. 대시보드는 조건과 결과가 일치할 때 적용을 허용한다. B의 적용 API는 입력의 형식과 범위를 확인한다.

아래는 모의 분석 결과를 담은 적용 예시다. 명령의 원료 필드 허용값은 실제 A 분석 입력 범위와 별개다.

```json
{
  "analysis_request_id": "example-request-id",
  "material": {
    "name": "혼합 원료 A",
    "feed_amount_kg": 1000,
    "ni_content_pct": 12.17,
    "co_content_pct": 2.41,
    "li_content_pct": 0,
    "mn_content_pct": 10.49,
    "cu_content_pct": 1.9,
    "fe_content_pct": null,
    "al_content_pct": 3.43
  },
  "process_conditions": {
    "sulfuric_acid_l": 1050.0,
    "leaching_temperature_c": 62.0,
    "leaching_time_hr": 5.5
  },
  "expected_recovery": {
    "ni_recovery_pct": 89.2,
    "co_recovery_pct": 82.1
  }
}
```

HTTP 202 응답은 명령 ID와 접수 상태를 반환한다. 실제 실행 여부는 이후 상태 보고로 확인한다.

```json
{
  "command_id": "example-command-id",
  "status": "queued",
  "source": "mock"
}
```

## `GET /api/v1/factory/commands/next`

Unity가 처리할 다음 명령을 조회한다. 새 명령이 없으면 HTTP `204 No Content`를 반환한다. 현재 구현은 조회 즉시 큐에서 제거하므로 응답 전달 실패 시 자동 재전송하지 않는다.

```json
{
  "command_id": "example-command-id",
  "command": "apply_and_start",
  "material": {
    "name": "혼합 원료 A",
    "feed_amount_kg": 1000,
    "ni_content_pct": 12.17,
    "co_content_pct": 2.41,
    "li_content_pct": 0,
    "mn_content_pct": 10.49,
    "cu_content_pct": 1.9,
    "fe_content_pct": null,
    "al_content_pct": 3.43
  },
  "process_conditions": {
    "sulfuric_acid_l": 1050.0,
    "leaching_temperature_c": 62.0,
    "leaching_time_hr": 5.5
  },
  "expected_recovery": {
    "ni_recovery_pct": 89.2,
    "co_recovery_pct": 82.1
  }
}
```

## `POST /api/v1/factory/status`

Unity는 알려진 현재 명령에 대해 `running`, `completed`, `error`를 보고한다. 명령이 없는 대기 상태는 B가 `idle`로 표시한다.

```json
{
  "command_id": "example-command-id",
  "state": "running",
  "progress_pct": 35,
  "message": "침출 공정 실행 중"
}
```

## `GET /api/v1/factory/state`

HMI가 표시할 최신 가상 공장 상태를 반환한다. Unity가 연결되지 않았으면 이를 성공 상태처럼 표현하지 않는다.

```json
{
  "source": "mock",
  "state": "running",
  "command_id": "example-command-id",
  "progress_pct": 35,
  "message": "Mock Unity process running",
  "updated_at": "2026-10-14T21:00:01+09:00",
  "connection_status": "connected",
  "last_seen_at": "2026-10-14T21:00:01+09:00"
}
```

상태와 명령은 MVP에서 메모리에만 저장되므로 FastAPI를 재시작하면 초기화된다.

## 오류 응답

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "입력값을 확인해 주세요.",
    "details": [
      { "field": "current_process.leaching_temperature_c", "message": "침출 온도(°C) 값을 확인해 주세요." }
    ]
  },
  "request_id": "example-request-id"
}
```

예상 HTTP 상태 코드는 다음과 같다.

| 상태 | 의미 |
|---|---|
| `400` | 요청 의미 또는 명령 상태 오류 |
| `409` | 대기·실행 중 추가 적용, 과거 명령 보고 또는 상태 역행 |
| `422` | 입력 형식 또는 범위 검증 실패 |
| `502` | A 분석 요청 실패 또는 A 응답 오류 |
| `503` | 실제 A 모델 준비 실패 |
| `504` | 실제 A 분석 요청 시간 초과 |
| `500` | B 내부의 예상하지 못한 오류 |

## Unity 명령과 상태 규칙

- MVP는 한 공정만 처리한다. `queued` 또는 `running` 중 `/apply`는 `409 FACTORY_BUSY`를 반환한다. 완료·오류 후에는 동일 조건도 새 명령으로 적용할 수 있다.
- 현재 명령 이외의 알려진 명령 보고는 `409 STALE_COMMAND`, 미등록 명령은 기존 `400 UNKNOWN_COMMAND`를 반환한다.
- `queued`에서 `running`, `completed`, `error`로, `running`에서 같은 상태·`completed`·`error`로 진행할 수 있다. 진행률 감소와 활성 명령의 `idle` 보고는 `409 INVALID_STATE_TRANSITION`이다. `completed`는 100%여야 한다.
- 완료·오류 후에는 같은 상태와 같은 진행률의 재보고만 허용한다. 종료 명령은 큐에서도 제거해 나중에 실행되지 않게 한다.
- `/state`와 정상 `/status` 응답에 `connection_status` (`connected`/`disconnected`)와 `last_seen_at` (ISO 8601 또는 null)을 추가한다.
- Unity의 `/commands/next` 요청(204 포함)과 유효한 `/status` 보고가 마지막 통신 시각을 갱신한다. HMI의 `/state` 조회는 갱신하지 않는다.
- 마지막 통신 이후 `UNITY_CONNECTION_TIMEOUT_SECONDS`(개발 기본값 10초)가 지나면 연결만 `disconnected`로 표시한다. 마지막 공정 상태와 진행률은 유지한다. 연결 끊김만으로 새 명령을 허용하지 않는다.
- HMI는 첫 화면부터 응답/실패 후 약 1초마다 상태를 다시 조회하며 각 HTTP 요청은 5초 제한을 둔다. 공정 상태와 B 서버 접근 실패를 구분하고 재연결 시 경고를 해제한다.
- 위 상태 전환·폴링·시간 기준은 C와 최종 합의 전의 DRAFT다. 수신 확인·명령 자동 재전송은 이번 변경에 포함하지 않는다.


## Unity 명령 데이터

- 적용 요청과 Unity 명령의 `material`에는 원료 이름, 투입량(kg), Ni·Co·Li·Mn 함량과 Cu·Fe·Al 불순물 함량(%)이 들어간다. 생략하거나 비워 둔 원료 성분은 null, 입력한 0은 0으로 전달한다. 각 성분은 0~100%이며, 투입량은 0 이상의 유한수 또는 null이다. 최종 조건의 예상 회수율도 각각 0~100%이다.
- material과 expected_recovery 객체는 새 적용 요청의 필수 항목이다. 구형 요청은 422로 거부한다. 프런트와 백엔드를 함께 갱신해야 한다. Unity 명령에는 analysis_request_id를 추가하지 않았으며 기존 command_id/command/process_conditions를 유지한다.
- HMI는 마지막 유효 분석 입력 스냅샷에서 원료 이름·투입량·성분과 최종 공정 조건을 읽는다. 추천을 그대로 사용하면 추천 expected_recovery를, 직접 수정·재예측한 조건은 current_prediction을 보낸다. 입력 변경 후 재예측하지 않으면 적용하지 않는다.
- `expected_recovery`는 분석 API가 반환한 예상 회수율이다. 분석 응답의 `source`에서 실제 A와 모의 분석을 구분한다.
- Unity는 null 원료 값을 미입력으로 처리한다. B의 공장 상태·접수 응답에 남아 있는 `source: mock` 값은 통신 여부와 별개다.
