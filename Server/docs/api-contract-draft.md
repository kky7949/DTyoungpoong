# B 파트 API 계약 초안

> **DRAFT:** A/C 담당자와 구현 과정에서 필드, 단위, 허용 범위, 상태 이름 및 갱신 주기를 확정하기 전까지 계약으로 간주하지 않는다.

기본 경로는 `/api/v1`이며 상태 확인만 `/health`를 사용한다. JSON 식별자는 영어로 유지하고 한국어 의미를 함께 기록한다.

현재 문서의 모든 엔드포인트는 B MVP에 구현되어 있다. 다만 A/C 실제 연동 전이므로 공정 필드와 단위는 계속 **DRAFT**이며 응답의 `source: "mock"`은 실제 AI 또는 공정 결과가 아님을 뜻한다.

## 공통 응답 정보

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

B와 A/C 어댑터의 현재 상태 및 지원 기능을 반환한다.

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

## `POST /api/v1/process/analyze`

현재 조건의 회수율 예측과 추천 공정 조건 탐색을 한 번에 요청한다. 비어 있는 측정값은 `null`로 보낼 수 있으며 B는 이를 임의로 대치하지 않는다. A가 수용할 수 있는 최소 필수 필드는 실제 A 연동 전에 확정한다.

### 요청 예시

```json
{
  "material": {
    "grade": "B",
    "ni_content_pct": 12.17,
    "co_content_pct": 6.98
  },
  "current_process": {
    "feed_amount_kg": 159.1,
    "sulfuric_acid_l": 1118.0,
    "leaching_temperature_c": 55.6,
    "leaching_time_hr": 6.32
  }
}
```

### 임시 필드 사전

| 필드 | 한글 이름 | 임시 단위 |
|---|---|---|
| `grade` | 원료 등급 | 없음 |
| `ni_content_pct` | 원료 내 니켈 함량 | % |
| `co_content_pct` | 원료 내 코발트 함량 | % |
| `feed_amount_kg` | 원료 투입량 | kg |
| `sulfuric_acid_l` | 황산 투입량 | L |
| `leaching_temperature_c` | 침출 온도 | °C |
| `leaching_time_hr` | 침출 시간 | 시간 |

### 모의 응답 예시

```json
{
  "schema_version": "draft-1",
  "source": "mock",
  "generated_at": "2026-10-14T21:00:00+09:00",
  "request_id": "example-request-id",
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

## `POST /api/v1/factory/apply`

사용자가 선택한 공정 조건을 다음 Unity 명령으로 등록한다.

```json
{
  "analysis_request_id": "example-request-id",
  "process_conditions": {
    "sulfuric_acid_l": 1050.0,
    "leaching_temperature_c": 62.0,
    "leaching_time_hr": 5.5
  }
}
```

응답은 명령 ID와 접수 상태를 반환한다.

```json
{
  "command_id": "example-command-id",
  "status": "queued",
  "source": "mock"
}
```

## `GET /api/v1/factory/commands/next`

Unity가 처리할 다음 명령을 조회한다. 새 명령이 없으면 HTTP `204 No Content`를 반환한다.

```json
{
  "command_id": "example-command-id",
  "command": "apply_and_start",
  "process_conditions": {
    "sulfuric_acid_l": 1050.0,
    "leaching_temperature_c": 62.0,
    "leaching_time_hr": 5.5
  }
}
```

## `POST /api/v1/factory/status`

Unity가 명령 처리 결과와 공정 상태를 보고한다. 상태 이름은 임시로 `idle`, `running`, `completed`, `error`를 사용하며 C 구현 중 확정한다.

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
  "updated_at": "2026-10-14T21:00:01+09:00"
}
```

상태와 명령은 MVP에서 메모리에만 저장되므로 FastAPI를 재시작하면 초기화된다.

## 오류 응답

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "침출 온도는 숫자로 입력해 주세요.",
    "details": []
  },
  "request_id": "example-request-id"
}
```

예상 HTTP 상태 코드는 다음과 같다.

| 상태 | 의미 |
|---|---|
| `400` | 요청 의미 또는 명령 상태 오류 |
| `422` | 입력 형식 또는 범위 검증 실패 |
| `502` | A 또는 C 외부 연동 응답 오류 |
| `503` | 필요한 외부 연결을 사용할 수 없음 |
| `500` | B 내부의 예상하지 못한 오류 |
